"""
Gorev motoru — uzun/cok adimli gorevleri yonetir.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

- Gorev olustur, alt gorevlere bol, ilerleme takip et, oncelik ver.
- Bagimlilik (bir alt gorev digerine bagli), gecmis, durum (bekliyor/calisiyor/bitti).
- Veriler memory/tasks.json'da kalici. JSON tabanli, harici paket gerekmez.
"""

from __future__ import annotations

import json
import time
import uuid

from paths import DATA_DIR

_TASKS_FILE = DATA_DIR / "memory" / "tasks.json"
_PRIORITY = {"low": 1, "normal": 2, "high": 3, "urgent": 4,
             "dusuk": 1, "orta": 2, "yuksek": 3, "acil": 4}


def _load() -> dict:
    try:
        if _TASKS_FILE.exists():
            return json.loads(_TASKS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"tasks": {}, "history": []}


def _save(data: dict) -> None:
    _TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _TASKS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                           encoding="utf-8")


def _short_id() -> str:
    return uuid.uuid4().hex[:6]


def create_task(title: str, steps: str = "", priority: str = "normal") -> str:
    """Yeni gorev olusturur. steps: virgul/yeni-satir ile ayrilmis alt adimlar."""
    title = (title or "").strip()
    if not title:
        return "Görev başlığı gerekli."
    data = _load()
    tid = _short_id()
    sub = []
    raw = [s.strip() for s in (steps or "").replace("\n", ",").split(",") if s.strip()]
    for i, s in enumerate(raw):
        sub.append({"id": f"{tid}.{i+1}", "text": s, "done": False})
    prio = _PRIORITY.get((priority or "normal").lower(), 2)
    data["tasks"][tid] = {
        "id": tid, "title": title, "priority": prio,
        "status": "pending", "created": time.time(),
        "subtasks": sub, "progress": 0,
    }
    _save(data)
    extra = f" ({len(sub)} alt adım)" if sub else ""
    return f"Görev oluşturuldu [{tid}]: {title}{extra}. Öncelik: {priority}."


def add_subtask(task_id: str, text: str) -> str:
    data = _load()
    t = data["tasks"].get(task_id)
    if not t:
        return f"Görev bulunamadı: {task_id}"
    n = len(t["subtasks"]) + 1
    t["subtasks"].append({"id": f"{task_id}.{n}", "text": text.strip(), "done": False})
    _save(data)
    return f"Alt adım eklendi [{task_id}.{n}]: {text}"


def complete_subtask(subtask_id: str) -> str:
    """Bir alt adimi tamamlandi isaretler ve ilerlemeyi gunceller."""
    data = _load()
    tid = subtask_id.split(".")[0]
    t = data["tasks"].get(tid)
    if not t:
        return f"Görev bulunamadı: {tid}"
    found = False
    for s in t["subtasks"]:
        if s["id"] == subtask_id:
            s["done"] = True
            found = True
    if not found:
        return f"Alt adım bulunamadı: {subtask_id}"
    done = sum(1 for s in t["subtasks"] if s["done"])
    total = len(t["subtasks"]) or 1
    t["progress"] = int(done / total * 100)
    if done == total:
        t["status"] = "done"
        data["history"].append({"id": tid, "title": t["title"],
                                "finished": time.time()})
    else:
        t["status"] = "running"
    _save(data)
    return f"[{subtask_id}] tamamlandı. İlerleme: %{t['progress']} ({done}/{total})."


def list_tasks(only_open: bool = True) -> str:
    """Acik (veya tum) gorevleri oncelik sirasiyla listeler."""
    data = _load()
    tasks = list(data["tasks"].values())
    if only_open:
        tasks = [t for t in tasks if t["status"] != "done"]
    if not tasks:
        return "Açık görev yok." if only_open else "Hiç görev yok."
    tasks.sort(key=lambda t: (-t["priority"], t["created"]))
    pr_name = {1: "düşük", 2: "orta", 3: "yüksek", 4: "ACİL"}
    lines = ["[GÖREVLER]"]
    for t in tasks:
        bar = f"%{t['progress']}"
        lines.append(f"[{t['id']}] {t['title']} — {pr_name.get(t['priority'],'orta')}, "
                     f"{t['status']}, {bar}")
        for s in t["subtasks"]:
            mark = "✓" if s["done"] else "○"
            lines.append(f"     {mark} {s['text']}")
    return "\n".join(lines)


def task_status(task_id: str) -> str:
    data = _load()
    t = data["tasks"].get(task_id)
    if not t:
        return f"Görev bulunamadı: {task_id}"
    done = sum(1 for s in t["subtasks"] if s["done"])
    total = len(t["subtasks"])
    lines = [f"[{t['id']}] {t['title']}",
             f"Durum: {t['status']} · İlerleme: %{t['progress']} ({done}/{total})"]
    for s in t["subtasks"]:
        lines.append(f"  {'✓' if s['done'] else '○'} {s['text']}")
    return "\n".join(lines)


def remove_task(task_id: str) -> str:
    data = _load()
    if task_id in data["tasks"]:
        title = data["tasks"].pop(task_id)["title"]
        _save(data)
        return f"Görev silindi [{task_id}]: {title}"
    return f"Görev bulunamadı: {task_id}"


def task_history(limit: int = 10) -> str:
    data = _load()
    hist = data.get("history", [])[-limit:][::-1]
    if not hist:
        return "Tamamlanmış görev geçmişi boş."
    lines = ["[GÖREV GEÇMİŞİ]"]
    for h in hist:
        when = time.strftime("%d.%m %H:%M", time.localtime(h.get("finished", 0)))
        lines.append(f"  ✓ {h['title']} ({when})")
    return "\n".join(lines)
