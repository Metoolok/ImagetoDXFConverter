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

        # Potrace için görseli hazırla
        cv2.imwrite(tmp_pbm, binary_img)

        # --- YOL BULMA MANTIĞINI GÜNCELLEDİK ---
        # Önce sistemde 'potrace' ve 'inkscape' komutlarını ara
        potrace_path = shutil.which("potrace")
        inkscape_path = shutil.which("inkscape")

        # Eğer hala bulunamadıysa alternatif Linux yollarını tara
        if not potrace_path:
            for alt_path in ["/usr/local/bin/potrace", "/bin/potrace", "/usr/bin/potrace"]:
                if os.path.exists(alt_path):
                    potrace_path = alt_path
                    break
        
        if not inkscape_path:
            for alt_path in ["/usr/local/bin/inkscape", "/bin/inkscape", "/usr/bin/inkscape"]:
                if os.path.exists(alt_path):
                    inkscape_path = alt_path
                    break

        # Eğer hala YOKSA, hata döndür (bize bilgi versin)
        if not potrace_path:
            return {"status": "error", "message": "Potrace sunucuda yüklü değil. Lütfen packages.txt dosyasını kontrol edin."}

        # 1. POTRACE
        potrace_cmd = [
            potrace_path,
            tmp_pbm,
            "-s",
            "--alphamax", str(self.config.get("alphamax", 1.1)),
            "--turdsize", str(self.config.get("turdsize", 30)),
            "--opttolerance", "0.2",
            "--longcurve",
            "-o", tmp_svg
        ]
        
        try:
            subprocess.run(potrace_cmd, check=True, capture_output=True)
        except Exception as e:
            return {"status": "error", "message": f"Potrace hatası: {e}"}

        # 2. SVG → DXF (Inkscape)
        if inkscape_path:
            inkscape_cmd = [
                inkscape_path,
                tmp_svg,
                "--export-type=dxf",
                "--export-filename", output_dxf
            ]
            try:
                subprocess.run(inkscape_cmd, check=True, capture_output=True)
            except Exception as e:
                return {"status": "error", "message": f"Inkscape hatası: {e}"}
        else:
            return {"status": "error", "message": "Inkscape sunucuda bulunamadı."}

        # Temizlik
        if os.path.exists(output_dxf):
            for f in (tmp_pbm, tmp_svg):
                if os.path.exists(f): os.remove(f)
            return {"status": "success", "output": output_dxf}
        else:
            return {"status": "error", "message": "Dönüşüm başarısız, çıktı dosyası oluşmadı."}

