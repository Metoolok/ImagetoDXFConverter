
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
        self._potrace = self._find_tool("potrace")

    def convert_to_dxf(self, binary_img, output_dxf: str) -> dict:
        if not self._potrace:
            return {"status": "error", "message": "Potrace bulunamadı. Kurulum: sudo apt install potrace"}

        with tempfile.TemporaryDirectory(prefix="vectorizer_") as tmp:
            tmp_pbm = os.path.join(tmp, "input.pbm")

            if not cv2.imwrite(tmp_pbm, binary_img):
                return {"status": "error", "message": "PBM dosyası oluşturulamadı"}

            out_dir = os.path.dirname(os.path.abspath(output_dxf))
            os.makedirs(out_dir, exist_ok=True)

            # Potrace'in kendi DXF backend'i — SVG/Inkscape/ezdxf yok
            cmd = [
                self._potrace, tmp_pbm,
                "--backend", "dxf",
                "--alphamax",     str(self.config.get("alphamax",     1.0)),
                "--turdsize",     str(self.config.get("turdsize",     2)),
                "--opttolerance", str(self.config.get("opttolerance", 0.2)),
                "--turnpolicy",   self.config.get("turnpolicy", "minority"),
                "--longcurve",
                "-o", output_dxf,
            ]

            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True,
                    timeout=self.config.get("timeout", 120)
                )
                if proc.returncode != 0:
                    return {"status": "error", "message": f"Potrace hatası: {proc.stderr.strip()}"}
            except subprocess.TimeoutExpired:
                return {"status": "error", "message": "Potrace zaman aşımı"}
            except Exception as e:
                return {"status": "error", "message": f"Potrace hatası: {e}"}

        if not os.path.exists(output_dxf):
            return {"status": "error", "message": "DXF dosyası oluşmadı"}

        return {"status": "success", "output": output_dxf}

    def _find_tool(self, name: str) -> str | None:
        found = shutil.which(name)
        if found:
            return found
        for base in self._SEARCH_PATHS:
            candidate = os.path.join(base, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        return None
