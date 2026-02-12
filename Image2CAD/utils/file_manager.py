"""
File Management Utilities
Handles file I/O operations and validation
"""

import os
import yaml
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FileManager:
    """
    Dosya yönetimi için utility sınıfı.
    """

    SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
    SUPPORTED_OUTPUT_FORMATS = {'.dxf'}

    @staticmethod
    def validate_image_path(filepath: str) -> bool:
        """
        Görüntü dosyasını doğrular.

        Args:
            filepath: Dosya yolu

        Returns:
            True ise dosya geçerli

        Raises:
            FileNotFoundError: Dosya bulunamadı
            ValueError: Desteklenmeyen format
        """
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        if not path.is_file():
            raise ValueError(f"Not a file: {filepath}")

        if path.suffix.lower() not in FileManager.SUPPORTED_IMAGE_FORMATS:
            raise ValueError(
                f"Unsupported format: {path.suffix}. "
                f"Supported: {FileManager.SUPPORTED_IMAGE_FORMATS}"
            )

        logger.info(f"Image path validated: {filepath}")
        return True

    @staticmethod
    def ensure_output_directory(filepath: str) -> Path:
        """
        Çıkış dosyası için dizin oluşturur.

        Args:
            filepath: Çıkış dosya yolu

        Returns:
            Path object
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory ensured: {path.parent}")
        return path

    @staticmethod
    def generate_output_filename(input_path: str,
                                 suffix: str = "",
                                 extension: str = ".dxf") -> str:
        """
        Input dosyasından output dosya adı üretir.

        Args:
            input_path: Input dosya yolu
            suffix: Dosya adına eklenecek suffix (örn: "_vectorized")
            extension: Çıkış uzantısı

        Returns:
            Output dosya yolu
        """
        path = Path(input_path)
        output_name = f"{path.stem}{suffix}{extension}"
        output_path = path.parent / output_name

        logger.info(f"Generated output filename: {output_path}")
        return str(output_path)

    @staticmethod
    def load_config(config_path: str) -> dict:
        """
        YAML config dosyasını yükler.

        Args:
            config_path: Config dosya yolu

        Returns:
            Config dict
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Config loaded from: {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    @staticmethod
    def save_config(config: dict, config_path: str):
        """
        Config dict'i YAML olarak kaydeder.

        Args:
            config: Config dict
            config_path: Kayıt yolu
        """
        try:
            FileManager.ensure_output_directory(config_path)
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            logger.info(f"Config saved to: {config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    @staticmethod
    def get_default_config() -> dict:
        """
        Varsayılan config döndürür (config dosyası yoksa).

        Returns:
            Default config dict
        """
        return {
            'preprocessing': {
                'resize_max_width': 2000,
                'resize_max_height': 2000,
                'denoise_strength': 5
            },
            'vectorization': {
                'threshold': 127,
                'edge_detection_method': 'canny',
                'min_contour_area': 10
            },
            'output': {
                'dxf_version': 'R2010',
                'default_layer': '0',
                'line_color': 7,
                'precision': 2
            }
        }