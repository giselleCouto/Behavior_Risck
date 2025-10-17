# 🚀 Quickstart - Behavior Score KAB

Guia rápido para colocar o modelo em produção em **5 minutos**.

---

## 📋 Pré-requisitos

Instale Docker e Docker Compose:

### Windows
1. Baixe e instale [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Reinicie o computador
3. Verifique: `docker --version` e `docker-compose --version`

### Linux (Ubuntu/Debian)
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### macOS
1. Baixe e instale [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. Verifique: `docker --version` e `docker-compose --version`

---

## ⚡ Deploy Rápido

### Opção 1: Usando Scripts (Recomendado)

#### Windows (PowerShell)
```powershell
cd deploy
.\scripts\deploy.ps1
```

#### Linux/macOS
```bash
cd deploy
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Opção 2: Manual

```bash
# 1. Navegar para a pasta deploy
cd deploy

# 2. Copiar configurações
cp env.example .env

# 3. Iniciar containers
docker-compose up -d --build

# 4. Verificar status
docker-compose ps

# 5. Verificar logs
docker-compose logs -f
```

---

## 🎯 Acessar os Serviços

Após ~30 segundos, acesse:

- **API**: http://localhost:8000
- **Documentação API**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

---

## 🧪 Testar a API

### 1. Health Check

**Navegador:**
```
http://localhost:8000/health
```

**Linha de comando:**
```bash
curl http://localhost:8000/health
```

### 2. Fazer uma Predição

**Windows (PowerShell):**
```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = @{
    cpf_cnpj = "12345678900"
    idade = 35
    renda_valida_new = 3000.0
    tempo_relacionamento_kredilig_meses = 24
    qtd_contratos = 5
    dias_maior_atraso = 15
    valor_pago_nr = 5000.0
    indice_instabilidade = 12.5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/predict" -Method Post -Headers $headers -Body $body
```

**Linux/macOS:**
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

**Resposta esperada:**
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

### 3. Usar a Documentação Interativa

Acesse: http://localhost:8000/docs

1. Clique em **POST /predict**
2. Clique em **Try it out**
3. Edite o JSON de exemplo
4. Clique em **Execute**

---

## 📊 Usar o Dashboard

1. Acesse: http://localhost:8501
2. Na aba **"carregar dados"**, faça upload dos arquivos:
   - Relatório de Behavior (CSV)
   - Arquivo Shap (Parquet)
   - Indicadores (XLSX)
3. Explore as outras abas:
   - **Análise Exploratória (EDA)** - Visualizações
   - **Relatório** - Consulta por CPF
   - **Indicadores** - Métricas temporais

---

## 🛠️ Comandos Úteis

### Ver logs em tempo real
```bash
docker-compose logs -f
```

### Ver logs de um serviço específico
```bash
docker-compose logs -f api
docker-compose logs -f dashboard
```

### Parar os serviços
```bash
docker-compose down
```

### Reiniciar os serviços
```bash
docker-compose restart
```

### Rebuild após mudanças
```bash
docker-compose up -d --build
```

### Ver status dos containers
```bash
docker-compose ps
```

---

## ❓ Problemas Comuns

### Porta já está em uso

**Erro:**
```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Solução:**
Edite `.env` e mude as portas:
```bash
API_PORT=8001
DASHBOARD_PORT=8502
```

### Modelos não encontrados

**Erro:**
```
FileNotFoundError: Modelo não encontrado
```

**Solução:**
Verifique se a pasta `Modelos/` está no caminho correto (um nível acima de `deploy/`)

### Container não inicia

**Solução:**
```bash
# Ver logs detalhados
docker-compose logs --tail=100 api

# Rebuild completo
docker-compose down
docker-compose up -d --build
```

### Sem memória suficiente

**Solução:**
No Docker Desktop: Settings → Resources → Aumentar Memory para 4GB+

---

## 📚 Próximos Passos

- 📖 Leia o [README_DEPLOY.md](README_DEPLOY.md) completo
- 🔒 Configure segurança (autenticação, HTTPS)
- 📊 Configure monitoramento (Prometheus, Grafana)
- 🧪 Execute testes: `./scripts/test_api.sh` (Linux/macOS)

---

## 🤝 Suporte

**Responsável:** Fernando J.M.  
**Email:** fernando.monteiro@bhs.com.br

Para mais informações, consulte a [documentação completa](README_DEPLOY.md).

