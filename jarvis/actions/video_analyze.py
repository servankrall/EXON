"""
Video analizi (hafif) — videodan kareler alip ozetler.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Tam video isleme COK agirdir (saniyede 30 kare = 30 gorsel analizi). Bunun
yerine HAFIF yaklasim: videodan esit araliklarla birkac KARE alir, her birini
Gemini vision ile analiz eder, sonra bir ozet sentezler.

Kare cikarma icin OpenCV (cv2) gerekir; yoksa kullaniciyi yonlendirir.
OpenCV zaten yuz tanima icin opsiyonel olarak listede.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app_config import get_app_config_value

_VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".wmv", ".flv", ".m4v"}


def _extract_frames(video_path: str, n_frames: int = 6) -> list[str]:
    """Videodan esit araliklarla n_frames kare cikarir, gecici PNG yollarini dondurur."""
    import cv2  # lazy: yoksa ImportError -> ust katman yakalar
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    if total <= 0:
        # bazi formatlarda kare sayisi okunamaz; suure gore tahmin
        total = 300
    step = max(1, total // (n_frames + 1))
    out = []
    tmp = Path(tempfile.gettempdir())
    idx = 0
    grabbed = 0
    while grabbed < n_frames:
        frame_no = step * (grabbed + 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ok, frame = cap.read()
        if not ok:
            break
        p = tmp / f"exon_frame_{frame_no}.png"
        try:
            cv2.imwrite(str(p), frame)
            out.append(str(p))
        except Exception:
            pass
        grabbed += 1
        idx += 1
        if idx > n_frames * 3:
            break
    cap.release()
    return out


def analyze_video(video_path: str, query: str = "", n_frames: int = 6) -> str:
    """Videoyu kare-kare analiz edip ozetler. query: ozel soru (opsiyonel)."""
    video_path = (video_path or "").strip().strip('"')
    p = Path(video_path).expanduser()
    if not p.exists() or not p.is_file():
        return f"Video bulunamadı: {video_path}"
    if p.suffix.lower() not in _VIDEO_EXT:
        return f"Desteklenmeyen video formatı: {p.suffix}"

    try:
        n_frames = max(3, min(int(n_frames or 6), 12))
    except (TypeError, ValueError):
        n_frames = 6

    # OpenCV var mi?
    try:
        import cv2  # noqa: F401
    except Exception:
        return ("Video analizi için OpenCV gerekli. CMD'de: "
                "pip install opencv-contrib-python  (sonra tekrar dene).")

    if not str(get_app_config_value("gemini_api_key", "") or "").strip():
        return "Video analizi için Gemini API anahtarı gerekli."

    frames = _extract_frames(str(p), n_frames)
    if not frames:
        return "Videodan kare çıkarılamadı (dosya bozuk veya codec eksik olabilir)."

    # Her kareyi analiz et
    from actions.screen_vision import analyze_image_file
    q = query.strip() or "Bu karede ne görünüyor? Kısa açıkla."
    observations = []
    for i, fpath in enumerate(frames, 1):
        try:
            desc = analyze_image_file(fpath, q)
            observations.append(f"[Kare {i}] {desc}")
        except Exception as exc:
            observations.append(f"[Kare {i}] analiz edilemedi: {exc}")
        finally:
            try:
                Path(fpath).unlink()
            except Exception:
                pass

    joined = "\n".join(observations)

    # Sentez: kareleri tek bir ozete birlestir
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=str(get_app_config_value("gemini_api_key", "")))
        sys_p = ("Sana bir videodan alinan ardisik karelerin aciklamalari verildi. "
                 "Bunlari birlestirerek videonun NE HAKKINDA oldugunu, ne olup bittigini "
                 "akici bir paragrafla Turkce ozetle.")
        prompt = f"Kare açıklamaları:\n{joined}"
        if query.strip():
            prompt += f"\n\nKullanıcının özel sorusu: {query}"
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=sys_p, temperature=0.4),
        )
        summary = (getattr(resp, "text", "") or "").strip()
    except Exception as exc:
        summary = f"(Özet üretilemedi: {exc})"

    return (f"[VİDEO ANALİZİ — {p.name}, {len(frames)} kare]\n\n"
            f"ÖZET:\n{summary}\n\n"
            f"Kare detayları:\n{joined[:1200]}")
