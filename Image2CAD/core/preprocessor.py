import cv2
import numpy as np

class ImagePreprocessor:
    def __init__(self, config):
        self.config = config

    def process(self, image_path):
        # 1. Gri tonlamada yükle
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError("Görüntü yüklenemedi")

        # 2. Boyutlandırma
        h, w = img.shape
        max_w = self.config.get("resize_max_width", 2000)
        if w > max_w:
            scale = max_w / w
            img = cv2.resize(
                img,
                (int(w * scale), int(h * scale)),
                interpolation=cv2.INTER_AREA
            )

        # 3. Gürültü azaltma (parlama yumuşatma)
        img = cv2.medianBlur(img, 5)

        # 4. Adaptive Threshold (kritik ayar)
        block = self.config.get("adaptive_block", 15)
        c_val = self.config.get("adaptive_c", 3)

        binary = cv2.adaptiveThreshold(
            img,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            block,
            c_val
        )

        # 5. Morfolojik kapatma (kopuklukları birleştir)
        kernel_size = self.config.get("morph_kernel_size", 3)
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # 6. Çok hafif erosion (Potrace için çizgiyi inceltir)
        binary = cv2.erode(binary, np.ones((2, 2), np.uint8), iterations=1)

        # DEBUG istersen aç
        # cv2.imwrite("debug_binary.png", binary)

        return binary
