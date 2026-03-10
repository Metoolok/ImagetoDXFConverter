import cv2
import numpy as np


class ImagePreprocessor:
    def __init__(self, config: dict):
        self.config = config

    def process(self, image_path: str) -> np.ndarray:
        cfg = self.config

        # 1. Yükle (RGBA desteği)
        img = self._load(image_path)

        # 2. Boyutlandır
        img = self._resize(img)

        # 3. Gri tonlama
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 4. Gürültü azaltma
        k = cfg.get("denoise_ksize", 5)
        if k > 0:
            img = cv2.medianBlur(img, k | 1)

        # 5. CLAHE — lokal kontrast iyileştirme
        if cfg.get("use_clahe", True):
            clahe = cv2.createCLAHE(
                clipLimit=cfg.get("clahe_clip", 2.5),
                tileGridSize=(8, 8)
            )
            img = clahe.apply(img)

        # 6. Gamma düzeltme
        gamma = cfg.get("gamma", 1.0)
        if gamma != 1.0:
            img = self._apply_gamma(img, gamma)

        # 7. Adaptif eşikleme
        block = max(cfg.get("adaptive_block", 15) | 1, 3)
        binary = cv2.adaptiveThreshold(
            img, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            block,
            cfg.get("adaptive_c", 3)
        )

        # 8. Morfolojik kapama
        ks = cfg.get("morph_kernel_size", 3)
        if ks > 0:
            binary = cv2.morphologyEx(
                binary, cv2.MORPH_CLOSE,
                np.ones((ks, ks), np.uint8)
            )

        # 9. Genişletme (isteğe bağlı)
        dilate = cfg.get("dilate_iter", 0)
        if dilate > 0:
            binary = cv2.dilate(binary, np.ones((2, 2), np.uint8), iterations=dilate)

        # 10. İnceltme
        erode = cfg.get("erode_iter", 1)
        if erode > 0:
            binary = cv2.erode(binary, np.ones((2, 2), np.uint8), iterations=erode)

        # 11. Kenar boşluğu (Potrace kenara taşmasın)
        pad = cfg.get("border_pad", 4)
        if pad > 0:
            binary = cv2.copyMakeBorder(
                binary, pad, pad, pad, pad,
                cv2.BORDER_CONSTANT, value=255
            )

        # Debug
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
        max_w = self.config.get("resize_max_width",  2000)
        max_h = self.config.get("resize_max_height", 2000)
        scale = min(max_w / w, max_h / h, 1.0)
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)),
                             interpolation=cv2.INTER_AREA)
        return img

    @staticmethod
    def _apply_gamma(img: np.ndarray, gamma: float) -> np.ndarray:
        lut = np.array(
            [min(255, int((i / 255.0) ** (1.0 / gamma) * 255)) for i in range(256)],
            dtype=np.uint8
        )
        return cv2.LUT(img, lut)
