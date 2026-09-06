import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("Set GOOGLE_API_KEY (or GEMINI_API_KEY) in .env before testing Gemini.")
client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="สวัสดีครับ! ทดสอบการเชื่อมต่อ Gemini API"
)

print(response.text)
