# Dosya Yolu: backend/product-service/app/generate_embeddings.py
import time
from sentence_transformers import SentenceTransformer
from .database import SessionLocal
from . import models
from PIL import Image
import requests
from io import BytesIO

print("GERÇEK GÖRSEL EMBEDDING oluşturma script'i başladı.")

# 1. Yapay Zeka Modelini Yükle (CLIP)
# Bu model, resimleri ve metinleri 512 boyutlu bir vektöre çevirir.
print("AI modeli (CLIP) yükleniyor... (ilk seferde birkaç dakika sürebilir)")
start_time = time.time()
model = SentenceTransformer('clip-ViT-B-32')
end_time = time.time()
print(f"Model {end_time - start_time:.2f} saniyede yüklendi.")

# Veritabanı ve model vektör boyutunu kontrol etmemiz gerekebilir.
# Bu model 512 boyutlu vektör üretir. DB kolonunu buna göre ayarlamalıyız.
embedding_dim = model.get_sentence_embedding_dimension()
print(f"Modelin vektör boyutu: {embedding_dim}")


# 2. Veritabanı Bağlantısı Kur
db = SessionLocal()
print("Veritabanı bağlantısı kuruldu.")

try:
    # 3. Resim URL'si olan ve embedding'i olmayan ürünleri çek
    products_to_update = db.query(models.Product).filter(
        models.Product.image_url != None,
        models.Product.embedding == None
    ).all()

    if not products_to_update:
        print("Embedding'i olmayan yeni ürün bulunamadı. İşlem tamamlandı.")
    else:
        print(f"{len(products_to_update)} adet ürün için görsel embedding oluşturulacak.")

        # 4. Her ürün için görsel vektörü oluştur ve kaydet
        for product in products_to_update:
            try:
                print(f"- ID: {product.id}, İsim: {product.name} işleniyor...")

                # Resmi URL'den indir
                response = requests.get(product.image_url)
                response.raise_for_status() # Hata varsa yakala
                img = Image.open(BytesIO(response.content))

                # Resmi vektöre dönüştür
                embedding = model.encode(img)

                product.embedding = embedding.tolist()
            except Exception as e:
                print(f"  !!! HATA: Ürün ID {product.id} için resim işlenemedi. URL: {product.image_url}, Hata: {e}")

        # 5. Tüm değişiklikleri veritabanına kaydet
        print("Tüm embedding'ler oluşturuldu. Veritabanına kaydediliyor...")
        db.commit()
        print("Kayıt işlemi başarıyla tamamlandı!")

finally:
    # 6. Veritabanı bağlantısını kapat
    db.close()
    print("Veritabanı bağlantısı kapatıldı.")