import cv2
import subprocess
import os

class ImageVectorizer:
    def __init__(self, config):
        self.config = config

    def convert_to_dxf(self, binary_img, output_dxf):
        tmp_pbm = "temp.pbm"
        tmp_svg = "temp.svg"

        # Potrace PBM sever
        cv2.imwrite(tmp_pbm, binary_img)

        # 1. POTRACE (optimize edilmiş)
        potrace_cmd = [
            "potrace",
            tmp_pbm,
            "-s",
            "--alphamax", "1.1",
            "--turdsize", "50",
            "--opttolerance", "0.2",
            "--longcurve",
            "-o", tmp_svg
        ]
        subprocess.run(potrace_cmd, check=True)

        # 2. SVG → DXF (Inkscape)
        inkscape_cmd = [
            "inkscape",
            tmp_svg,
            "--export-type=dxf",
            "--export-filename", output_dxf
        ]
        subprocess.run(inkscape_cmd, check=True)

        # Geçici dosyaları temizle
        for f in (tmp_pbm, tmp_svg):
            if os.path.exists(f):
                os.remove(f)

        return {
            "status": "success",
            "output": output_dxf
        }

