"""
Teste LOCAL das credenciais Azure OpenAI
"""
from openai import AsyncAzureOpenAI
import asyncio

async def test():
    print("🔑 Testando credenciais Azure OpenAI localmente...")
    print()
    
    # Credenciais
    api_key = "932843a5e242442a98f4a26fc634f218"
    endpoint = "https://eastus.api.cognitive.microsoft.com/"
    deployment = "gpt-4o-mini"
    api_version = "2024-02-15-preview"
    
    print(f"Endpoint: {endpoint}")
    print(f"Deployment: {deployment}")
    print(f"API Version: {api_version}")
    print()
    
    try:
        client = AsyncAzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        
        print("📞 Chamando Azure OpenAI...")
        response = await client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "user", "content": "Olá, responda apenas 'OK' se você me entendeu"}
            ],
            max_tokens=10
        )
        
        content = response.choices[0].message.content
        print(f"✅ SUCESSO! Resposta: {content}")
        print()
        print("🎉 As credenciais estão corretas!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        print()
        print("Detalhes do erro:")
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensagem: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    exit(0 if result else 1)
