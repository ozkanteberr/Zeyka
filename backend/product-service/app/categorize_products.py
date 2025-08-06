# Dosya Yolu: backend/product-service/app/categorize_products.py
import requests
import time
from database import SessionLocal
import models

print("Toplu ürün kategorizasyon script'i başladı.")

db = SessionLocal()
CATEGORIZATION_API_URL = "http://categorization_service:8000/categorize-image"

try:
    # Kategorisi olmayan ürünleri veritabanından çek
    products_to_categorize = db.query(models.Product).filter(
        models.Product.image_url != None,
        models.Product.category == None
    ).all()

    if not products_to_categorize:
        print("Kategorize edilecek yeni ürün bulunamadı.")
    else:
        print(f"{len(products_to_categorize)} adet ürün kategorize edilecek.")

        for product in products_to_categorize:
            try:
                print(f"- ID: {product.id}, İsim: {product.name} işleniyor...")

                # categorization-service'e istek at
                response = requests.post(CATEGORIZATION_API_URL, json={"image_url": product.image_url})
                response.raise_for_status() # Hata varsa yakala

                data = response.json()
                category = data.get("category")

                if category:
                    product.category = category
                    print(f"  -> Kategori bulundu: {category}")
                else:
                    print("  -> Geçerli bir kategori bulunamadı.")

                # API'yi yormamak için küçük bir gecikme ekle
                time.sleep(1)

            except Exception as e:
                print(f"  !!! HATA: Ürün ID {product.id} için kategorizasyon başarısız. Hata: {e}")

        print("Kategorizasyon tamamlandı. Veritabanı güncelleniyor...")
        db.commit()
        print("Veritabanı başarıyla güncellendi!")

finally:
    db.close()
    print("Veritabanı bağlantısı kapatıldı.")