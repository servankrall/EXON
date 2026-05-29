"""
Görev planlayıcı — "her sabah 8'de hava durumu söyle" gibi zamanlı görevler.
Servan Kanğal tarafından yapılmıştır — EXON Windows Edition

Görevler memory/scheduled_tasks.json içinde saklanır. Arka planda bir thread
her 20 saniyede zamanı kontrol eder; vakti gelen görev için on_fire(task) çağrılır.
"""

from __future__ import annotations

import datetime
import json
import threading
import time
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TASKS_PATH = BASE_DIR / "memory" / "scheduled_tasks.json"

_WEEKDAY_TR = {
    "pazartesi": 0, "salı": 1, "sali": 1, "çarşamba": 2, "carsamba": 2,
    "perşembe": 3, "persembe": 3, "cuma": 4, "cumartesi": 5, "pazar": 6,
}


class TaskScheduler:
    def __init__(self, on_fire):
        """on_fire: vakti gelen görev için çağrılan callback(task_dict)."""
        self.on_fire = on_fire
        self._tasks = self._load()
        self._stop = False
        self._lock = threading.Lock()
        self._thread = None

    def _load(self) -> list:
        try:
            data = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save(self):
        try:
            TASKS_PATH.parent.mkdir(parents=True, exist_ok=True)
            TASKS_PATH.write_text(
                json.dumps(self._tasks, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    @staticmethod
    def _normalize_time(time_str: str) -> str:
        s = (time_str or "").strip().replace(".", ":")
        if ":" not in s:
            s = s + ":00"
        try:
            h, m = s.split(":")[:2]
            return f"{int(h):02d}:{int(m):02d}"
        except Exception:
            return s

    def add_task(self, time_str: str, prompt: str, repeat: str = "daily",
                 days: list | None = None) -> dict:
        task = {
            "id": uuid.uuid4().hex[:8],
            "time": self._normalize_time(time_str),
            "prompt": (prompt or "").strip(),
            "repeat": (repeat or "daily").lower(),
            "days": days or [],
            "last_run": "",
        }
        with self._lock:
            self._tasks.append(task)
            self._save()
        return task

    def list_tasks(self) -> list:
        with self._lock:
            return [dict(t) for t in self._tasks]

    def remove_task(self, identifier: str) -> int:
        ident = (identifier or "").strip().lower()
        with self._lock:
            before = len(self._tasks)
            self._tasks = [
                t for t in self._tasks
                if t.get("id", "").lower() != ident
                and ident not in t.get("prompt", "").lower()
            ]
            removed = before - len(self._tasks)
            self._save()
        return removed

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop = False
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop = True

    def _loop(self):
        while not self._stop:
            now = datetime.datetime.now()
            hm = now.strftime("%H:%M")
            stamp = now.strftime("%Y-%m-%d %H:%M")
            weekday = now.weekday()
            due = []
            with self._lock:
                changed = False
                for t in self._tasks:
                    if t.get("time") != hm:
                        continue
                    if t.get("last_run") == stamp:
                        continue
                    days = t.get("days") or []
                    if days and weekday not in days:
                        continue
                    t["last_run"] = stamp
                    changed = True
                    due.append(dict(t))
                    # Tek seferlik görevi işaretle (sonra temizlenebilir)
                if changed:
                    self._save()
            for t in due:
                try:
                    self.on_fire(t)
                except Exception:
                    pass
                if t.get("repeat") in ("once", "bir kez", "tek"):
                    self.remove_task(t.get("id", ""))
            time.sleep(20)
