"""
Teste Direto da ExportFunction
Testa a geração de Excel via API
"""
import requests
import json
from datetime import datetime

# URL da ExportFunction
EXPORT_URL = "https://promoagente-func.azurewebsites.net/api/export"

# Dados de teste de uma promoção completa
promo_data = {
    "titulo": "Combo Always - Teste",
    "mecanica": "combo",
    "descricao": "Combo especial de higiene feminina Always",
    "segmentacao": "Distribuidores de São Paulo",
    "periodo_inicio": "01/03/2026",
    "periodo_fim": "31/03/2026",
    "condicoes": "Compra mínima de 12 combos",
    "recompensas": "Desconto de 8%",
    "produtos": "Always Básico Seca 8un + Always Noturno 8un",
    "desconto_percentual": "8"
}

print("🧪 TESTE DIRETO DA EXPORTFUNCTION")
print("=" * 60)
print(f"📍 URL: {EXPORT_URL}")
print(f"📊 Dados da promoção:")
print(json.dumps(promo_data, indent=2, ensure_ascii=False))
print("=" * 60)

try:
    print("\n📤 Enviando requisição...")
    
    # Faz a requisição
    response = requests.post(
        EXPORT_URL,
        json={
            "promo_data": promo_data,
            "format": "excel"
        },
        timeout=30
    )
    
    print(f"\n📥 Status Code: {response.status_code}")
    print(f"📥 Headers: {dict(response.headers)}")
    
    # Verifica resposta
    if response.status_code == 200:
        print("\n✅ SUCESSO!")
        
        try:
            result = response.json()
            print(f"\n📄 Resposta JSON:")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:500])  # Primeiros 500 chars
            
            if result.get("success"):
                print(f"\n✅ Excel gerado com sucesso!")
                print(f"📁 Filename: {result.get('filename')}")
                
                if result.get("excel_base64"):
                    base64_len = len(result.get("excel_base64", ""))
                    print(f"📦 Tamanho do Base64: {base64_len} caracteres")
                    print(f"📦 Tamanho estimado do Excel: {base64_len * 3 // 4} bytes")
                    
                    # Salva arquivo para teste
                    import base64
                    from pathlib import Path
                    
                    excel_bytes = base64.b64decode(result["excel_base64"])
                    filename = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    
                    with open(filename, "wb") as f:
                        f.write(excel_bytes)
                    
                    print(f"\n💾 Excel salvo localmente: {filename}")
                    print(f"💾 Tamanho do arquivo: {len(excel_bytes)} bytes")
                    print(f"\n🎉 TESTE COMPLETO! Abra o arquivo para verificar.")
                else:
                    print("\n⚠️ Resposta não contém excel_base64")
            else:
                print(f"\n❌ Erro na resposta: {result.get('error', 'Erro desconhecido')}")
                
        except json.JSONDecodeError as e:
            print(f"\n❌ Erro ao decodificar JSON: {e}")
            print(f"📄 Resposta raw (primeiros 500 chars):")
            print(response.text[:500])
    
    elif response.status_code == 500:
        print("\n❌ ERRO 500 - Internal Server Error")
        print("📄 Resposta:")
        try:
            error_data = response.json()
            print(json.dumps(error_data, indent=2, ensure_ascii=False))
        except:
            print(response.text[:1000])
    
    else:
        print(f"\n❌ Erro {response.status_code}")
        print(f"📄 Resposta: {response.text[:500]}")

except requests.exceptions.RequestException as e:
    print(f"\n❌ Erro na requisição:")
    print(f"   {type(e).__name__}: {str(e)}")
    
except Exception as e:
    print(f"\n❌ Erro inesperado:")
    print(f"   {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("🏁 TESTE FINALIZADO")
print("=" * 60)
