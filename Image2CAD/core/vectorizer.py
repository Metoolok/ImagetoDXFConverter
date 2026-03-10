
import cv2
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET


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
        try:
            import ezdxf
        except ImportError:
            return {"status": "error", "message": "ezdxf yüklü değil. Kurulum: pip install ezdxf"}

        with tempfile.TemporaryDirectory(prefix="vectorizer_") as tmp:
            tmp_pbm = os.path.join(tmp, "input.pbm")
            tmp_svg = os.path.join(tmp, "output.svg")

            if not cv2.imwrite(tmp_pbm, binary_img):
                return {"status": "error", "message": "PBM dosyası oluşturulamadı"}

            result = self._run_potrace(tmp_pbm, tmp_svg)
            if result["status"] == "error":
                return result

            if not os.path.exists(tmp_svg):
                return {"status": "error", "message": "Potrace SVG oluşturmadı"}

            result = self._svg_to_dxf(tmp_svg, output_dxf)

        return result

    # ------------------------------------------------------------------
    def _run_potrace(self, pbm_path: str, svg_path: str) -> dict:
        cmd = [
            self._potrace, pbm_path,
            "--svg",
            "--alphamax",     str(self.config.get("alphamax",     1.0)),
            "--turdsize",     str(self.config.get("turdsize",     2)),
            "--opttolerance", str(self.config.get("opttolerance", 0.2)),
            "--turnpolicy",   self.config.get("turnpolicy", "minority"),
            "--longcurve",
            "-o", svg_path,
        ]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=self.config.get("timeout", 120)
            )
            if proc.returncode != 0:
                return {"status": "error", "message": f"Potrace hatası: {proc.stderr.strip()}"}
            return {"status": "success"}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Potrace zaman aşımı"}
        except Exception as e:
            return {"status": "error", "message": f"Potrace hatası: {e}"}

    # ------------------------------------------------------------------
    def _svg_to_dxf(self, svg_path: str, dxf_path: str) -> dict:
        import ezdxf

        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()

            # Potrace'in <g transform="..."> içindeki matrix'i oku
            transform = self._read_group_transform(root)

            doc = ezdxf.new("R2010")
            doc.units = ezdxf.units.MM
            msp = doc.modelspace()

            path_count = 0
            for elem in root.iter("{http://www.w3.org/2000/svg}path"):
                d = elem.get("d", "").strip()
                if not d:
                    continue
                subpaths = self._parse_svg_path(d, transform)
                for pts in subpaths:
                    if len(pts) >= 2:
                        msp.add_lwpolyline(
                            pts,
                            close=False,
                            dxfattribs={"layer": "0", "color": 7}
                        )
                        path_count += 1

            if path_count == 0:
                return {"status": "error", "message": "SVG içinde çizilebilir path bulunamadı"}

            out_dir = os.path.dirname(os.path.abspath(dxf_path))
            os.makedirs(out_dir, exist_ok=True)
            doc.saveas(dxf_path)
            return {"status": "success", "output": dxf_path}

        except Exception as e:
            return {"status": "error", "message": f"SVG→DXF dönüşüm hatası: {e}"}

    # ------------------------------------------------------------------
    def _read_group_transform(self, root) -> dict:
        """
        Potrace SVG çıktısındaki <g transform="..."> transform'unu okur.
        Döndürür: {"tx": float, "ty": float, "sx": float, "sy": float}

        Potrace tipik çıktı:
          translate(0, 123.456) scale(0.1, -0.1)
          ya da
          scale(1,-1) translate(0,-height)
        """
        result = {"tx": 0.0, "ty": 0.0, "sx": 1.0, "sy": 1.0}

        for elem in root.iter("{http://www.w3.org/2000/svg}g"):
            transform_str = elem.get("transform", "")
            if not transform_str:
                continue

            # translate(tx, ty)
            m = re.search(r"translate\(\s*([-\d.e]+)\s*[,\s]\s*([-\d.e]+)\s*\)", transform_str)
            if m:
                result["tx"] = float(m.group(1))
                result["ty"] = float(m.group(2))

            # scale(sx, sy) veya scale(sx)
            m = re.search(r"scale\(\s*([-\d.e]+)\s*(?:[,\s]\s*([-\d.e]+))?\s*\)", transform_str)
            if m:
                result["sx"] = float(m.group(1))
                result["sy"] = float(m.group(2)) if m.group(2) else float(m.group(1))

            break  # ilk <g> yeterli

        return result

    def _apply_transform(self, x: float, y: float, t: dict) -> tuple:
        """
        SVG transform'u uygular: önce scale, sonra translate.
        Sonucu mm'ye çevirir (Potrace pt cinsinden çalışır, 1pt = 25.4/72 mm).
        """
        # Potrace koordinatları pt (point) cinsinden
        # scale zaten pt→px dönüşümünü içeriyor
        px = x * t["sx"] + t["tx"]
        py = y * t["sy"] + t["ty"]

        # pt → mm (1 pt = 25.4/72 mm)
        mm_per_pt = 25.4 / 72.0
        return (px * mm_per_pt, py * mm_per_pt)

    # ------------------------------------------------------------------
    def _parse_svg_path(self, d: str, transform: dict) -> list:
        subpaths  = []
        current   = []
        cx = cy   = 0.0
        sx = sy   = 0.0
        last_ctrl = None

        def add(x, y):
            current.append(self._apply_transform(x, y, transform))

        def cubic_bezier(p0, p1, p2, p3, steps=16):
            for k in range(1, steps + 1):
                t = k / steps
                u = 1 - t
                x = u**3*p0[0]+3*u**2*t*p1[0]+3*u*t**2*p2[0]+t**3*p3[0]
                y = u**3*p0[1]+3*u**2*t*p1[1]+3*u*t**2*p2[1]+t**3*p3[1]
                add(x, y)

        tokens = re.findall(
            r"[MmLlHhVvCcSsQqZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?",
            d
        )

        i   = [0]
        cmd = "M"

        def next_nums(n):
            result = []
            while len(result) < n and i[0] < len(tokens):
                t = tokens[i[0]]
                if re.match(r"^[-+]?[\d.]", t):
                    result.append(float(t))
                    i[0] += 1
                else:
                    break
            return result

        while i[0] < len(tokens):
            t = tokens[i[0]]

            if re.match(r"^[MmLlHhVvCcSsQqZz]$", t):
                cmd = t
                i[0] += 1

            if cmd in ("M", "m"):
                if current:
                    subpaths.append(current)
                    current = []
                n = next_nums(2)
                if len(n) < 2: break
                if cmd == "m": cx += n[0]; cy += n[1]
                else:          cx,  cy  =  n[0], n[1]
                sx, sy = cx, cy
                add(cx, cy)
                cmd = "l" if cmd == "m" else "L"

            elif cmd in ("L", "l"):
                n = next_nums(2)
                if len(n) < 2: break
                if cmd == "l": cx += n[0]; cy += n[1]
                else:          cx,  cy  =  n[0], n[1]
                add(cx, cy)

            elif cmd in ("H", "h"):
                n = next_nums(1)
                if not n: break
                cx = cx + n[0] if cmd == "h" else n[0]
                add(cx, cy)

            elif cmd in ("V", "v"):
                n = next_nums(1)
                if not n: break
                cy = cy + n[0] if cmd == "v" else n[0]
                add(cx, cy)

            elif cmd in ("C", "c"):
                n = next_nums(6)
                if len(n) < 6: break
                if cmd == "c":
                    x1,y1 = cx+n[0],cy+n[1]
                    x2,y2 = cx+n[2],cy+n[3]
                    ex,ey = cx+n[4],cy+n[5]
                else:
                    x1,y1,x2,y2,ex,ey = n
                cubic_bezier((cx,cy),(x1,y1),(x2,y2),(ex,ey))
                last_ctrl = (x2, y2)
                cx, cy = ex, ey

            elif cmd in ("S", "s"):
                n = next_nums(4)
                if len(n) < 4: break
                x1 = 2*cx - last_ctrl[0] if last_ctrl else cx
                y1 = 2*cy - last_ctrl[1] if last_ctrl else cy
                if cmd == "s":
                    x2,y2 = cx+n[0],cy+n[1]
                    ex,ey = cx+n[2],cy+n[3]
                else:
                    x2,y2,ex,ey = n
                cubic_bezier((cx,cy),(x1,y1),(x2,y2),(ex,ey))
                last_ctrl = (x2, y2)
                cx, cy = ex, ey

            elif cmd in ("Z", "z"):
                if current:
                    add(sx, sy)
                    subpaths.append(current)
                    current = []
                cx, cy = sx, sy

            else:
                i[0] += 1

        if current:
            subpaths.append(current)

        return subpaths

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
