"""
Git entegrasyonu — EXON kod projelerinde git islemlerini yapar.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

git komutlarini subprocess ile guvenli calistirir. TEHLIKELI islemler
(push --force, reset --hard, clean -fd) acikca engellenir/onay ister.
Harici paket gerekmez (sistem git'ini kullanir).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

_NOWIN = 0
try:
    import os as _os
    if _os.name == "nt":
        _NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
except Exception:
    pass

# Onay olmadan ASLA calismayacak tehlikeli kaliplar
_DANGER = ("push --force", "push -f", "reset --hard", "clean -fd",
           "clean -f", "filter-branch", "gc --prune", "reflog expire")


def _run_git(args: list[str], cwd: str) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                           text=True, timeout=60, creationflags=_NOWIN)
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        return r.returncode, out
    except FileNotFoundError:
        return 1, "git bulunamadı. Bilgisayarda Git kurulu olmalı (git-scm.com)."
    except Exception as exc:
        return 1, str(exc)


def _valid_repo(path: str) -> bool:
    code, _ = _run_git(["rev-parse", "--is-inside-work-tree"], path)
    return code == 0


def git_action(action: str = "status", path: str = ".",
               message: str = "", name: str = "") -> str:
    """Git islemi yapar. action: status|log|diff|branch|add|commit|
    create_branch|switch|pull|current."""
    action = (action or "status").lower().strip()
    path = (path or ".").strip().strip('"')
    p = Path(path).expanduser()
    if not p.exists():
        return f"Klasör bulunamadı: {path}"
    path = str(p)

    if not _valid_repo(path):
        return f"Burası bir git deposu değil: {path}"

    if action in ("status", "durum"):
        code, out = _run_git(["status", "-sb"], path)
        return out or "Çalışma alanı temiz."

    if action in ("log", "gecmis", "geçmiş"):
        code, out = _run_git(["log", "--oneline", "-15"], path)
        return "Son commit'ler:\n" + out if out else "Henüz commit yok."

    if action in ("diff", "fark"):
        code, out = _run_git(["diff", "--stat"], path)
        return out or "Değişiklik yok (veya hepsi commit'lenmiş)."

    if action in ("branch", "branches", "dallar"):
        code, out = _run_git(["branch", "-a"], path)
        return "Dallar:\n" + out if out else "Dal bulunamadı."

    if action in ("current", "aktif"):
        code, out = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], path)
        return f"Aktif dal: {out}" if code == 0 else out

    if action == "add":
        code, out = _run_git(["add", "-A"], path)
        return "Tüm değişiklikler sahnelendi (staged)." if code == 0 else out

    if action == "commit":
        if not message.strip():
            return "Commit için bir mesaj gerekli."
        _run_git(["add", "-A"], path)
        code, out = _run_git(["commit", "-m", message.strip()], path)
        return ("Commit oluşturuldu: " + message.strip()) if code == 0 else out

    if action in ("create_branch", "yeni_dal"):
        if not name.strip():
            return "Yeni dal için bir ad gerekli."
        code, out = _run_git(["checkout", "-b", name.strip()], path)
        return f"Yeni dal oluşturuldu ve geçildi: {name}" if code == 0 else out

    if action in ("switch", "gecis", "geçiş", "checkout"):
        if not name.strip():
            return "Geçilecek dal adı gerekli."
        code, out = _run_git(["checkout", name.strip()], path)
        return f"Dal değiştirildi: {name}" if code == 0 else out

    if action == "pull":
        code, out = _run_git(["pull"], path)
        return out or "Pull tamamlandı."

    return (f"Bilinmeyen git işlemi: {action}. "
            "Kullanılabilir: status, log, diff, branch, current, add, commit, "
            "create_branch, switch, pull.")


def suggest_commit_message(path: str = ".") -> str:
    """Sahnelenmis (veya tum) degisikliklere bakip commit mesaji ONERIR."""
    path = str(Path((path or ".").strip().strip('"')).expanduser())
    if not _valid_repo(path):
        return f"Burası bir git deposu değil: {path}"
    code, stat = _run_git(["diff", "--stat", "HEAD"], path)
    if not stat.strip():
        code, stat = _run_git(["diff", "--cached", "--stat"], path)
    if not stat.strip():
        return "Commit'lenecek değişiklik bulamadım."
    # Degisen dosya turlerinden basit bir oneri uret
    code, files = _run_git(["diff", "--name-only", "HEAD"], path)
    flist = [f for f in files.splitlines() if f.strip()]
    summary = stat.strip().splitlines()[-1] if stat.strip() else ""
    hint = ""
    if any(f.endswith((".md", ".txt")) for f in flist):
        hint = "docs: "
    elif any("test" in f.lower() for f in flist):
        hint = "test: "
    elif flist:
        hint = "update: "
    sample = ", ".join(Path(f).name for f in flist[:3])
    return (f"Değişiklik özeti: {summary}\n"
            f"Önerilen commit mesajı: '{hint}{sample} güncellendi'\n"
            f"Onaylarsan git_action(action=commit, message=...) ile uygularım.")
