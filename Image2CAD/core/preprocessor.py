import cv2
import numpy as np


class ImagePreprocessor:
    def __init__(self, config: dict):
        self.config = config

    def process(self, image_path: str) -> np.ndarray:
        cfg = self.config

        # 1. Yükle
        img = self._load(image_path)

        # 2. Boyutlandır — yüksek çözünürlük kalite demek
        img = self._resize(img)

        # 3. Gri tonlama
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 4. Sadece hafif gürültü azaltma — AutoTrace kendi işini yapacak
        img = cv2.GaussianBlur(img, (3, 3), 0)

        # 5. Kontrast gerdirme — histogram stretch
        min_val = np.percentile(img, 2)
        max_val = np.percentile(img, 98)
        if max_val > min_val:
            img = np.clip((img - min_val) * 255.0 / (max_val - min_val), 0, 255).astype(np.uint8)

        if cfg.get("debug", False):
            cv2.imwrite("debug_output.png", img)

        # Binary DEĞİL — gri görüntü döndür, AutoTrace halleder
        return img

    def _load(self, path: str) -> np.ndarray:
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Görüntü yüklenemedi: {path}")
        if img.ndim == 3 and img.shape[2] == 4:
            alpha = img[:, :, 3:4].astype(float) / 255.0
            rgb   = img[:, :, :3].astype(float)
            img   = (rgb * alpha + 255.0 * (1.0 - alpha)).astype(np.uint8)
        return img

    def _resize(self, img: np.ndarray) -> np.ndarray:
        h, w  = img.shape[:2]
        max_w = self.config.get("resize_max_width",  3000)
        max_h = self.config.get("resize_max_height", 3000)
        scale = min(max_w / w, max_h / h, 1.0)
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)),
                             interpolation=cv2.INTER_AREA)
        return img
