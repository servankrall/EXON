"""
Görsel oluşturma — birden çok motor (ücretsiz seçenekler dahil).
Servan Kanğal tarafından yapılmıştır — EXON Windows Edition

Denenme sırası (ilk başarılı sonuç kullanılır):
1. Gemini native image modelleri (generate_content)         — kota/billing gerekir
2. Imagen modelleri (generate_images)                       — kota/billing gerekir
3. Hugging Face Inference API (ücretsiz token, opsiyonel)   — config: hf_api_key
4. Pollinations.ai (TAMAMEN ÜCRETSİZ, ANAHTAR GEREKTİRMEZ)  — her zaman yedek

Yani API anahtarı/kotası olmasa bile Pollinations sayesinde görsel üretimi çalışır.
Tüm denemeler başarısız olursa gerçek hata mesajı döndürülür.
"""

from __future__ import annotations

import base64
import binascii
import datetime
import os
import urllib.parse
from pathlib import Path

import requests
from google import genai
from google.genai import types

from app_config import get_app_config_value


from paths import DATA_DIR

OUTPUT_DIR = DATA_DIR / "generated_images"

# generate_content ile çalışan Gemini görsel modelleri (hızlı/ucuz olan önce)
GEMINI_IMAGE_MODELS = (
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
    "gemini-2.0-flash-preview-image-generation",
)
# generate_images ile çalışan Imagen modelleri (hızlı olan önce)
IMAGEN_MODELS = (
    "imagen-4.0-fast-generate-001",
    "imagen-4.0-generate-001",
)

_IMG_MAGIC = (b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"RIFF")


def _output_path() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return OUTPUT_DIR / f"exon_{stamp}.png"


def _looks_like_image(data: bytes) -> bool:
    return bool(data) and any(data[:4].startswith(m) for m in _IMG_MAGIC)


def _coerce_bytes(data) -> bytes | None:
    """inline_data bazen ham bytes, bazen base64 string olabilir; ikisini de çöz."""
    if not data:
        return None
    if isinstance(data, bytes):
        if _looks_like_image(data):
            return data
        try:
            decoded = base64.b64decode(data, validate=True)
            if _looks_like_image(decoded):
                return decoded
        except (binascii.Error, ValueError):
            pass
        return data
    if isinstance(data, str):
        try:
            return base64.b64decode(data)
        except (binascii.Error, ValueError):
            return None
    return None


def _save_bytes(data: bytes) -> Path:
    path = _output_path()
    path.write_bytes(data)
    return path


def _is_quota_error(message: str) -> bool:
    low = message.lower()
    return any(k in low for k in ("429", "resource_exhausted", "quota", "billing"))


def _extract_image_bytes_from_response(response) -> bytes | None:
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            inline = getattr(part, "inline_data", None)
            if inline is not None:
                coerced = _coerce_bytes(getattr(inline, "data", None))
                if coerced:
                    return coerced
    return None


def _try_gemini_image(client: "genai.Client", prompt: str, errors: list[str]) -> bytes | None:
    config_variants = [
        types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        types.GenerateContentConfig(response_modalities=["IMAGE"]),
        None,
    ]
    for model in GEMINI_IMAGE_MODELS:
        for cfg in config_variants:
            try:
                kwargs = {"model": model, "contents": prompt}
                if cfg is not None:
                    kwargs["config"] = cfg
                response = client.models.generate_content(**kwargs)
                data = _extract_image_bytes_from_response(response)
                if data:
                    return data
            except TypeError:
                continue  # bu SDK sürümü response_modalities kabul etmiyor → sıradaki varyant
            except Exception as exc:
                msg = str(exc)
                errors.append(f"{model}: {msg[:160]}")
                if _is_quota_error(msg):
                    return None  # kota yok; diğer Gemini modelleri aynı kotayı paylaşır
                break
    return None


def _try_imagen(client: "genai.Client", prompt: str, errors: list[str]) -> bytes | None:
    for model in IMAGEN_MODELS:
        try:
            result = client.models.generate_images(
                model=model,
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1),
            )
            generated = getattr(result, "generated_images", None) or []
            for item in generated:
                image = getattr(item, "image", None)
                data = _coerce_bytes(getattr(image, "image_bytes", None))
                if data:
                    return data
        except Exception as exc:
            msg = str(exc)
            errors.append(f"{model}: {msg[:160]}")
            if _is_quota_error(msg):
                return None
    return None


def _try_huggingface(prompt: str, errors: list[str]) -> bytes | None:
    """Ücretsiz Hugging Face token'ı varsa (config: hf_api_key) kullanır."""
    token = (str(get_app_config_value("hf_api_key", "") or "").strip()
             or os.environ.get("HF_API_KEY", "").strip())
    if not token:
        return None
    models = ("black-forest-labs/FLUX.1-schnell",
              "stabilityai/stable-diffusion-xl-base-1.0")
    for model in models:
        try:
            r = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers={"Authorization": f"Bearer {token}"},
                json={"inputs": prompt},
                timeout=120,
            )
            ctype = r.headers.get("Content-Type", "")
            if r.status_code == 200 and ctype.startswith("image"):
                return r.content
            errors.append(f"hf {model}: HTTP {r.status_code} {r.text[:80]}")
        except Exception as exc:
            errors.append(f"hf {model}: {str(exc)[:120]}")
    return None


def _try_pollinations(prompt: str, errors: list[str]) -> bytes | None:
    """Pollinations.ai — tamamen ücretsiz, anahtar gerektirmez. Güvenilir yedek."""
    try:
        url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
        r = requests.get(
            url,
            params={"width": 1024, "height": 1024, "nologo": "true", "model": "flux"},
            timeout=90,
        )
        if r.status_code == 200 and _looks_like_image(r.content):
            return r.content
        errors.append(f"pollinations: HTTP {r.status_code}")
    except Exception as exc:
        errors.append(f"pollinations: {str(exc)[:160]}")
    return None


def generate_image(prompt: str) -> dict:
    """
    Metin isteminden görsel üretir.
    Döner: {"ok": bool, "path": str|None, "message": str}
    """
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "path": None,
                "message": "Görsel oluşturmak için bir açıklama vermelisin."}

    errors: list[str] = []
    data: bytes | None = None
    source = ""

    # 1-2) Gemini / Imagen (kota varsa)
    api_key = str(get_app_config_value("gemini_api_key", "") or "").strip()
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            data = _try_gemini_image(client, prompt, errors)
            if data:
                source = "Gemini"
            if not data:
                data = _try_imagen(client, prompt, errors)
                if data:
                    source = "Imagen"
        except Exception as exc:
            errors.append(f"client: {str(exc)[:160]}")

    # 3) Hugging Face (ücretsiz token varsa)
    if not data:
        data = _try_huggingface(prompt, errors)
        if data:
            source = "HuggingFace"

    # 4) Pollinations (ücretsiz, anahtarsız yedek)
    if not data:
        data = _try_pollinations(prompt, errors)
        if data:
            source = "Pollinations"

    if not data:
        joined = " | ".join(errors)
        return {"ok": False, "path": None,
                "message": ("Görsel oluşturulamadı. Tüm motorlar başarısız oldu. "
                            f"Ayrıntı: {joined[:300]}")}

    try:
        path = _save_bytes(data)
    except Exception as exc:
        return {"ok": False, "path": None,
                "message": f"Görsel oluşturuldu ama kaydedilemedi: {exc}"}

    return {"ok": True, "path": str(path),
            "message": f"Görsel oluşturuldu ({source}) ve kaydedildi: {path.name}"}
