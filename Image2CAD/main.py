import sys
from core.preprocessor import ImagePreprocessor
from core.vectorizer import ImageVectorizer

def main():
    if len(sys.argv) < 2:
        print("Kullanım:")
        print("python main.py assets/0996.jpg")
        return

    input_path = sys.argv[1]
    output_path = "final_clean.dxf"

    config = {
        "resize_max_width": 2000,
        "adaptive_block": 15,
        "adaptive_c": 3,
        "morph_kernel_size": 3
    }

    prep = ImagePreprocessor(config)
    vect = ImageVectorizer(config)

    print("▶ Görüntü işleniyor...")
    binary = prep.process(input_path)

    print("▶ Potrace + DXF dönüşümü...")
    res = vect.convert_to_dxf(binary, output_path)

    print("✅ TAMAMLANDI")
    print("DXF:", res["output"])
    print("LibreCAD / AutoCAD ile açabilirsin.")

if __name__ == "__main__":
    main()

