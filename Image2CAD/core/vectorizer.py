import cv2
import subprocess
import os
import shutil

class ImageVectorizer:
    def __init__(self, config):
        self.config = config

    def convert_to_dxf(self, binary_img, output_dxf):
        tmp_pbm = "temp.pbm"
        tmp_svg = "temp.svg"

        # Potrace PBM formatını sever, cv2 ile kaydediyoruz
        cv2.imwrite(tmp_pbm, binary_img)

        # Sistemde programların yolunu bul (Streamlit Cloud için kritik)
        potrace_path = shutil.which("potrace") or "/usr/bin/potrace"
        inkscape_path = shutil.which("inkscape") or "/usr/bin/inkscape"

        # 1. POTRACE - Senin optimize parametrelerinle
        potrace_cmd = [
            potrace_path,
            tmp_pbm,
            "-s", # SVG çıktısı üret
            "--alphamax", str(self.config.get("alphamax", 1.1)),
            "--turdsize", str(self.config.get("turdsize", 30)),
            "--opttolerance", "0.2",
            "--longcurve",
            "-o", tmp_svg
        ]
        
        try:
            subprocess.run(potrace_cmd, check=True, capture_output=True)
        except Exception as e:
            return {"status": "error", "message": f"Potrace çalıştırılamadı: {e}"}

        # 2. SVG → DXF (Inkscape üzerinden)
        inkscape_cmd = [
            inkscape_path,
            tmp_svg,
            "--export-type=dxf",
            "--export-filename", output_dxf
        ]
        
        try:
            subprocess.run(inkscape_cmd, check=True, capture_output=True)
        except Exception as e:
            return {"status": "error", "message": f"Inkscape çalıştırılamadı: {e}"}

        # Dosya oluştu mu kontrol et
        if not os.path.exists(output_dxf):
            return {"status": "error", "message": "Dönüşüm tamamlandı ama DXF dosyası bulunamadı."}

        # Geçici dosyaları temizle
        for f in (tmp_pbm, tmp_svg):
            if os.path.exists(f):
                os.remove(f)

        return {
            "status": "success",
            "output": output_dxf
        }

