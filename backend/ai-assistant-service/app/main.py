# ai-assistant-service/app/main.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import json
import httpx
from typing import List, Optional
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
    description: Optional[str] = None
    image_url: Optional[str] = None

# Eski Moda Asistanı için Modeller
class SuggestedItem(BaseModel):
    item_type: str
    description: str
    optional: bool = False

class ComboPiece(BaseModel):
    suggestion: SuggestedItem
    matched_products: List[MatchedProduct]

class FinalFashionResponse(BaseModel):
    explanation: str
    combo_pieces: List[ComboPiece]

class FashionPromptRequest(BaseModel):
    prompt: str

# YENİ Alışveriş Ajanı için Modeller
class AgentRequest(BaseModel):
    prompt: str
    budget: Optional[float] = None

class AgentSearchResult(BaseModel):
    category: str # Örn: "Gömlek"
    matched_products: List[MatchedProduct]

class AgentResponse(BaseModel):
    summary: str # Gemini'nin oluşturduğu özet
    results: List[AgentSearchResult]


# --- Endpoints ---

@app.post("/generate-fashion-combo", response_model=FinalFashionResponse)
async def generate_fashion_combo(request: FashionPromptRequest):
    # Bu fonksiyon aynı kalıyor...
    pass # Önceki mesajlardaki kodun aynısı

# YENİ ALIŞVERİŞ AJANI ENDPOINT'İ
@app.post("/shopping-agent", response_model=AgentResponse)
async def shopping_agent(request: AgentRequest):
    if not model:
        raise HTTPException(status_code=503, detail="AI model is not available.")

    # 1. Adım (Akıl Yürütme): Gemini'ye ne yapması gerektiğini sor.
    agent_prompt = f"""
    Bir e-ticaret sitesi için akıllı alışveriş ajanısın. Kullanıcının isteğini analiz et ve bu isteği yerine getirmek için hangi ürün kategorilerinde arama yapman gerektiğini belirle.
    Sonucu JSON formatında ver. JSON objesi şu alanları içermeli:
    "summary": Kullanıcının isteğini anladığını ve ne yapacağını özetleyen kısa bir metin.
    "search_terms": Arama yapılması gereken ürün kategorilerini veya anahtar kelimeleri içeren bir string listesi (en fazla 3 tane).

    Kullanıcı isteği: "{request.prompt}"
    """
    if request.budget:
        agent_prompt += f"\nKullanıcı bütçesi: {request.budget} TL"

    try:
        print(f"Ajan için Gemini'ye gönderilen prompt: {request.prompt}")
        response = await model.generate_content_async(agent_prompt)
        response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        plan_data = json.loads(response_text)

        search_terms = plan_data.get("search_terms", [])
        summary = plan_data.get("summary", "İsteğiniz anlaşıldı, ürünler aranıyor...")
        print(f"Gemini'nin oluşturduğu plan: Arama terimleri={search_terms}")

        # 2. Adım (Eyleme Geçme): Belirlenen terimlerle ürünleri ara.
        agent_search_results = []
        async with httpx.AsyncClient() as client:
            for term in search_terms:
                product_search_url = f"http://product_service:8000/search/?q={term}"
                print(f"Product service'e istek atılıyor: {product_search_url}")
                search_response = await client.get(product_search_url, timeout=30)

                matched_products = []
                if search_response.status_code == 200:
                    products_data = search_response.json()
                    # Bütçe varsa filtrele
                    if request.budget:
                        matched_products = [p for p in products_data if float(p.get('price', 0)) <= request.budget]
                    else:
                        matched_products = products_data

                agent_search_results.append(AgentSearchResult(
                    category=term.capitalize(),
                    matched_products=matched_products
                ))

        # 3. Adım (Sonuç Derleme): Nihai sonucu döndür.
        return AgentResponse(summary=summary, results=agent_search_results)

    except Exception as e:
        print(f"Ajan çalışırken hata oluştu: {e}")
        raise HTTPException(status_code=500, detail=f"Alışveriş ajanında bir hata oluştu: {str(e)}")

