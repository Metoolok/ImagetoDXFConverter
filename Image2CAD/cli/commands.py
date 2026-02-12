"""
Command Line Interface
Provides CLI for batch processing and automation
"""

import argparse
import sys
from pathlib import Path
from typing import List
from colorama import Fore, Style, init

# Colorama'yı başlat
init(autoreset=True)


class CLICommands:
    """
    CLI komutları ve argparse konfigürasyonu.
    """

    @staticmethod
    def create_parser() -> argparse.ArgumentParser:
        """
        Ana argparse parser'ı oluşturur.

        Returns:
            ArgumentParser
        """
        parser = argparse.ArgumentParser(
            description=f"{Fore.CYAN}Image2CAD{Style.RESET_ALL} - AI-Powered Image to CAD Vectorization",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Tek dosya çevirme
  python main.py convert image.png -o output.dxf

  # Threshold ayarlama
  python main.py convert image.png -t 150

  # Önizleme modu
  python main.py preview image.png

  # Batch işleme
  python main.py batch ./images/*.png -o ./output/
            """
        )

        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # CONVERT komutu
        convert_parser = subparsers.add_parser('convert', help='Convert single image to DXF')
        convert_parser.add_argument('input', type=str, help='Input image file')
        convert_parser.add_argument('-o', '--output', type=str, help='Output DXF file (default: input_name.dxf)')
        convert_parser.add_argument('-t', '--threshold', type=int, default=127,
                                    help='Binary threshold (0-255, default: 127)')
        convert_parser.add_argument('--adaptive', action='store_true',
                                    help='Use adaptive threshold')
        convert_parser.add_argument('--no-simplify', action='store_true',
                                    help='Disable contour simplification')
        convert_parser.add_argument('--epsilon', type=float, default=0.01,
                                    help='Simplification factor (default: 0.01)')
        convert_parser.add_argument('-c', '--config', type=str,
                                    help='Custom config file path')

        # PREVIEW komutu
        preview_parser = subparsers.add_parser('preview', help='Preview preprocessing steps')
        preview_parser.add_argument('input', type=str, help='Input image file')
        preview_parser.add_argument('-s', '--save', type=str,
                                    help='Save preview to file')

        # BATCH komutu
        batch_parser = subparsers.add_parser('batch', help='Batch process multiple images')
        batch_parser.add_argument('inputs', nargs='+', help='Input image files (supports wildcards)')
        batch_parser.add_argument('-o', '--output-dir', type=str, required=True,
                                  help='Output directory for DXF files')
        batch_parser.add_argument('-t', '--threshold', type=int, default=127)
        batch_parser.add_argument('--adaptive', action='store_true')
        batch_parser.add_argument('-c', '--config', type=str)

        # CONFIG komutu
        config_parser = subparsers.add_parser('config', help='Manage configuration')
        config_parser.add_argument('action', choices=['show', 'reset', 'edit'],
                                   help='Config action')
        config_parser.add_argument('-f', '--file', type=str,
                                   help='Config file path')

        # Global arguments
        parser.add_argument('-v', '--verbose', action='store_true',
                            help='Enable verbose logging')
        parser.add_argument('--version', action='version',
                            version='Image2CAD v0.1.0')

        return parser

    @staticmethod
    def print_banner():
        """
        CLI banner'ı yazdırır.
        """
        banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════╗
║                                                       ║
║              {Fore.WHITE}IMAGE2CAD{Fore.CYAN} v0.1.0                       ║
║     {Fore.GREEN}AI-Powered Image to CAD Vectorization{Fore.CYAN}        ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(banner)

    @staticmethod
    def print_success(message: str):
        """Success mesajı yazdırır."""
        print(f"{Fore.GREEN}✓{Style.RESET_ALL} {message}")

    @staticmethod
    def print_error(message: str):
        """Error mesajı yazdırır."""
        print(f"{Fore.RED}✗{Style.RESET_ALL} {message}", file=sys.stderr)

    @staticmethod
    def print_info(message: str):
        """Info mesajı yazdırır."""
        print(f"{Fore.CYAN}ℹ{Style.RESET_ALL} {message}")

    @staticmethod
    def print_warning(message: str):
        """Warning mesajı yazdırır."""
        print(f"{Fore.YELLOW}⚠{Style.RESET_ALL} {message}")