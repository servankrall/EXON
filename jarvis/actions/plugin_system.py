"""
Modul/Eklenti sistemi — plugins/ klasorune konan .py dosyalarini dinamik yukler.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Bir eklenti, plugins/ altinda su yapida bir .py dosyasidir:

    NAME = "selam"                  # eklenti adi
    DESCRIPTION = "Selam verir"     # ne yaptigi
    def run(arg: str = "") -> str:  # EXON bunu cagirir
        return "Merhaba " + arg

EXON: 'eklentileri listele', 'X eklentisini calistir', 'eklentileri yeniden yukle'.
Hata izolasyonu: bozuk bir eklenti digerlerini/EXON'u etkilemez.
"""

from __future__ import annotations

import importlib.util
import traceback

from paths import DATA_DIR

_PLUGIN_DIR = DATA_DIR / "plugins"
_LOADED: dict[str, dict] = {}
_DISABLED: set[str] = set()


def _ensure_dir() -> None:
    try:
        _PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        readme = _PLUGIN_DIR / "BENI_OKU.txt"
        if not readme.exists():
            readme.write_text(
                "EXON eklenti klasoru.\n"
                "Buraya .py dosyasi koy. Ornek:\n\n"
                "NAME = 'selam'\n"
                "DESCRIPTION = 'Isim alip selam verir'\n"
                "def run(arg=''):\n"
                "    return 'Merhaba ' + (arg or 'dunya')\n\n"
                "Sonra EXON'a 'eklentileri yeniden yukle' de.\n",
                encoding="utf-8")
    except Exception:
        pass


def load_plugins() -> str:
    """plugins/ icindeki tum .py eklentilerini (yeniden) yukler."""
    _ensure_dir()
    _LOADED.clear()
    errors = []
    for f in sorted(_PLUGIN_DIR.glob("*.py")):
        if f.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"exon_plugin_{f.stem}", f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            name = str(getattr(mod, "NAME", f.stem)).strip().lower()
            run = getattr(mod, "run", None)
            if not callable(run):
                errors.append(f"{f.name}: 'run' fonksiyonu yok")
                continue
            _LOADED[name] = {
                "name": name,
                "desc": str(getattr(mod, "DESCRIPTION", "")),
                "run": run,
                "file": f.name,
            }
        except Exception as exc:
            errors.append(f"{f.name}: {exc}")
    msg = f"{len(_LOADED)} eklenti yüklendi"
    if _LOADED:
        msg += ": " + ", ".join(_LOADED)
    msg += "."
    if errors:
        msg += " Hatalı: " + "; ".join(errors)
    return msg


def list_plugins() -> str:
    if not _LOADED:
        load_plugins()
    if not _LOADED:
        return ("Hiç eklenti yok. plugins/ klasörüne .py dosyası ekleyip "
                "'eklentileri yeniden yükle' de.")
    lines = ["[EKLENTİLER]"]
    for name, info in _LOADED.items():
        state = " (devre dışı)" if name in _DISABLED else ""
        lines.append(f"  • {name}{state}: {info['desc'] or info['file']}")
    return "\n".join(lines)


def run_plugin(name: str, arg: str = "") -> str:
    if not _LOADED:
        load_plugins()
    name = (name or "").strip().lower()
    if name in _DISABLED:
        return f"'{name}' eklentisi devre dışı. Önce etkinleştir."
    info = _LOADED.get(name)
    if not info:
        return f"Eklenti bulunamadı: {name}. 'eklentileri listele' ile bak."
    try:
        result = info["run"](arg)
        return str(result)
    except Exception:
        return f"'{name}' eklentisi hata verdi:\n{traceback.format_exc()[-300:]}"


def toggle_plugin(name: str, enable: bool) -> str:
    name = (name or "").strip().lower()
    if enable:
        _DISABLED.discard(name)
        return f"'{name}' eklentisi etkinleştirildi."
    _DISABLED.add(name)
    return f"'{name}' eklentisi devre dışı bırakıldı."
