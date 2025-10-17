# Deploy em Produção - Behavior Score KAB

## 📋 Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e Configuração](#instalação-e-configuração)
- [Deploy](#deploy)
- [Uso da API](#uso-da-api)
- [Monitoramento](#monitoramento)
- [Troubleshooting](#troubleshooting)
- [Segurança](#segurança)

---

## 🎯 Visão Geral

Este diretório contém toda a estrutura necessária para fazer o deploy em produção do modelo **Behavior Score KAB**, um sistema de predição de risco de crédito.

### Componentes

1. **API REST (FastAPI)** - Endpoint para predições do modelo
2. **Dashboard (Streamlit)** - Interface web para visualização e análise
3. **Nginx (Opcional)** - Reverse proxy para gerenciamento de tráfego

---

## 🏗️ Arquitetura

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐         ┌──────────────────┐
│  Nginx (80/443) │────────▶│  Dashboard:8501  │
└────────┬────────┘         └──────────────────┘
         │
         │
         ▼
┌─────────────────┐         ┌──────────────────┐
│   API:8000      │────────▶│  Modelos (ML)    │
└─────────────────┘         └──────────────────┘
```

---

## 📦 Pré-requisitos

### Software Necessário

- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **Git**: >= 2.30 (para controle de versão)

### Recursos Mínimos Recomendados

- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disco**: 20 GB de espaço livre
- **Sistema Operacional**: Linux (Ubuntu 20.04+), Windows Server 2019+, ou macOS

### Verificar Instalação

```bash
# Verificar Docker
docker --version

# Verificar Docker Compose
docker-compose --version

# Verificar permissões (Linux)
docker ps
```

---

## ⚙️ Instalação e Configuração

### 1. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e configure:

```bash
cd deploy
cp env.example .env
```

Edite o arquivo `.env` conforme necessário:

```bash
# Portas dos serviços
API_PORT=8000
DASHBOARD_PORT=8501

# Configurações de Log
LOG_LEVEL=info

# API Workers
API_WORKERS=2
```

### 2. Verificar Estrutura de Arquivos

Certifique-se de que os modelos estão na pasta correta:

```
Behavior_KAB-main/
├── deploy/              # Você está aqui
├── Modelos/
│   ├── Pré-Processamento/
│   │   ├── imputer_cat.pkl
│   │   ├── imputer_num.pkl
│   │   ├── scaler_num.pkl
│   │   └── ...
│   ├── fa_12.pkl (ou fa_11.pkl, fa_8.pkl)
│   ├── kmeans.pkl
│   ├── bins_SCR.npy
│   └── ...
└── POLÍTICAS_BEHAVIOR.xlsx
```

### 3. Estrutura do Diretório Deploy

```
deploy/
├── api/
│   ├── app.py                 # Aplicação FastAPI
│   ├── model_service.py       # Lógica de ML
│   ├── schemas.py             # Validação Pydantic
│   ├── requirements.txt       # Dependências
│   └── Dockerfile             # Imagem Docker
├── dashboard/
│   ├── Dash.py                # Aplicação Streamlit
│   ├── requirements.txt       # Dependências
│   └── Dockerfile             # Imagem Docker
├── nginx/
│   └── nginx.conf             # Configuração Nginx
├── docker-compose.yml         # Orquestração
├── env.example                # Template de variáveis
└── README_DEPLOY.md           # Este arquivo
```

---

## 🚀 Deploy

### Opção 1: Deploy Básico (API + Dashboard)

```bash
cd deploy
docker-compose up -d --build
```

### Opção 2: Deploy Completo (com Nginx)

```bash
cd deploy
docker-compose --profile with-nginx up -d --build
```

### Verificar Status dos Containers

```bash
docker-compose ps
```

Saída esperada:
```
NAME                  STATUS              PORTS
behavior_api          Up 2 minutes        0.0.0.0:8000->8000/tcp
behavior_dashboard    Up 2 minutes        0.0.0.0:8501->8501/tcp
behavior_nginx        Up 2 minutes        0.0.0.0:80->80/tcp
```

### Verificar Logs

```bash
# Logs de todos os serviços
docker-compose logs -f

# Logs apenas da API
docker-compose logs -f api

# Logs apenas do Dashboard
docker-compose logs -f dashboard
```

### Parar os Serviços

```bash
docker-compose down
```

### Rebuild Após Mudanças

```bash
docker-compose up -d --build
```

---

## 🔌 Uso da API

### Endpoints Disponíveis

#### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Resposta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-17T10:30:00",
  "model_loaded": true,
  "models_info": {
    "preprocessors_loaded": true,
    "models_loaded": true,
    "bins_loaded": true,
    "all_loaded": true
  }
}
```

#### 2. Predição Individual

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "cpf_cnpj": "12345678900",
    "idade": 35,
    "renda_valida_new": 3000.0,
    "tempo_relacionamento_kredilig_meses": 24,
    "qtd_contratos": 5,
    "dias_maior_atraso": 15,
    "valor_pago_nr": 5000.0,
    "indice_instabilidade": 12.5
  }'
```

**Resposta:**
```json
{
  "cpf_cnpj": "12345678900",
  "score": 750,
  "pd": 0.12,
  "faixa_risco": "MEDIO",
  "limite_sugerido": 15000.0,
  "decisao": "APROVAR",
  "motivo": "Cliente com risco MEDIO dentro dos parâmetros",
  "timestamp": "2025-10-17T10:30:00"
}
```

#### 3. Predição em Lote

```bash
curl -X POST "http://localhost:8000/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "clients": [
      {
        "cpf_cnpj": "12345678900",
        "idade": 35,
        "renda_valida_new": 3000.0,
        "tempo_relacionamento_kredilig_meses": 24
      },
      {
        "cpf_cnpj": "98765432100",
        "idade": 42,
        "renda_valida_new": 5000.0,
        "tempo_relacionamento_kredilig_meses": 36
      }
    ]
  }'
```

#### 4. Informações do Modelo

```bash
curl http://localhost:8000/model/info
```

#### 5. Features Esperadas

```bash
curl http://localhost:8000/model/features
```

### Documentação Interativa

Acesse a documentação Swagger em:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📊 Dashboard

### Acessar Dashboard

Abra no navegador:
```
http://localhost:8501
```

### Funcionalidades

1. **Carregar Dados** - Upload de arquivos CSV/Parquet
2. **Análise Exploratória (EDA)** - Visualizações interativas
3. **Relatórios** - Consulta por CPF
4. **Indicadores** - Métricas e séries temporais
5. **SHAP Values** - Explicabilidade do modelo

---

## 📈 Monitoramento

### Health Checks

Os containers possuem health checks automáticos:

```bash
# Verificar saúde dos containers
docker ps

# Inspecionar health check específico
docker inspect --format='{{json .State.Health}}' behavior_api
```

### Logs

```bash
# Logs em tempo real
docker-compose logs -f

# Últimas 100 linhas
docker-compose logs --tail=100

# Logs de um serviço específico
docker-compose logs -f api
```

### Métricas

Para monitoramento avançado, considere integrar:
- **Prometheus** - Coleta de métricas
- **Grafana** - Visualização de métricas
- **ELK Stack** - Centralização de logs

---

## 🛠️ Troubleshooting

### Problema: Container não inicia

**Verificar:**
```bash
docker-compose logs api
docker-compose logs dashboard
```

**Soluções:**
1. Verificar se as portas 8000 e 8501 estão livres
2. Verificar se os modelos estão no caminho correto
3. Rebuild dos containers: `docker-compose up -d --build`

### Problema: Erro ao carregar modelos

**Verificar:**
1. Pasta `Modelos/` existe no caminho correto
2. Arquivos .pkl e .npy estão presentes
3. Permissões de leitura nos arquivos

**Solução:**
```bash
# Verificar volumes montados
docker inspect behavior_api | grep Mounts -A 20

# Entrar no container para debug
docker exec -it behavior_api bash
ls -la /app/Modelos/
```

### Problema: API lenta

**Soluções:**
1. Aumentar workers da API no `.env`:
   ```
   API_WORKERS=4
   ```

2. Alocar mais recursos aos containers:
   ```yaml
   # Em docker-compose.yml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```

### Problema: Dashboard não carrega dados

**Verificar:**
1. Arquivo foi carregado corretamente
2. Formato do arquivo está correto (CSV, Parquet, XLSX)
3. Colunas necessárias estão presentes

### Logs de Erro Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| `Model not loaded` | Modelos não encontrados | Verificar path dos volumes |
| `Port already in use` | Porta ocupada | Mudar porta no .env |
| `Out of memory` | RAM insuficiente | Aumentar recursos ou reduzir batch size |
| `Connection refused` | Serviço não iniciado | Aguardar health check ou verificar logs |

---

## 🔒 Segurança

### Recomendações para Produção

#### 1. Autenticação

Adicione autenticação na API:

```python
# Em app.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Adicionar dependência nos endpoints
@app.post("/predict", dependencies=[Depends(get_api_key)])
```

#### 2. HTTPS

Configure certificados SSL no Nginx:

```bash
# Gerar certificado auto-assinado (desenvolvimento)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deploy/nginx/ssl/key.pem \
  -out deploy/nginx/ssl/cert.pem
```

#### 3. Rate Limiting

Adicione limitação de requisições:

```python
# Usando slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/predict")
@limiter.limit("10/minute")
async def predict(...):
    ...
```

#### 4. Variáveis Sensíveis

**NUNCA commite:**
- Arquivo `.env`
- Credenciais
- Chaves de API
- Certificados

Use secrets management como:
- **Docker Secrets**
- **AWS Secrets Manager**
- **Azure Key Vault**
- **HashiCorp Vault**

#### 5. Firewall

Configure firewall para expor apenas portas necessárias:

```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### 6. Updates

Mantenha imagens atualizadas:

```bash
# Atualizar imagens base
docker-compose pull
docker-compose up -d --build
```

---

## 📚 Recursos Adicionais

### Documentação

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)

### Scripts Úteis

#### Script de Backup

```bash
#!/bin/bash
# backup.sh - Backup dos modelos e configurações

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/${DATE}"

mkdir -p ${BACKUP_DIR}
cp -r ../Modelos ${BACKUP_DIR}/
cp ../POLÍTICAS_BEHAVIOR.xlsx ${BACKUP_DIR}/
cp .env ${BACKUP_DIR}/

tar -czf ${BACKUP_DIR}.tar.gz ${BACKUP_DIR}
rm -rf ${BACKUP_DIR}

echo "Backup criado: ${BACKUP_DIR}.tar.gz"
```

#### Script de Deploy

```bash
#!/bin/bash
# deploy.sh - Deploy automatizado

echo "🚀 Iniciando deploy..."

# Pull das últimas mudanças
git pull origin main

# Rebuild dos containers
docker-compose down
docker-compose up -d --build

# Aguardar health checks
echo "⏳ Aguardando containers..."
sleep 30

# Verificar status
docker-compose ps

# Testar API
curl -f http://localhost:8000/health || echo "❌ API não respondeu"

echo "✅ Deploy concluído!"
```

---

## 🤝 Suporte

Para questões e suporte:

**Responsável:** Fernando J.M.  
**Email:** fernando.monteiro@bhs.com.br

---

## 📝 Changelog

### v1.0.0 (2025-10-17)
- ✨ Implementação inicial da API FastAPI
- ✨ Containerização do Dashboard Streamlit
- ✨ Configuração Docker Compose
- ✨ Documentação completa de deploy
- ✨ Health checks e monitoramento básico

---

## 📄 Licença

Projeto proprietário - Behavior Score KAB  
© 2025 - Todos os direitos reservados

