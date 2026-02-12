# 1. Python imajını temel al
FROM python:3.9-slim

# 2. Sistem araçlarını kur (Potrace ve Inkscape senin projenin kalbi)
RUN apt-get update && apt-get install -y \
    potrace \
    inkscape \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 3. Çalışma dizini oluştur
WORKDIR /app

# 4. Kütüphane listesini kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Tüm proje dosyalarını (app.py ve core klasörü) kopyala
COPY . .

# 6. Port ayarı (Hugging Face için 7860 standarttır)
EXPOSE 7860

# 7. Uygulamayı başlat
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]