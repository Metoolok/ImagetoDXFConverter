
import cv2
import os
import shutil
import subprocess
import tempfile


class ImageVectorizer:
    _SEARCH_PATHS = [
        "/usr/bin", "/usr/local/bin", "/bin",
        "/opt/homebrew/bin", "/snap/bin", "/opt/local/bin",
    ]

    def __init__(self, config: dict):
        self.config = config
        self._potrace  = self._find_tool("potrace")
        self._inkscape = self._find_tool("inkscape")

    def convert_to_dxf(self, binary_img, output_dxf: str) -> dict:
        if not self._potrace:
            return {"status": "error", "message": "Potrace bulunamadı. Kurulum: sudo apt install potrace"}
        if not self._inkscape:
            return {"status": "error", "message": "Inkscape bulunamadı. Kurulum: sudo apt install inkscape"}

        with tempfile.TemporaryDirectory(prefix="vectorizer_") as tmp:
            tmp_pbm = os.path.join(tmp, "input.pbm")
            tmp_svg = os.path.join(tmp, "output.svg")

            if not cv2.imwrite(tmp_pbm, binary_img):
                return {"status": "error", "message": "PBM dosyası oluşturulamadı"}

            # 1. Potrace → SVG
            result = self._run([
                self._potrace, tmp_pbm,
                "--svg",
                "--alphamax",     str(self.config.get("alphamax",     1.1)),
                "--turdsize",     str(self.config.get("turdsize",     30)),
                "--opttolerance", str(self.config.get("opttolerance", 0.2)),
                "--turnpolicy",   self.config.get("turnpolicy", "minority"),
                "--longcurve",
                "-o", tmp_svg,
            ], "Potrace")
            if result["status"] == "error":
                return result

            # 2. SVG → DXF
            os.makedirs(os.path.dirname(os.path.abspath(output_dxf)), exist_ok=True)
            result = self._run([
                self._inkscape, tmp_svg,
                "--export-type=dxf",
                "--export-filename", output_dxf,
            ], "Inkscape")
            if result["status"] == "error":
                return result

        if not os.path.exists(output_dxf):
            return {"status": "error", "message": "DXF dosyası oluşmadı"}

        return {"status": "success", "output": output_dxf}

    def _run(self, cmd: list, tool_name: str) -> dict:
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=self.config.get("timeout", 120)
            )
            if proc.returncode != 0:
                detail = proc.stderr.strip() or proc.stdout.strip()
                return {"status": "error", "message": f"{tool_name} hatası: {detail}"}
            return {"status": "success"}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": f"{tool_name} zaman aşımı"}
        except Exception as e:
            return {"status": "error", "message": f"{tool_name} hatası: {e}"}

    def _find_tool(self, name: str) -> str | None:
        found = shutil.which(name)
        if found:
            return found
        for base in self._SEARCH_PATHS:
            candidate = os.path.join(base, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        return None
