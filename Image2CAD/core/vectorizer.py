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
        self._autotrace = self._find_tool("autotrace")
        self._potrace   = self._find_tool("potrace")

    def convert_to_dxf(self, img, output_dxf: str) -> dict:
        if self._autotrace:
            return self._convert_autotrace(img, output_dxf)
        elif self._potrace:
            return self._convert_potrace(img, output_dxf)
        else:
            return {"status": "error", "message": "autotrace veya potrace bulunamadı"}

    # ------------------------------------------------------------------
    def _convert_autotrace(self, img, output_dxf: str) -> dict:
        with tempfile.TemporaryDirectory(prefix="vectorizer_") as tmp:
            tmp_png = os.path.join(tmp, "input.png")

            # PNG olarak kaydet — AutoTrace PNG'yi en iyi işler
            if not cv2.imwrite(tmp_png, img):
                return {"status": "error", "message": "PNG oluşturulamadı"}

            out_dir = os.path.dirname(os.path.abspath(output_dxf))
            os.makedirs(out_dir, exist_ok=True)

            cmd = [
                self._autotrace,
                "--output-format",           "dxf",
                "--output-file",             output_dxf,
                "--error-threshold",         str(self.config.get("error_threshold",         2.0)),
                "--line-threshold",          str(self.config.get("line_threshold",          1.0)),
                "--corner-threshold",        str(self.config.get("corner_threshold",        60)),
                "--corner-surround",         str(self.config.get("corner_surround",         4)),
                "--corner-always-threshold", str(self.config.get("corner_always_threshold", 60)),
                "--filter-iterations",       str(self.config.get("filter_iterations",       4)),
                "--despeckle-level",         str(self.config.get("despeckle_level",         2)),
                "--despeckle-tightness",     str(self.config.get("despeckle_tightness",     2.0)),
                "--tangent-surround",        str(self.config.get("tangent_surround",        3)),
                "--color-count",             str(self.config.get("color_count",             2)),
                "--background-color",        "FFFFFF",
                "--remove-adjacent-corners",
                tmp_png,
            ]

            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True,
                    timeout=self.config.get("timeout", 120)
                )
                if proc.returncode != 0:
                    return {"status": "error", "message": f"AutoTrace hatası: {proc.stderr.strip()}"}
            except subprocess.TimeoutExpired:
                return {"status": "error", "message": "AutoTrace zaman aşımı"}
            except Exception as e:
                return {"status": "error", "message": f"AutoTrace hatası: {e}"}

        if not os.path.exists(output_dxf):
            return {"status": "error", "message": "DXF dosyası oluşmadı"}

        return {"status": "success", "output": output_dxf}

    # ------------------------------------------------------------------
    def _convert_potrace(self, img, output_dxf: str) -> dict:
        with tempfile.TemporaryDirectory(prefix="vectorizer_") as tmp:
            tmp_pbm = os.path.join(tmp, "input.pbm")

            if len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(img, 0, 255,
                                      cv2.THRESH_BINARY | cv2.THRESH_OTSU)

            if not cv2.imwrite(tmp_pbm, binary):
                return {"status": "error", "message": "PBM oluşturulamadı"}

            out_dir = os.path.dirname(os.path.abspath(output_dxf))
            os.makedirs(out_dir, exist_ok=True)

            cmd = [
                self._potrace, tmp_pbm,
                "--backend", "dxf",
                "--alphamax",     str(self.config.get("alphamax",     1.0)),
                "--turdsize",     str(self.config.get("turdsize",     2)),
                "--opttolerance", str(self.config.get("opttolerance", 0.2)),
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
            return {"status": "error", "message": "DXF oluşmadı"}

        return {"status": "success", "output": output_dxf}

    # ------------------------------------------------------------------
    def _find_tool(self, name: str) -> str | None:
        found = shutil.which(name)
        if found:
            return found
        for base in self._SEARCH_PATHS:
            candidate = os.path.join(base, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        return None
