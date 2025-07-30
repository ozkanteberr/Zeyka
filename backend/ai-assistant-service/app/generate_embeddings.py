# Dosya Yolu: backend/product-service/app/generate_embeddings.py
import time
import numpy as np # Numpy kütüphanesini import ediyoruz
from .database import SessionLocal
from . import models

print("SAHTE (MOCK) Embedding oluşturma script'i başladı.")

# Veritabanı Bağlantısı Kur
db = SessionLocal()
print("Veritabanı bağlantısı kuruldu.")

try:
    # Embedding'i olmayan ürünleri veritabanından çek
    products_to_update = db.query(models.Product).filter(models.Product.embedding == None).all()

    if not products_to_update:
        print("Embedding'i olmayan yeni ürün bulunamadı. İşlem tamamlandı.")
    else:
        print(f"{len(products_to_update)} adet ürün için SAHTE embedding oluşturulacak.")

        # Her ürün için rastgele vektör oluştur ve kaydet
        for product in products_to_update:
            print(f"- ID: {product.id}, İsim: {product.name} işleniyor...")

            # 384 boyutlu rastgele bir vektör oluştur
            embedding = np.random.rand(384).tolist()

            # Vektörü veritabanındaki ilgili ürünün kolonuna ata
            product.embedding = embedding

        # Tüm değişiklikleri veritabanına kaydet
        print("Tüm embedding'ler oluşturuldu. Veritabanına kaydediliyor...")
        db.commit()
        print("Kayıt işlemi başarıyla tamamlandı!")

finally:
    # Veritabanı bağlantısını kapat
    db.close()
    print("Veritabanı bağlantısı kapatıldı.")