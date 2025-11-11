"""
Testa ExtractorFunction diretamente
"""
import requests
import json

URL = "https://promoagente-func.azurewebsites.net/api/extract"

payload = {
    "text": "Promoção progressiva Nivea janeiro a março"
}

print("🔍 Testando ExtractorFunction diretamente...")
print(f"📧 Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(URL, json=payload, timeout=60)
    
    print(f"📊 Status Code: {response.status_code}")
    print()
    print("📋 Response:")
    print(response.text)
    
except Exception as e:
    print(f"❌ Erro: {e}")
