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
origins = [
    "http://localhost:3000",
]
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

# Moda Asistanı için Modeller
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

# Alışveriş Ajanı için Modeller
class AgentRequest(BaseModel):
    prompt: str
    budget: Optional[float] = None

class AgentSearchResult(BaseModel):
    category: str
    matched_products: List[MatchedProduct]

class AgentResponse(BaseModel):
    summary: str
    results: List[AgentSearchResult]


# --- Endpoints ---

@app.post("/generate-fashion-combo", response_model=FinalFashionResponse)
async def generate_fashion_combo(request: FashionPromptRequest):
    if not model:
        raise HTTPException(status_code=503, detail="AI model is not available.")
    
    prompt_template = f"""
    Bir e-ticaret sitesi için moda asistanı olarak görev yapıyorsun.
    Kullanıcının isteğine göre bir kombin oluştur ve sonucu JSON formatında ver.
    JSON objesi şu alanları içermeli: "explanation" (bu kombini neden önerdiğini anlatan kısa bir metin) ve "suggested_items" (bir liste).
    Bu listedeki her bir obje de şu alanları içermeli: "item_type" (örneğin 'Gömlek', 'Pantolon'), "description" (ürünün kısa bir tanımı, örneğin 'Beyaz keten, uzun kollu') ve "optional" (bu parçanın opsiyonel olup olmadığı, true/false).
    En fazla 4 parça öner.
    Kullanıcı isteği: "{request.prompt}"
    """
    
    try:
        gemini_response = await model.generate_content_async(prompt_template)
        response_text = gemini_response.text.strip().replace("```json", "").replace("```", "").strip()
        gemini_data = json.loads(response_text)
        suggested_items = [SuggestedItem(**item) for item in gemini_data.get("suggested_items", [])]
        
        combo_pieces = []
        
        async with httpx.AsyncClient() as client:
            for item_suggestion in suggested_items:
                search_query = f"{item_suggestion.description} {item_suggestion.item_type}"
                product_search_url = f"http://product_service:8000/search/?q={search_query}"
                
                search_response = await client.get(product_search_url)
                
                matched_products = []
                if search_response.status_code == 200:
                    matched_products = search_response.json()

                combo_pieces.append(ComboPiece(
                    suggestion=item_suggestion,
                    matched_products=matched_products
                ))

        return FinalFashionResponse(
            explanation=gemini_data.get("explanation", ""),
            combo_pieces=combo_pieces
        )

    except Exception as e:
        print(f"API hatası: {e}")
        raise HTTPException(status_code=500, detail=f"AI asistanından cevap alınamadı. Hata: {str(e)}")


@app.post("/shopping-agent", response_model=AgentResponse)
async def shopping_agent(request: AgentRequest):
    if not model:
        raise HTTPException(status_code=503, detail="AI model is not available.")

    # 1. Adım (Akıl Yürütme): Gemini'den arama için kategori ve anahtar kelime üretmesini iste.
    agent_prompt = f"""
    Bir e-ticaret sitesi için akıllı alışveriş ajanısın. Kullanıcının isteğini analiz et.
    Sonucu JSON formatında ver. JSON objesi şu alanları içermeli:
    "summary": Kullanıcının isteğini anladığını ve ne yapacağını özetleyen kısa bir metin.
    "search_plan": Bir liste. Bu listedeki her bir obje de şu iki alanı içermeli:
        - "category": Ürün veritabanında filtrelenecek olan tek kelimelik kategori (Örn: "T-shirt", "Pants", "Jacket", "Shirt", "Dress").
        - "query": Ürün adı veya açıklamasında aranacak anahtar kelime.
    
    Kullanıcı isteği: "{request.prompt}"
    """
    if request.budget:
        agent_prompt += f"\nKullanıcı bütçesi: {request.budget} TL"

    try:
        print(f"Ajan için Gemini'ye gönderilen prompt: {request.prompt}")
        response = await model.generate_content_async(agent_prompt)
        response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        plan_data = json.loads(response_text)
        
        search_plan = plan_data.get("search_plan", [])
        summary = plan_data.get("summary", "İsteğiniz anlaşıldı, ürünler aranıyor...")
        print(f"Gemini'nin oluşturduğu plan: {search_plan}")

        # 2. Adım (Eyleme Geçme): Plana göre ürünleri ara.
        agent_search_results = []
        async with httpx.AsyncClient() as client:
            for plan_item in search_plan:
                category = plan_item.get("category")
                query = plan_item.get("query") # Sorguyu şimdilik kullanmasak da alalım

                if not category:
                    continue

                # --- DÜZELTME BURADA ---
                # Parametreleri bir sözlükte toplayalım
                search_params = {
                    "category": category
                    # "q" parametresini bilerek göndermiyoruz
                }
                # Eğer kullanıcı bir bütçe belirttiyse, onu da parametrelere ekleyelim
                if request.budget:
                    search_params["max_price"] = request.budget

                base_url = "http://product_service:8000/search/"

                print(f"Product service'e FİLTRELİ istek atılıyor: URL={base_url}, Parametreler={search_params}")

                # client.get'e params argümanını vererek isteği güvenli bir şekilde yapalım
                search_response = await client.get(base_url, params=search_params, timeout=30)
                # -------------------------

                matched_products = []
                if search_response.status_code == 200:
                    matched_products = search_response.json()
                else:
                    print(f"Product service'ten hata alındı: {search_response.status_code} - {search_response.text}")

                agent_search_results.append(AgentSearchResult(
                    category=category,
                    matched_products=matched_products
                ))

        return AgentResponse(summary=summary, results=agent_search_results)

    except Exception as e:
        print(f"Ajan çalışırken hata oluştu: {e}")
        raise HTTPException(status_code=500, detail=f"Alışveriş ajanında bir hata oluştu: {str(e)}")

    except Exception as e:
        print(f"Ajan çalışırken hata oluştu: {e}")
        raise HTTPException(status_code=500, detail=f"Alışveriş ajanında bir hata oluştu: {str(e)}")

    except Exception as e:
        print(f"Ajan çalışırken hata oluştu: {e}")
        raise HTTPException(status_code=500, detail=f"Alışveriş ajanında bir hata oluştu: {str(e)}")

