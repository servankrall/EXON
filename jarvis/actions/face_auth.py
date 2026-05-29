"""
Yüz tanıma — kamera ile giriş / kişi tanıma (OpenCV LBPH).
Servan Kanğal tarafından yapılmıştır — EXON Windows Edition

Kurulum:
- pip install opencv-contrib-python   (cv2.face için 'contrib' şart)
- faces/<isim>/ klasörüne o kişinin birkaç yüz fotoğrafını (.jpg) koy.
  Örn: faces/Servan/1.jpg, faces/Servan/2.jpg ...

recognize() webcam'i açar, eğitilmiş kişilerden birini tanırsa adını döndürür.
"""

from __future__ import annotations

import time
from pathlib import Path

from paths import DATA_DIR

FACES_DIR = DATA_DIR / "faces"

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
    _CV2_OK = True
    _HAS_FACE = hasattr(cv2, "face")
except Exception:
    _CV2_OK = False
    _HAS_FACE = False


class FaceAuth:
    def __init__(self):
        self.ready = False
        self.labels: dict[int, str] = {}
        self._recognizer = None
        self._cascade = None
        if _CV2_OK:
            try:
                self._cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            except Exception:
                self._cascade = None

    def available(self) -> tuple[bool, str]:
        if not _CV2_OK:
            return False, "OpenCV kurulu değil (pip install opencv-contrib-python)"
        if not _HAS_FACE:
            return False, "cv2.face yok — 'opencv-contrib-python' gerekli"
        if self._cascade is None:
            return False, "Yüz tespit modeli (haarcascade) yüklenemedi"
        if not FACES_DIR.exists() or not any(FACES_DIR.iterdir()):
            return False, "faces/<isim>/ klasörüne yüz fotoğrafı ekle"
        return True, "hazır"

    def enroll_and_train(self) -> bool:
        ok, _ = self.available()
        if not ok:
            return False
        images, ids = [], []
        self.labels = {}
        next_id = 0
        for person_dir in sorted(FACES_DIR.iterdir()):
            if not person_dir.is_dir():
                continue
            label_id = next_id
            self.labels[label_id] = person_dir.name
            next_id += 1
            for img_path in person_dir.glob("*.*"):
                gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
                if gray is None:
                    continue
                faces = self._cascade.detectMultiScale(gray, 1.2, 5)
                for (x, y, w, h) in faces:
                    images.append(gray[y:y + h, x:x + w])
                    ids.append(label_id)
        if not images:
            return False
        self._recognizer = cv2.face.LBPHFaceRecognizer_create()
        self._recognizer.train(images, np.array(ids))
        self.ready = True
        return True

    def recognize(self, timeout: float = 6.0, threshold: float = 75.0) -> str | None:
        """Webcam açar; tanınan kişinin adını döndürür, tanıyamazsa None."""
        if not self.ready and not self.enroll_and_train():
            return None
        cap = cv2.VideoCapture(0)
        if not cap or not cap.isOpened():
            return None
        name = None
        start = time.time()
        try:
            while time.time() - start < timeout:
                ok, frame = cap.read()
                if not ok:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self._cascade.detectMultiScale(gray, 1.2, 5)
                for (x, y, w, h) in faces:
                    label, conf = self._recognizer.predict(gray[y:y + h, x:x + w])
                    if conf <= threshold:
                        name = self.labels.get(label)
                        break
                if name:
                    break
        finally:
            cap.release()
        return name

    def recognize_summary(self) -> str:
        ok, msg = self.available()
        if not ok:
            return f"Yüz tanıma kullanılamıyor: {msg}"
        name = self.recognize()
        if name:
            return f"Yüz tanındı: {name}. Hoş geldin {name}!"
        return "Kamerada tanıdık bir yüz göremedim."
