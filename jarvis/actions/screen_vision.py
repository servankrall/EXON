"""
Ekran görüntüsü alma ve analiz — Windows uyumlu.
macOS Swift helper yerine PIL.ImageGrab + win32gui kullanılıyor.
Servan Kanğal tarafından yapılmıştır
Windows portu: Swift/osascript → PIL.ImageGrab + win32gui
"""

from __future__ import annotations

import io
import mimetypes
import tempfile
import time
from pathlib import Path

from google import genai
from google.genai import errors, types
from PIL import Image, ImageStat

from app_config import get_app_config_value


BASE_DIR = Path(__file__).resolve().parent.parent

VISION_MODELS = (
    "models/gemini-2.0-flash",
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.5-flash",
)
VISION_MAX_DIMENSION = 1800
VISION_MAX_INLINE_BYTES = 5_500_000


def _capture_active_window() -> tuple[Image.Image | None, str, str]:
    """
    Aktif pencereyi yakalar.
    Döndürür: (PIL Image veya None, sahip_adi, pencere_basligi)
    """
    # win32gui ile aktif pencere tespiti
    try:
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            window_title = win32gui.GetWindowText(hwnd) or ""
            # Pencere sınırlarını al
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            if right > left and bottom > top:
                from PIL import ImageGrab
                img = ImageGrab.grab(bbox=(left, top, right, bottom))
                return img, "", window_title
    except ImportError:
        pass
    except Exception:
        pass

    # pygetwindow fallback
    try:
        import pygetwindow as gw
        win = gw.getActiveWindow()
        if win:
            from PIL import ImageGrab
            bbox = (win.left, win.top, win.right, win.bottom)
            if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
                img = ImageGrab.grab(bbox=bbox)
                return img, "", win.title or ""
    except ImportError:
        pass
    except Exception:
        pass

    # Tam ekran fallback
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        return img, "", "Ekran"
    except Exception as exc:
        return None, "", f"Ekran yakalama hatası: {exc}"


def _screen_permission_message() -> str:
    return (
        "Ekran analizi için ekran yakalama izni gerekiyor. "
        "Windows Gizlilik Ayarları > Ekran yakalama bölümünü kontrol edin. "
        "win32gui için 'pywin32', pygetwindow için 'pygetwindow' paketi gereklidir: "
        "pip install pywin32 pygetwindow"
    )


def _image_looks_blank(img: Image.Image) -> bool:
    try:
        sample = img.convert("RGB")
        stat = ImageStat.Stat(sample)
        means = stat.mean
        extrema = stat.extrema
        max_seen = max(channel[1] for channel in extrema)
        mean_total = sum(means) / max(1, len(means))
        return max_seen <= 8 or mean_total <= 3
    except Exception:
        return False


def _build_image_part(img: Image.Image) -> types.Part:
    try:
        work = img.copy()
        if work.mode not in {"RGB", "L"}:
            work = work.convert("RGB")
        if max(work.size) > VISION_MAX_DIMENSION:
            work.thumbnail((VISION_MAX_DIMENSION, VISION_MAX_DIMENSION), Image.Resampling.LANCZOS)

        png_buffer = io.BytesIO()
        work.save(png_buffer, format="PNG", optimize=True)
        png_bytes = png_buffer.getvalue()
        if len(png_bytes) <= VISION_MAX_INLINE_BYTES:
            return types.Part.from_bytes(data=png_bytes, mime_type="image/png")

        jpg_buffer = io.BytesIO()
        rgb = work.convert("RGB") if work.mode != "RGB" else work
        rgb.save(jpg_buffer, format="JPEG", quality=88, optimize=True)
        return types.Part.from_bytes(data=jpg_buffer.getvalue(), mime_type="image/jpeg")
    except Exception as exc:
        raise RuntimeError(f"Görüntü dönüştürülemedi: {exc}")


def _vision_prompt(query: str, window_title: str) -> str:
    label = window_title or "aktif pencere"
    user_query = (query or "Ekranda ne var?").strip()
    return (
        "Sen Windows üzerinde EXON için ekran analizi yapan bir görüntü yorumlayıcısısın.\n"
        "Aşağıdaki ekran görüntüsü aktif pencereye ait.\n"
        f"Pencere bağlamı: {label}\n\n"
        "Görevlerin:\n"
        "1. Pencerenin genel amacını 1-2 cümlede açıkla.\n"
        "2. Görünen önemli metinleri, hata mesajlarını, butonları, başlıkları ve durum etiketlerini oku.\n"
        "3. Kullanıcı sorusunu bu görüntüye göre doğrudan cevapla.\n"
        "4. Eğer bir hata, uyarı veya dikkat edilmesi gereken bir şey varsa bunu ayrı ve net belirt.\n"
        "5. Uydurma yapma. Emin olmadığın kısımlarda bunu söyle.\n\n"
        f"Kullanıcı sorusu: {user_query}\n\n"
        "Yanıtı Türkçe ver. Gereksiz uzun olma, ama okunabilir detay ver."
    )


