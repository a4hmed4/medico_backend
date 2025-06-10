from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import requests

app = FastAPI()

# السماح للـ Flutter بالوصول
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = "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"  # حط مفتاحك هنا

class ChatRequest(BaseModel):
    message: str

@app.post("/analyze-xray/")
async def analyze_xray(image: UploadFile = File(...)):
    image_data = await image.read()
    base64_image = base64.b64encode(image_data).decode('utf-8')

    prompt = """
You are a medical AI assistant. Analyze this X-ray image and reply only in this JSON format:
{
  "report": "Detailed medical report (at least 5 lines).",
  "diagnosis": "Short diagnosis of the condition.",
  "notes": "Important medical notes in 20 to 40 words.",
  "explanation": "Explainable AI insights about the detected disease."
}
    """

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        }
    )

    if response.status_code == 200:
        try:
            gemini_response = response.json()
            content = gemini_response['candidates'][0]['content']['parts'][0]['text']
            clean_json = content.replace('```json', '').replace('```', '').strip()
            return {"success": True, "result": clean_json}
        except Exception as e:
            return {"success": False, "error": "تحليل الصورة نجح ولكن فشل في قراءة النتيجة", "details": str(e)}
    else:
        return {"success": False, "error": "فشل الاتصال بـ Gemini", "status_code": response.status_code}

@app.post("/chat/")
def chat_with_patient(request: ChatRequest):
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": f"You are a medical assistant. Patient asked: {request.message}"}]}]
        }
    )

    if response.status_code == 200:
        reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return {"success": True, "reply": reply}
    else:
        return {"success": False, "error": "فشل الرد على الرسالة"}
