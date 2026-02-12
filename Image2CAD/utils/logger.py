"""
Logging Configuration
Sets up consistent logging across the application
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "img2cad",
                 level: int = logging.INFO,
                 log_file: bool = True,
                 log_dir: str = "logs") -> logging.Logger:
    """
    Uygulama logger'ını konfigüre eder.

    Args:
        name: Logger adı
        level: Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Dosyaya da logla
        log_dir: Log dosyası dizini

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Önceki handler'ları temizle (duplicate önleme)
    if logger.handlers:
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (renkli)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (opsiyonel)
    if log_file:
        Path(log_dir).mkdir(exist_ok=True)
        log_filename = f"{log_dir}/img2cad_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Dosyaya daha detaylı log
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Mevcut logger'ı döndürür veya yeni oluşturur.

    Args:
        name: Logger adı

    Returns:
        Logger instance
    """
    return logging.getLogger(name)