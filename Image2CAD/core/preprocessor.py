import cv2
import numpy as np


class ImagePreprocessor:
    def __init__(self, config: dict):
        self.config = config

    def process(self, image_path: str) -> np.ndarray:
        cfg = self.config

        # 1. Yükle
        img = self._load(image_path)

        # 2. Boyutlandır — yüksek çözünürlük = iyi vektör
        img = self._resize(img)

        # 3. Gri
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 4. Bilateral filtre — kenarları korur, gürültüyü siler
        img = cv2.bilateralFilter(img, 9, 75, 75)

        # 5. CLAHE — lokal kontrast, karanlık bölgeleri kurtarır
        clahe = cv2.createCLAHE(
            clipLimit=cfg.get("clahe_clip", 2.0),
            tileGridSize=(8, 8)
        )
        img = clahe.apply(img)

        # 6. Keskinleştirme — çizgi detaylarını belirginleştirir
        if cfg.get("sharpen", True):
            kernel = np.array([
                [ 0, -1,  0],
                [-1,  5, -1],
                [ 0, -1,  0]
            ], dtype=np.float32)
            img = cv2.filter2D(img, -1, kernel)

        # 7. Eşikleme — mod seçimi
        mode = cfg.get("threshold_mode", "adaptive")

        if mode == "otsu":
            _, binary = cv2.threshold(
                img, 0, 255,
                cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
            )
        elif mode == "adaptive":
            block = cfg.get("adaptive_block", 15) | 1
            block = max(block, 3)
            binary = cv2.adaptiveThreshold(
                img, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                block,
                cfg.get("adaptive_c", 3)
            )
        else:  # sabit eşik
            _, binary = cv2.threshold(
                img,
                cfg.get("threshold_value", 127),
                255,
                cv2.THRESH_BINARY_INV
            )

        # 8. Morfolojik kapama — kopuk çizgileri birleştir
        ks = cfg.get("morph_kernel_size", 2)
        if ks > 0:
            binary = cv2.morphologyEx(
                binary, cv2.MORPH_CLOSE,
                np.ones((ks, ks), np.uint8)
            )

        # 9. İnceltme — Potrace için ince çizgi
        erode = cfg.get("erode_iter", 1)
        if erode > 0:
            binary = cv2.erode(
                binary,
                np.ones((2, 2), np.uint8),
                iterations=erode
            )

        # 10. Kenar boşluğu
        pad = cfg.get("border_pad", 8)
        if pad > 0:
            binary = cv2.copyMakeBorder(
                binary, pad, pad, pad, pad,
                cv2.BORDER_CONSTANT, value=255
            )

        if cfg.get("debug", False):
            cv2.imwrite("debug_binary.png", binary)

        return binary

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
            img = cv2.resize(
                img,
                (int(w * scale), int(h * scale)),
                interpolation=cv2.INTER_AREA
            )
        return img
