"""
'EXON'u Gelistir' denetim modu — EXON kendi sistemini analiz edip
gelistirme onerileri uretir.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Listedeki 'kendini puanlama / darbogaz / gereksiz modul / denetim merkezi'
maddelerini karsilar. Tamamen yerel ve okuma-amacli (hicbir sey bozmaz).
"""

from __future__ import annotations

import os
from pathlib import Path

_JARVIS = Path(__file__).resolve().parent.parent


def _py_files() -> list[Path]:
    out = []
    for base in (_JARVIS, _JARVIS / "actions", _JARVIS / "memory"):
        if base.is_dir():
            out.extend(base.glob("*.py"))
    return out


def self_audit() -> str:
    """EXON'un kendi kodunu/durumunu analiz edip gelistirme onerileri uretir."""
    lines = ["[EXON KENDİNİ DENETLEME RAPORU]", ""]

    # 1) Kod boyutu / modul sayisi
    files = _py_files()
    total_lines = 0
    big_files = []
    for f in files:
        try:
            n = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            total_lines += n
            if n > 800:
                big_files.append((f.name, n))
        except Exception:
            pass
    lines.append(f"• Modül sayısı: {len(files)}, toplam ~{total_lines} satır kod.")
    if big_files:
        big_files.sort(key=lambda x: -x[1])
        lines.append("• Büyük dosyalar (bölünebilir): "
                     + ", ".join(f"{n} ({c} satır)" for n, c in big_files[:3]))

    # 2) Arac sayisi + tutarlilik
    try:
        import re
        src = (_JARVIS / "main.py").read_text(encoding="utf-8")
        decl = set(re.findall(r'"name":\s*"([a-z_]+)"', src))
        hand = set(re.findall(r'name == "([a-z_]+)"', src))
        hand.discard("nt")
        lines.append(f"• Araç sayısı: {len(decl)}. Tanım/işleyici tutarlılığı: "
                     + ("TAM ✓" if decl == hand else f"UYUMSUZ ✗ {decl ^ hand}"))
    except Exception:
        pass

    # 3) Calisma zamani durumu (varsa)
    try:
        from actions.dev_mode import snapshot
        snap = snapshot()
        lines.append(f"• Bu oturum: {snap['tool_calls']} araç çağrısı, "
                     f"{snap['errors']} hata, süre {snap['uptime']}.")
        if snap["errors"] > 0 and snap["tool_calls"]:
            rate = snap["errors"] / snap["tool_calls"] * 100
            if rate > 15:
                lines.append(f"  ⚠ Hata oranı yüksek (%{rate:.0f}) — araçları gözden geçir.")
    except Exception:
        pass

    # 4) Hafiza durumu
    try:
        from memory.smart_memory import memory_stats
        ms = memory_stats()
        lines.append(f"• Hafıza: {ms['total']} kayıt, {len(ms['categories'])} kategori.")
        if ms["total"] > 200:
            lines.append("  ⚠ Hafıza büyük — 'cleanup_memory' önerilir.")
    except Exception:
        pass

    # 5) Bilgi tabani
    try:
        from actions.vector_store import _VEC_DIR, VectorStore
        if _VEC_DIR.exists():
            cols = list(_VEC_DIR.glob("*.json"))
            tot = sum(VectorStore(c.stem).count() for c in cols)
            lines.append(f"• Bilgi tabanı (RAG): {len(cols)} koleksiyon, {tot} parça.")
    except Exception:
        pass

    # 6) Guvenlik
    try:
        from actions.security import verify_integrity
        integ = verify_integrity().split("\n")[0]
        lines.append(f"• Güvenlik bütünlüğü: {integ}")
    except Exception:
        pass

    # 7) Gelistirme onerileri (sezgisel)
    lines.append("")
    lines.append("GELİŞTİRME ÖNERİLERİ:")
    suggestions = []
    if big_files:
        suggestions.append("En büyük dosyaları daha küçük modüllere böl (bakımı kolaylaşır).")
    # Opsiyonel paket kontrolu
    optional = {"pyaudio": "sesli giriş", "pygame": "ses efektleri",
                "cv2": "yüz tanıma", "pypdf": "PDF okuma"}
    missing = []
    for mod, what in optional.items():
        try:
            __import__(mod)
        except Exception:
            missing.append(f"{mod} ({what})")
    if missing:
        suggestions.append("Eksik opsiyonel paketler: " + ", ".join(missing)
                           + " — kurulursa o özellikler açılır.")
    suggestions.append("Sık kullanılan araçları 'usage_analytics' ile takip et, "
                       "az kullanılanları sadeleştir.")
    suggestions.append("Düzenli 'security_action snapshot' ile bütünlük referansını güncel tut.")
    for i, s in enumerate(suggestions, 1):
        lines.append(f"  {i}. {s}")

    return "\n".join(lines)


