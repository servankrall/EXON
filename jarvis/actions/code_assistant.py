"""
Kod asistani — kullanicinin kodlarina erisir, okur, arar ve (onayla) yazar.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

EXON kod yazarken yardim edebilsin diye: dosya okuma, klasor listeleme,
icerik arama ve dosya yazma. Tum islemler kullanicinin kendi makinesinde.
"""

from __future__ import annotations

import os
from pathlib import Path


_MAX_READ = 20000   # tek seferde okunacak en fazla karakter
_CODE_EXTS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".m", ".mm",
    ".html", ".css", ".scss", ".json", ".yaml", ".yml", ".toml", ".xml",
    ".sql", ".sh", ".bat", ".ps1", ".md", ".txt", ".ino", ".lua", ".dart",
}
_SKIP_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv",
              "dist", "build", ".idea", ".vscode", "target"}


def read_code_file(path: str, max_chars: int = _MAX_READ) -> str:
    """Bir kod/metin dosyasini satir numaralariyla okur."""
    path = (path or "").strip().strip('"')
    if not path:
        return "Okunacak dosya yolunu ver."
    p = Path(path).expanduser()
    if not p.exists() or not p.is_file():
        return f"Dosya bulunamadi: {path}"
    try:
        max_chars = max(500, min(int(max_chars or _MAX_READ), 60000))
    except (TypeError, ValueError):
        max_chars = _MAX_READ
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"Dosya okunamadi: {exc}"
    truncated = len(text) > max_chars
    text = text[:max_chars]
    lines = text.splitlines()
    numbered = "\n".join(f"{i:>4} | {ln}" for i, ln in enumerate(lines, 1))
    note = "\n... (dosya kisaltildi)" if truncated else ""
    return f"[{p}] ({len(lines)} satir gosteriliyor)\n{numbered}{note}"


def list_code_files(directory: str = ".", pattern: str = "") -> str:
    """Bir klasordeki kod dosyalarini listeler (alt klasorler dahil)."""
    directory = (directory or ".").strip().strip('"')
    base = Path(directory).expanduser()
    if not base.exists() or not base.is_dir():
        return f"Klasor bulunamadi: {directory}"
    pat = (pattern or "").lower().strip()
    found: list[str] = []
    try:
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS
                           and not d.startswith(".")]
            for fn in filenames:
                if Path(fn).suffix.lower() in _CODE_EXTS:
                    if pat and pat not in fn.lower():
                        continue
                    found.append(str(Path(dirpath) / fn))
                    if len(found) >= 80:
                        break
            if len(found) >= 80:
                break
    except Exception as exc:
        return f"Listeleme hatasi: {exc}"
    if not found:
        return f"'{directory}' altinda kod dosyasi bulunamadi."
    return f"{len(found)} kod dosyasi:\n" + "\n".join(f"- {f}" for f in found)


def search_in_code(directory: str, query: str, max_results: int = 25) -> str:
    """Klasordeki kod dosyalarinda metin/desen arar (dosya:satir gosterir)."""
    query = (query or "").strip()
    if not query:
        return "Aranacak metni ver."
    base = Path((directory or ".").strip().strip('"')).expanduser()
    if not base.exists() or not base.is_dir():
        return f"Klasor bulunamadi: {directory}"
    try:
        max_results = max(1, min(int(max_results or 25), 100))
    except (TypeError, ValueError):
        max_results = 25
    q = query.lower()
    hits: list[str] = []
    try:
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS
                           and not d.startswith(".")]
            for fn in filenames:
                if Path(fn).suffix.lower() not in _CODE_EXTS:
                    continue
                fp = Path(dirpath) / fn
                try:
                    with open(fp, encoding="utf-8", errors="replace") as f:
                        for ln_no, line in enumerate(f, 1):
                            if q in line.lower():
                                hits.append(f"{fp}:{ln_no}: {line.strip()[:120]}")
                                if len(hits) >= max_results:
                                    break
                except Exception:
                    continue
                if len(hits) >= max_results:
                    break
            if len(hits) >= max_results:
                break
    except Exception as exc:
        return f"Arama hatasi: {exc}"
    if not hits:
        return f"'{query}' kod icinde bulunamadi."
    return f"'{query}' icin {len(hits)} eslesme:\n" + "\n".join(hits)


def write_code_file(path: str, content: str) -> str:
    """Bir dosyaya icerik yazar/olusturur. Var olan dosyanin ustune yazabilir."""
    path = (path or "").strip().strip('"')
    if not path:
        return "Yazilacak dosya yolunu ver."
    p = Path(path).expanduser()
    existed = p.exists()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content or "", encoding="utf-8")
    except Exception as exc:
        return f"Dosya yazilamadi: {exc}"
    action = "guncellendi" if existed else "olusturuldu"
    return f"Dosya {action}: {p} ({len(content or '')} karakter)."
