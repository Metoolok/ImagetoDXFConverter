import cv2
import subprocess
import os
import shutil  # Sistem yollarını bulmak için şart

class ImageVectorizer:
    def __init__(self, config):
        self.config = config

    def convert_to_dxf(self, binary_img, output_dxf):
        tmp_pbm = "temp.pbm"
        tmp_svg = "temp.svg"

        # Potrace PBM sever
        cv2.imwrite(tmp_pbm, binary_img)

        # --- GÜNCELLEME: Komutların yerini bul ---
        potrace_path = shutil.which("potrace") or "/usr/bin/potrace"
        inkscape_path = shutil.which("inkscape") or "/usr/bin/inkscape"

        # 1. POTRACE (optimize edilmiş)
        potrace_cmd = [
            potrace_path, # 'potrace' yerine tam yol
            tmp_pbm,
            "-s",
            "--alphamax", str(self.config.get("alphamax", 1.1)), # Config'den alalım
            "--turdsize", str(self.config.get("turdsize", 50)),
            "--opttolerance", "0.2",
            "--longcurve",
            "-o", tmp_svg
        ]
        
        try:
            subprocess.run(potrace_cmd, check=True)
        except Exception as e:
            return {"status": "error", "message": f"Potrace hatası: {e}"}

        # 2. SVG → DXF (Inkscape)
        inkscape_cmd = [
            inkscape_path, # 'inkscape' yerine tam yol
            tmp_svg,
            "--export-type=dxf",
            "--export-filename", output_dxf
        ]
        
        try:
            subprocess.run(inkscape_cmd, check=True)
        except Exception as e:
            return {"status": "error", "message": f"Inkscape hatası: {e}"}

        # Geçici dosyaları temizle
        for f in (tmp_pbm, tmp_svg):
            if os.path.exists(f):
                os.remove(f)

        return {
            "status": "success",
            "output": output_dxf
        }

