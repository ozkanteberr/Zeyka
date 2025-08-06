# 1. Adım: İnternet gerektirmeyen, daha önce indirdiğimiz temel imajı kullan
FROM zeyka-base-ai:latest

# 2. Adım: Sadece bu servise ait kodları kopyala
COPY ./app /app/app

# 3. Adım (Eksik Olan Buydu): Uygulamayı başlatma komutunu ekle
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]