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
        self._inkscape_version = self._get_inkscape_version()

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

            if not os.path.exists(tmp_svg):
                return {"status": "error", "message": "Potrace SVG oluşturmadı"}

            # 2. SVG → DXF (sürüme göre uygun komut)
            out_dir = os.path.dirname(os.path.abspath(output_dxf))
            os.makedirs(out_dir, exist_ok=True)

            result = self._inkscape_to_dxf(tmp_svg, output_dxf)
            if result["status"] == "error":
                return result

        if not os.path.exists(output_dxf):
            return {"status": "error", "message": "DXF dosyası oluşmadı"}

        return {"status": "success", "output": output_dxf}

    # ------------------------------------------------------------------
    def _inkscape_to_dxf(self, svg_path: str, dxf_path: str) -> dict:
        ver = self._inkscape_version

        # Inkscape 1.0+ (yeni API)
        if ver >= (1, 0):
            cmd = [
                self._inkscape, svg_path,
                "--export-type=dxf",
                f"--export-filename={dxf_path}",
            ]
            result = self._run(cmd, "Inkscape")
            if result["status"] == "success" and os.path.exists(dxf_path):
                return result

            # 1.x'te bazen --actions daha güvenilir
            cmd2 = [
                self._inkscape,
                f"--actions=file-open:{svg_path};export-type:dxf;export-filename:{dxf_path};export-do",
            ]
            return self._run(cmd2, "Inkscape (actions)")

        # Inkscape 0.9x (eski API)
        else:
            cmd = [
                self._inkscape,
                f"--file={svg_path}",
                f"--export-dxf={dxf_path}",
            ]
            return self._run(cmd, "Inkscape (legacy)")

    # ------------------------------------------------------------------
    def _get_inkscape_version(self) -> tuple:
        if not self._inkscape:
            return (0, 0)
        try:
            proc = subprocess.run(
                [self._inkscape, "--version"],
                capture_output=True, text=True, timeout=10
            )
            import re
            m = re.search(r"(\d+)\.(\d+)", proc.stdout + proc.stderr)
            if m:
                return (int(m.group(1)), int(m.group(2)))
        except Exception:
            pass
        return (1, 0)  # bilinmiyorsa yeni API dene

    def _run(self, cmd: list, tool_name: str) -> dict:
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=self.config.get("timeout", 120)
            )
            if proc.returncode != 0:
                detail = proc.stderr.strip() or proc.stdout.strip()
                return {"status": "error", "message": f"{tool_name} hatası (kod {proc.returncode}): {detail}"}
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
