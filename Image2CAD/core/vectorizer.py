
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

    def convert_to_dxf(self, binary_img, output_dxf: str) -> dict:
        if self._autotrace:
            return self._convert_autotrace(binary_img, output_dxf)
        elif self._potrace:
            return self._convert_potrace(binary_img, output_dxf)
        else:
            return {"status": "error", "message": "autotrace veya potrace bulunamadı. Kurulum: sudo apt install autotrace"}

    # ------------------------------------------------------------------
    # AutoTrace — DXF'e doğrudan çıktı, Y ekseni sorunu yok
    # ------------------------------------------------------------------
    def _convert_autotrace(self, binary_img, output_dxf: str) -> dict:
        with tempfile.TemporaryDirectory(prefix="vectorizer_") as tmp:
            tmp_pnm = os.path.join(tmp, "input.pnm")

            if not cv2.imwrite(tmp_pnm, binary_img):
                return {"status": "error", "message": "PNM dosyası oluşturulamadı"}

            out_dir = os.path.dirname(os.path.abspath(output_dxf))
            os.makedirs(out_dir, exist_ok=True)

            cmd = [
                self._autotrace,
                "--output-format", "dxf",
                "--output-file",   output_dxf,
                "--corner-threshold",   str(self.config.get("corner_threshold",  60)),
                "--error-threshold",    str(self.config.get("error_threshold",   2.0)),
                "--line-threshold",     str(self.config.get("line_threshold",    1.0)),
                "--filter-iterations",  str(self.config.get("filter_iterations", 4)),
                "--remove-adjacent-corners",
                tmp_pnm,
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
    # Potrace fallback — autotrace yoksa
    # ------------------------------------------------------------------
    def _convert_potrace(self, binary_img, output_dxf: str) -> dict:
        with tempfile.TemporaryDirectory(prefix="vectorizer_") as tmp:
            tmp_pbm = os.path.join(tmp, "input.pbm")

            if not cv2.imwrite(tmp_pbm, binary_img):
                return {"status": "error", "message": "PBM dosyası oluşturulamadı"}

            out_dir = os.path.dirname(os.path.abspath(output_dxf))
            os.makedirs(out_dir, exist_ok=True)

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
```

`packages.txt` dosyasına ekle:
```
autotrace
potrace
