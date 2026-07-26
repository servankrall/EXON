"""
Vektor deposu — saf Python, SIFIR ek paket (chromadb/faiss gerekmez).
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Embedding'leri Gemini'nin ucretsiz embedding modeliyle uretir (anahtarin zaten var),
yerel JSON'da saklar, kosinus benzerligiyle semantik arama yapar. Kucuk-orta
veri (binlerce parca) icin yeterince hizli ve kurulum DERDI YOK.

Kullanim: RAG (belge sorgulama), proje bazli hafiza, kisisel bilgi grafigi bunu kullanir.
"""

from __future__ import annotations

import json
import math
import time

from paths import DATA_DIR
from app_config import get_app_config_value

_VEC_DIR = DATA_DIR / "vectors"
_EMBED_MODEL = "models/text-embedding-004"
_EMBED_CACHE: dict[str, list[float]] = {}


def _embed(text: str) -> list[float] | None:
    """Metni vektore cevirir (Gemini embedding). Basarisizsa None."""
    text = (text or "").strip()
    if not text:
        return None
    if text in _EMBED_CACHE:
        return _EMBED_CACHE[text]
    api_key = str(get_app_config_value("gemini_api_key", "") or "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        resp = client.models.embed_content(model=_EMBED_MODEL, contents=text[:8000])
        vec = None
        embs = getattr(resp, "embeddings", None)
        if embs:
            vec = list(getattr(embs[0], "values", None) or embs[0])
        elif getattr(resp, "embedding", None) is not None:
            vec = list(getattr(resp.embedding, "values", None) or resp.embedding)
        if vec:
            if len(_EMBED_CACHE) < 2000:
                _EMBED_CACHE[text] = vec
            return vec
    except Exception:
        return None
    return None


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class VectorStore:
    """Adlandirilmis bir koleksiyon (orn. 'docs', 'project_X')."""

    def __init__(self, name: str = "default"):
        self.name = "".join(c for c in name if c.isalnum() or c in "_-") or "default"
        self.path = _VEC_DIR / f"{self.name}.json"
        self._items: list[dict] = []
        self._load()

    def _load(self):
        try:
            if self.path.exists():
                self._items = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            self._items = []

    def _save(self):
        try:
            _VEC_DIR.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self._items, ensure_ascii=False),
                                 encoding="utf-8")
        except Exception:
            pass

    def add(self, text: str, meta: dict | None = None) -> bool:
        vec = _embed(text)
        if not vec:
            return False
        self._items.append({"text": text, "vec": vec,
                            "meta": meta or {}, "ts": time.time()})
        self._save()
        return True

    def add_many(self, chunks: list[str], meta: dict | None = None) -> int:
        added = 0
        for ch in chunks:
            if ch.strip() and self.add(ch, meta):
                added += 1
        return added

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        qv = _embed(query)
        if not qv or not self._items:
            return []
        scored = []
        for it in self._items:
            scored.append((_cosine(qv, it["vec"]), it))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, it in scored[:top_k]:
            out.append({"text": it["text"], "score": round(score, 3),
                        "meta": it.get("meta", {})})
        return out

    def count(self) -> int:
        return len(self._items)

    def clear(self):
        self._items = []
        self._save()


def chunk_text(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    """Uzun metni, ustuste binen parcalara boler (RAG icin)."""
    text = " ".join((text or "").split())
    if not text:
        return []
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i + size])
        i += size - overlap
    return chunks


def embeddings_available() -> bool:
    """Embedding API calisiyor mu (kucuk bir test)."""
    return _embed("test") is not None
