# Resmi ve hafif bir Python imajını temel al
FROM python:3.11-slim

# Konteyner içindeki çalışma klasörünü ayarla
WORKDIR /app

# Önce sadece gereksinimler dosyasını kopyala ve kur
# Bu sayede kod her değiştiğinde kütüphaneler tekrar kurulmaz, derleme hızlanır
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Geri kalan tüm uygulama kodunu kopyala
COPY ./app /app/app

# Konteyner çalıştığında hangi komutun çalışacağını belirt
# Bu komut, FastAPI uygulamasını başlatır
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]