def _extract_response_text(response) -> str:
    text = str(getattr(response, "text", "") or "").strip()
    if text:
        return text
    candidates = getattr(response, "candidates", None) or []
    chunks: list[str] = []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            part_text = str(getattr(part, "text", "") or "").strip()
            if part_text:
                chunks.append(part_text)
    return "\n".join(chunk for chunk in chunks if chunk).strip()


def _is_transient_vision_error(exc: Exception) -> bool:
    if isinstance(exc, (errors.ServerError, TimeoutError)):
        return True
    message = str(exc or "").lower()
    transient_markers = ("503", "429", "deadline", "timed out", "timeout",
                         "unavailable", "service unavailable", "internal error",
                         "busy", "overloaded", "resource exhausted")
    return any(marker in message for marker in transient_markers)


def _friendly_vision_error(exc: Exception) -> str:
    message = str(exc or "").lower()
    if any(k in message for k in ("quota", "rate limit", "billing")):
        return "Gemini vision isteği kota limitine takıldı. Biraz bekleyip tekrar dene."
    if _is_transient_vision_error(exc):
        return "Gemini vision servisi şu anda yoğun. Biraz sonra tekrar dene."
    return f"Gemini vision isteği başarısız oldu: {exc}"


def _uploaded_image_prompt(query: str) -> str:
    user_query = (query or "Bu görselde ne var?").strip()
    return (
        "Sen EXON için görsel analiz eden bir görüntü yorumlayıcısısın.\n"
        "Aşağıdaki görsel kullanıcı tarafından yüklendi.\n\n"
        "Görevlerin:\n"
        "1. Görselin genel içeriğini 1-2 cümlede açıkla.\n"
        "2. Görseldeki önemli nesneleri, kişileri, metinleri ve detayları oku.\n"
        "3. Kullanıcı sorusunu bu görsele göre doğrudan cevapla.\n"
        "4. Uydurma yapma; emin olmadığın kısımları belirt.\n\n"
        f"Kullanıcı sorusu: {user_query}\n\n"
        "Yanıtı Türkçe ver. Okunabilir ama gereksiz uzun olmayan detay ver."
    )


def _analyze_with_gemini(query: str, img: Image.Image, window_title: str,
                         prompt_override: str | None = None) -> str:
    api_key = str(get_app_config_value("gemini_api_key", "") or "").strip()
    if not api_key:
        return "Gemini API anahtarı eksik olduğu için görsel analizi yapılamadı."

    prompt = prompt_override or _vision_prompt(query, window_title)
    client = genai.Client(api_key=api_key)
    image_part = _build_image_part(img)
    retry_delays = (0.9, 1.8, 3.0)
    last_error: Exception | None = None

    for model_name in VISION_MODELS:
        for attempt, delay in enumerate(retry_delays, start=1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_text(text=prompt),
                        image_part,
                    ],
                    config=types.GenerateContentConfig(temperature=0.2),
                )
                merged = _extract_response_text(response)
                if merged:
                    return merged
                raise RuntimeError("Gemini geçerli bir ekran analizi metni döndürmedi.")
            except Exception as exc:
                last_error = exc
                if attempt < len(retry_delays) and _is_transient_vision_error(exc):
                    time.sleep(delay)
                    continue
                if _is_transient_vision_error(exc):
                    break
                raise RuntimeError(_friendly_vision_error(exc)) from exc

    assert last_error is not None
    raise RuntimeError(_friendly_vision_error(last_error))


def analyze_screen(query: str, target: str = "active_window") -> str:
    target = (target or "active_window").strip().lower()
    if target != "active_window":
        return "Screen Vision v1 yalnızca aktif pencere analizini destekliyor."

    img, owner_name, window_title = _capture_active_window()

    if img is None:
        return _screen_permission_message()

    if img.size[0] <= 0 or img.size[1] <= 0:
        return "Ekran görüntüsü boş geldi. " + _screen_permission_message()

    if _image_looks_blank(img):
        return (
            "Ekran görüntüsü siyah veya boş görünüyor. "
            "Bu, izin eksikliğinden veya korumalı bir uygulama açıkken olabilir. "
            + _screen_permission_message()
        )

    try:
        analysis = _analyze_with_gemini(query, img, window_title)
    except Exception as exc:
        prefix = window_title.strip()
        if prefix:
            return f"Ekran görüntüsü alındı ({prefix}) ama analiz tamamlanamadı: {exc}"
        return f"Ekran görüntüsü alındı ama analiz tamamlanamadı: {exc}"

    if window_title:
        return f"[Aktif pencere: {window_title}]\n{analysis}"
    return analysis


def analyze_image_file(image_path: str, query: str = "Bu görselde ne var?") -> str:
    """Kullanıcının yüklediği bir görsel dosyasını Gemini vision ile analiz eder."""
    path = Path(image_path)
    if not path.exists():
        return f"Görsel bulunamadı: {image_path}"

    try:
        img = Image.open(path)
        img.load()
    except Exception as exc:
        return f"Görsel açılamadı: {exc}"

    try:
        return _analyze_with_gemini(
            query, img, "",
            prompt_override=_uploaded_image_prompt(query),
        )
    except Exception as exc:
        return f"Görsel alındı ama analiz tamamlanamadı: {exc}"
