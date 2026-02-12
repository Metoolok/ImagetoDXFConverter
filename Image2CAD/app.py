import streamlit as st
import os
import cv2
import numpy as np
from core.preprocessor import ImagePreprocessor
from core.vectorizer import ImageVectorizer

# Sayfa Ayarları (Logo ve Başlık Sekmesi)
st.set_page_config(
    page_title="Metoolok - Image2CAD",
    page_icon="🏗️",
    layout="centered"
)

# --- TASARIM (CSS) ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stTitle {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        color: #1e1e1e;
        text-align: center;
    }
    .footer {
        text-align: center;
        padding: 20px;
        color: #6c757d;
        font-size: 0.8rem;
    }
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ÜST BÖLÜM: LOGO VE BAŞLIK ---
st.markdown("""
    <div class="logo-container">
        <h1 style="color: #007bff; margin:0;">Ⓜ️ Metoolok</h1>
    </div>
    """, unsafe_allow_html=True)

st.title("Image2CAD: Otomatik DXF Dönüştürücü")
st.markdown(
    "<p style='text-align: center;'>Görüntüleri saniyeler içinde kesime hazır profesyonel vektörlere dönüştürün.</p>",
    unsafe_allow_html=True)

# Sabit Gelişmiş Ayarlar (Senin en iyi sonuç veren değerlerin)
FIXED_CONFIG = {
    "resize_max_width": 2500,
    "threshold": 180,
    "alphamax": 1.1,
    "turdsize": 30,
    "morph_kernel_size": 3
}

# --- ANA İÇERİK ---
st.divider()

uploaded_file = st.file_uploader("Çizime dönüştürülecek resmi sürükleyin veya seçin", type=['jpg', 'png', 'jpeg'])

if uploaded_file is not None:
    # Geçici dosya kayıt
    input_path = f"temp_{uploaded_file.name}"
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Görsel Önizleme
    with st.expander("Yüklenen Resmi Gör", expanded=True):
        st.image(uploaded_file, use_container_width=True)

    # İşlem Butonu
    if st.button("🚀 DXF DOSYASINI HAZIRLA", use_container_width=True):
        with st.status("Metoolok Motoru Çalışıyor...", expanded=True) as status:
            try:
                # Arka plandaki sınıflar
                prep = ImagePreprocessor(FIXED_CONFIG)
                vect = ImageVectorizer(FIXED_CONFIG)

                st.write("🔍 Görüntü iyileştiriliyor...")
                binary_mask = prep.process(input_path)

                st.write("📐 Vektör çizgileri hesaplanıyor...")
                output_dxf = "metoolok_output.dxf"
                result = vect.convert_to_dxf(binary_mask, output_dxf)

                if result["status"] == "success":
                    status.update(label="✅ Çizim Hazır!", state="complete", expanded=False)
                    st.balloons()
                    st.success("Çizim başarıyla oluşturuldu.")

                    # İndirme Butonu
                    with open(output_dxf, "rb") as file:
                        st.download_button(
                            label="📥 DXF DOSYASINI İNDİR",
                            data=file,
                            file_name=f"Metoolok_{os.path.splitext(uploaded_file.name)[0]}.dxf",
                            mime="application/dxf",
                            use_container_width=True
                        )
                else:
                    # Hata durumunda detayı gösteriyoruz
                    status.update(label="❌ İşlem Başarısız", state="error")
                    st.error(f"Hata Detayı: {result.get('message', 'Bilinmeyen bir hata oluştu.')}")

            except Exception as e:
                st.error(f"Sistem Hatası: {e}")
            finally:
                # Temizlik
                if os.path.exists(input_path): os.remove(input_path)
                # DXF'i silmiyoruz ki indirme butonu çalışabilsin, 
                # ancak bir sonraki döngüde veya script sonunda temizlenebilir.

# --- ALT BÖLÜM: FOOTER ---
st.markdown("""
    <div class="footer">
        © 2026 Metoolok. Tüm hakları saklıdır. <br>
        Mühendislik için tasarlandı.
    </div>
    """, unsafe_allow_html=True)
