"""
RAG / Bilgi tabani — belge/metin ekle, semantik ara, sorgula.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Vektor deposunu (vector_store) kullanir. Koleksiyon adi = proje/baglam adi,
boylece PROJE BAZLI HAFIZA ve GOREV BAZLI BAGLAM da bununla saglanir.

- learn_text / learn_file: bilgiyi parcalara bolup vektor deposuna ekler.
- knowledge_search: semantik arama (anlamca en yakin parcalar).
- knowledge_query: aramayi yapip Gemini ile KAYNAKLI yanit uretir (RAG).
"""

from __future__ import annotations

from pathlib import Path

from app_config import get_app_config_value
from actions.vector_store import VectorStore, chunk_text, embeddings_available


def _read_file_text(path: str) -> str | None:
    p = Path((path or "").strip().strip('"')).expanduser()
    if not p.exists() or not p.is_file():
        return None
    if p.suffix.lower() == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(p))
            return " ".join((pg.extract_text() or "") for pg in reader.pages)
        except Exception:
            return None
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def learn_text(text: str, collection: str = "default",
               source: str = "manuel") -> str:
    """Bir metni bilgi tabanina ekler (semantik aramaya hazir hale getirir)."""
    text = (text or "").strip()
    if not text:
        return "Öğrenilecek metin boş."
    if not embeddings_available():
        return ("Bilgi tabanı için embedding gerekiyor ama erişilemedi. "
                "Gemini API anahtarının geçerli olduğundan emin ol.")
    store = VectorStore(collection)
    chunks = chunk_text(text)
    added = store.add_many(chunks, meta={"source": source})
    return (f"'{collection}' bilgi tabanına {added} parça eklendi "
            f"(kaynak: {source}). Toplam: {store.count()} parça.")


def learn_file(path: str, collection: str = "default") -> str:
    """Bir dosyayi (txt/md/kod/pdf) okuyup bilgi tabanina ekler."""
    text = _read_file_text(path)
    if text is None:
        return f"Dosya okunamadı: {path}"
    name = Path(path).name
    return learn_text(text, collection, source=name)


def knowledge_search(query: str, collection: str = "default",
                     top_k: int = 4) -> str:
    """Bilgi tabaninda semantik arama (en yakin parcalari dondurur)."""
    store = VectorStore(collection)
    if store.count() == 0:
        return f"'{collection}' bilgi tabanı boş. Önce learn_file/learn_text ile bilgi ekle."
    hits = store.search(query, top_k=top_k)
    if not hits:
        return "Eşleşen bilgi bulunamadı (veya embedding erişilemedi)."
    lines = [f"'{query}' için en alakalı {len(hits)} parça:"]
    for i, h in enumerate(hits, 1):
        src = h["meta"].get("source", "?")
        lines.append(f"{i}. (benzerlik {h['score']}, kaynak {src})\n   {h['text'][:300]}")
    return "\n".join(lines)


def knowledge_query(question: str, collection: str = "default") -> str:
    """RAG: bilgi tabanindan ilgili parcalari bulup Gemini ile KAYNAKLI yanit verir."""
    store = VectorStore(collection)
    if store.count() == 0:
        return f"'{collection}' bilgi tabanı boş. Önce bilgi ekle."
    hits = store.search(question, top_k=5)
    if not hits:
        return "İlgili bilgi bulunamadı."
    context = "\n\n".join(f"[Parça {i+1}] {h['text']}" for i, h in enumerate(hits))
    api_key = str(get_app_config_value("gemini_api_key", "") or "").strip()
    if not api_key:
        return "Yanıt için Gemini API anahtarı gerekli.\n\nİlgili parçalar:\n" + context[:1200]
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        sys_p = ("Sana verilen PARÇALARA dayanarak soruyu yanıtla. Sadece parçalardaki "
                 "bilgiyi kullan; parçalarda yoksa 'bu bilgi belgede yok' de. Türkçe, net yanıt ver.")
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"PARÇALAR:\n{context}\n\nSORU: {question}",
            config=types.GenerateContentConfig(system_instruction=sys_p, temperature=0.3),
        )
        answer = (getattr(resp, "text", "") or "").strip()
        return answer or "Yanıt üretilemedi."
    except Exception as exc:
        return f"Yanıt üretilemedi: {exc}\n\nİlgili parçalar:\n{context[:1000]}"


def knowledge_stats() -> str:
    """Bilgi tabani koleksiyonlarinin durumu."""
    from actions.vector_store import _VEC_DIR
    if not _VEC_DIR.exists():
        return "Henüz bilgi tabanı oluşturulmadı."
    cols = list(_VEC_DIR.glob("*.json"))
    if not cols:
        return "Henüz bilgi tabanı oluşturulmadı."
    lines = ["[BİLGİ TABANI]"]
    for c in cols:
        store = VectorStore(c.stem)
        lines.append(f"  {c.stem}: {store.count()} parça")
    return "\n".join(lines)
