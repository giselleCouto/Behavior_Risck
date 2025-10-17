# 🐳 Deploy Docker - Behavior Score KAB

Sistema completo de deploy em produção para o modelo de Credit Scoring Behavior Score KAB.

---

## 📋 O que está incluído?

Este diretório contém **tudo** que você precisa para colocar o modelo em produção:

### 🎯 Componentes Principais

1. **API REST (FastAPI)** - Serve o modelo via endpoints HTTP
2. **Dashboard (Streamlit)** - Interface web para análise e visualização
3. **Nginx (Opcional)** - Reverse proxy e load balancer

### 📂 Estrutura

```
deploy/
├── api/                    # API FastAPI
│   ├── app.py             # Aplicação principal
│   ├── model_service.py   # Lógica do modelo
│   ├── schemas.py         # Validação de dados
│   ├── Dockerfile         # Container da API
│   └── requirements.txt   # Dependências
│
├── dashboard/             # Dashboard Streamlit
│   ├── Dash.py           # Aplicação Streamlit
│   ├── Dockerfile        # Container do Dashboard
│   └── requirements.txt  # Dependências
│
├── nginx/                # Reverse Proxy
│   └── nginx.conf       # Configuração Nginx
│
├── scripts/              # Scripts de automação
│   ├── deploy.sh        # Deploy Linux/macOS
│   ├── deploy.ps1       # Deploy Windows
│   ├── backup.sh        # Backup de modelos
│   ├── test_api.sh      # Testes da API
│   └── test_api.ps1     # Testes Windows
│
├── examples/             # Exemplos de integração
│   ├── python_client.py # Cliente Python
│   └── README.md        # Documentação exemplos
│
├── docker-compose.yml    # Orquestração dos serviços
├── env.example          # Template de variáveis
├── QUICKSTART.md        # Guia rápido (5 min)
└── README_DEPLOY.md     # Documentação completa
```

---

## 🚀 Início Rápido

### Opção 1: Quickstart (5 minutos)

Para colocar tudo rodando rapidamente:

📖 **[Siga o Quickstart Guide](QUICKSTART.md)**

### Opção 2: Documentação Completa

Para entender todos os detalhes e configurações avançadas:

📖 **[Leia a Documentação Completa](README_DEPLOY.md)**

---

## ⚡ Deploy em 3 Comandos

```bash
# 1. Entrar na pasta deploy
cd deploy

# 2. Configurar ambiente (apenas primeira vez)
cp env.example .env

# 3. Iniciar tudo
docker-compose up -d --build
```

Aguarde ~30 segundos e acesse:
- **API**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

---

## 📊 Arquitetura

```
┌─────────────────┐
│   Cliente Web   │
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌─────────────────┐
│  API:8000       │  │ Dashboard:8501  │
│  (FastAPI)      │  │ (Streamlit)     │
└────────┬────────┘  └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Modelos ML     │
│  (Pickles/NPY)  │
└─────────────────┘
```

---

## 🎯 Casos de Uso

### 1. Desenvolvimento Local

```bash
docker-compose up -d
# Acesse: http://localhost:8000 e http://localhost:8501
```

### 2. Produção com Nginx

```bash
docker-compose --profile with-nginx up -d
# Acesse: http://seu-dominio.com
```

### 3. Integração com Sistemas

Use o cliente Python:

```python
from examples.python_client import BehaviorScoreClient

client = BehaviorScoreClient()
resultado = client.predict({
    "cpf_cnpj": "12345678900",
    "idade": 35,
    "renda_valida_new": 3000.0,
    # ... outros campos
})

print(f"Score: {resultado['score']}")
print(f"Decisão: {resultado['decisao']}")
```

---

## 🛠️ Comandos Úteis

```bash
# Ver status
docker-compose ps

# Ver logs
docker-compose logs -f

# Parar tudo
docker-compose down

# Reiniciar
docker-compose restart

# Rebuild
docker-compose up -d --build

# Testar API
curl http://localhost:8000/health
```

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| [QUICKSTART.md](QUICKSTART.md) | Guia rápido para começar |
| [README_DEPLOY.md](README_DEPLOY.md) | Documentação completa |
| [examples/README.md](examples/README.md) | Exemplos de integração |

---

## 🔧 Configuração

### Variáveis de Ambiente

Edite `.env`:

```bash
# Portas
API_PORT=8000
DASHBOARD_PORT=8501

# Configurações
LOG_LEVEL=info
API_WORKERS=2
```

### Segurança (Produção)

- ✅ Configure autenticação na API
- ✅ Use HTTPS com certificados SSL
- ✅ Configure rate limiting
- ✅ Use secrets management
- ✅ Configure firewall

Veja detalhes em [README_DEPLOY.md](README_DEPLOY.md#-segurança)

---

## 🧪 Testes

### Testar API

**Linux/macOS:**
```bash
./scripts/test_api.sh
```

**Windows:**
```powershell
.\scripts\test_api.ps1
```

### Testar Manualmente

```bash
# Health check
curl http://localhost:8000/health

# Predição
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"cpf_cnpj":"12345678900","idade":35,...}'
```

---

## 📊 Monitoramento

### Health Checks

```bash
# API
curl http://localhost:8000/health

# Dashboard
curl http://localhost:8501/_stcore/health
```

### Logs

```bash
# Todos os serviços
docker-compose logs -f

# Apenas API
docker-compose logs -f api

# Últimas 100 linhas
docker-compose logs --tail=100
```

### Métricas

Os containers incluem health checks automáticos. Verifique:

```bash
docker ps
# A coluna STATUS mostra "healthy" se tudo estiver OK
```

---

## ❓ Problemas Comuns

| Problema | Solução |
|----------|---------|
| Porta em uso | Mude `API_PORT` e `DASHBOARD_PORT` no `.env` |
| Modelos não encontrados | Verifique pasta `../Modelos/` |
| Container não inicia | `docker-compose logs -f <serviço>` |
| API lenta | Aumente `API_WORKERS` no `.env` |
| Sem memória | Aumente recursos no Docker Desktop |

Veja mais em [README_DEPLOY.md](README_DEPLOY.md#-troubleshooting)

---

## 🔄 Backup

```bash
# Linux/macOS
./scripts/backup.sh

# Windows
# Use ferramenta de backup do Windows ou copie manualmente:
# - ../Modelos/
# - ../POLÍTICAS_BEHAVIOR.xlsx
# - .env
```

---

## 🤝 Suporte

**Responsável:** Fernando J.M.  
**Email:** fernando.monteiro@bhs.com.br

---

## 📝 Versão

**v1.0.0** - Deploy inicial completo

- ✅ API FastAPI com predições
- ✅ Dashboard Streamlit
- ✅ Docker Compose
- ✅ Scripts de automação
- ✅ Documentação completa
- ✅ Exemplos de integração

---

## 📄 Licença

Projeto proprietário - Behavior Score KAB  
© 2025 - Todos os direitos reservados

