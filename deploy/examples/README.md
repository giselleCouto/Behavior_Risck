# Exemplos de Uso - API Behavior Score

Este diretório contém exemplos práticos de como integrar com a API do Behavior Score KAB.

## 📁 Arquivos

- `python_client.py` - Cliente Python completo com exemplos
- `requirements.txt` - Dependências necessárias

## 🚀 Como Usar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Garantir que a API está Rodando

```bash
cd ..
docker-compose ps

# Deve mostrar behavior_api como "Up"
```

### 3. Executar Exemplos

```bash
python python_client.py
```

## 📖 Exemplos Incluídos

### Exemplo 1: Predição Individual

Mostra como fazer uma predição para um único cliente.

```python
from python_client import BehaviorScoreClient

client = BehaviorScoreClient()

cliente = {
    "cpf_cnpj": "12345678900",
    "idade": 35,
    "renda_valida_new": 3000.0,
    "tempo_relacionamento_kredilig_meses": 24
}

resultado = client.predict(cliente)
print(f"Score: {resultado['score']}")
```

### Exemplo 2: Predição em Lote

Mostra como fazer múltiplas predições de uma vez.

```python
clientes = [cliente1, cliente2, cliente3]
resultado = client.predict_batch(clientes)
```

### Exemplo 3: Informações do Modelo

Obtém metadados sobre o modelo.

```python
info = client.get_model_info()
features = client.get_expected_features()
```

### Exemplo 4: Tratamento de Erros

Demonstra como lidar com erros da API.

```python
try:
    resultado = client.predict(dados)
except requests.exceptions.HTTPError as e:
    print(f"Erro: {e.response.status_code}")
```

## 🔧 Personalizando

### Mudar URL da API

```python
client = BehaviorScoreClient(base_url="http://seu-servidor:8000")
```

### Adicionar Autenticação

```python
client = BehaviorScoreClient(api_key="sua-chave-aqui")
```

## 📚 Outros Exemplos

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Predição
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"cpf_cnpj": "12345678900", "idade": 35, ...}'
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

async function predict(clientData) {
  const response = await axios.post(
    'http://localhost:8000/predict',
    clientData
  );
  return response.data;
}
```

### C#

```csharp
using System.Net.Http;

var client = new HttpClient();
var content = new StringContent(jsonData, Encoding.UTF8, "application/json");
var response = await client.PostAsync("http://localhost:8000/predict", content);
var result = await response.Content.ReadAsStringAsync();
```

## 🆘 Suporte

Para dúvidas, consulte a [documentação completa](../README_DEPLOY.md).

