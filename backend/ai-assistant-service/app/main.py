# ai-assistant-service/app/main.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import json
import httpx
app = FastAPI()

# CORS Ayarları
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GEMINI API KURULUMU ---
# Kendi API anahtarınızı buraya yapıştırın
# DİKKAT: Gerçek bir projede bu anahtar asla koda yazılmaz, environment variable olarak saklanır.
try:
    GOOGLE_API_KEY = "AIzaSyChcIh8HYB4rQaEbfNH68Jw3mntvM7zu9A" 
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
except Exception as e:
    print(f"Gemini modeli yüklenirken hata oluştu: {e}")
    model = None
# -------------------------

class MatchedProduct(BaseModel):
    id: int
    name: str
    price: str
    description: str | None = None

# Gemini'den gelen her bir öneri
class SuggestedItem(BaseModel):
    item_type: str
    description: str
    optional: bool = False

# Her bir kombin parçası ve eşleşen ürünlerimiz
class ComboPiece(BaseModel):
    suggestion: SuggestedItem
    matched_products: list[MatchedProduct]

# Frontend'e göndereceğimiz nihai zengin yanıt
class FinalFashionResponse(BaseModel):
    explanation: str
    combo_pieces: list[ComboPiece]

class FashionPromptRequest(BaseModel):
    prompt: str

@app.post("/generate-fashion-combo", response_model=FinalFashionResponse)
async def generate_fashion_combo(request: FashionPromptRequest):
    if not model:
        raise HTTPException(status_code=503, detail="AI model is not available.")

    # ... (prompt_template aynı kalabilir) ...
    prompt_template = f"""
    Bir e-ticaret sitesi için moda asistanı olarak görev yapıyorsun.
    Kullanıcının isteğine göre bir kombin oluştur ve sonucu JSON formatında ver.
    JSON objesi şu alanları içermeli: "explanation" (bu kombini neden önerdiğini anlatan kısa bir metin) ve "suggested_items" (bir liste).
    Bu listedeki her bir obje de şu alanları içermeli: "item_type" (örneğin 'Gömlek', 'Pantolon'), "description" (ürünün kısa bir tanımı, örneğin 'Beyaz keten, uzun kollu') ve "optional" (bu parçanın opsiyonel olup olmadığı, true/false).
    En fazla 4 parça öner.
    Kullanıcı isteği: "{request.prompt}"
    """

    try:
        # 1. Adım: Gemini'den kombin önerilerini al
        response = await model.generate_content_async(prompt_template)
        response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        gemini_data = json.loads(response_text)
        suggested_items = [SuggestedItem(**item) for item in gemini_data.get("suggested_items", [])]

        combo_pieces = []

        # 2. Adım: Her bir öneri için product-service'i ara
        async with httpx.AsyncClient() as client:
            for item_suggestion in suggested_items:
                search_query = f"{item_suggestion.description} {item_suggestion.item_type}"

                # ÖNEMLİ: Docker network'ü içinde servisler birbirleriyle servis adları üzerinden konuşur.
                # Bu yüzden localhost:8002 yerine http://product-service:8000 kullanıyoruz.
                product_search_url = f"http://product_service:8000/search/?q={search_query}"

                print(f"Product service'e istek atılıyor: {product_search_url}")
                search_response = await client.get(product_search_url)

                matched_products = []
                if search_response.status_code == 200:
                    matched_products = search_response.json()

                combo_pieces.append(ComboPiece(
                    suggestion=item_suggestion,
                    matched_products=matched_products
                ))

        # 3. Adım: Zenginleştirilmiş sonucu döndür
        return FinalFashionResponse(
            explanation=gemini_data.get("explanation", ""),
            combo_pieces=combo_pieces
        )

    except Exception as e:
        print(f"API hatası: {e}")
        raise HTTPException(status_code=500, detail=f"AI asistanından cevap alınamadı. Hata: {str(e)}")