def optimize_self() -> str:
    """Kendini optimize eden cekirdek: kullanim verisine bakip somut, onceliklendirilmis
    iyilestirme/optimizasyon onerileri uretir ('bir sonraki gelistirme ne olmali')."""
    lines = ["[EXON KENDİNİ OPTİMİZE ETME RAPORU]", ""]
    recs = []

    # 1) Kullanim analitigi: az/cok kullanilan araclar
    try:
        from actions.analytics import _load as _aload
        data = _aload()
        feats = data.get("features", {})
        if feats:
            ranked = sorted(feats.items(), key=lambda kv: -kv[1])
            top = ", ".join(f"{n}({c})" for n, c in ranked[:5])
            lines.append(f"• En çok kullanılan: {top}")
            rare = [n for n, c in ranked if c <= 1]
            if len(rare) > 8:
                recs.append(f"{len(rare)} araç neredeyse hiç kullanılmıyor — "
                            "menü/öneri sadeleştirilebilir.")
            lines.append(f"• Toplam {len(feats)} farklı araç kullanılmış.")
        else:
            lines.append("• Henüz kullanım verisi yok (daha çok kullanınca öneriler keskinleşir).")
    except Exception:
        pass

    # 2) Hata orani
    try:
        from actions.dev_mode import snapshot
        snap = snapshot()
        if snap["tool_calls"]:
            rate = snap["errors"] / snap["tool_calls"] * 100
            lines.append(f"• Bu oturum hata oranı: %{rate:.0f}")
            if rate > 10:
                recs.append("Hata oranı yüksek — en çok hata veren aracı gözden geçir.")
    except Exception:
        pass

    # 3) Hafiza/bilgi tabani buyumesi
    try:
        from memory.smart_memory import memory_stats
        ms = memory_stats()
        if ms["total"] > 150:
            recs.append("Hafıza büyük — 'cleanup_memory' ile düşük önemli kayıtları buda.")
    except Exception:
        pass

    # 4) Eksik opsiyonel yetenekler
    optional = {"cv2": "yüz tanıma + video analizi", "pypdf": "PDF okuma/RAG",
                "pyaudio": "sesli giriş"}
    missing = [f"{m} ({w})" for m, w in optional.items()
               if not _safe_import(m)]
    if missing:
        recs.append("Şu paketler kurulursa yeni yetenekler açılır: " + ", ".join(missing))

    # 5) Bir sonraki gelistirme onerisi (sezgisel oncelik)
    lines.append("")
    lines.append("BİR SONRAKİ GELİŞTİRME ÖNERİLERİ (öncelik sırası):")
    if not recs:
        recs.append("Sistem dengeli görünüyor. Düzenli 'backup_data cloud' ile yedek al.")
    recs.append("Sık kullandığın işler için 'plugins/' altında kendi eklentini yaz.")
    recs.append("Önemli belgeleri 'learn_file' ile bilgi tabanına ekle (RAG gücü artar).")
    for i, r in enumerate(recs, 1):
        lines.append(f"  {i}. {r}")
    return "\n".join(lines)


def _safe_import(mod: str) -> bool:
    try:
        __import__(mod)
        return True
    except Exception:
        return False
