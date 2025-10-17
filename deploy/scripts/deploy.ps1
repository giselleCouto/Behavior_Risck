# Script de Deploy para Windows - Behavior Score KAB
# Uso: .\deploy.ps1 [desenvolvimento|producao]

param(
    [string]$Ambiente = "desenvolvimento"
)

# Cores
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[ERRO] $Message" -ForegroundColor Red
}

function Write-WarningMsg {
    param([string]$Message)
    Write-Host "[AVISO] $Message" -ForegroundColor Yellow
}

Write-Info "🚀 Iniciando deploy do Behavior Score KAB..."
Write-Info "📦 Ambiente: $Ambiente"

# Verifica se Docker está instalado
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-ErrorMsg "Docker não está instalado!"
    exit 1
}

# Verifica se Docker Compose está instalado
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-ErrorMsg "Docker Compose não está instalado!"
    exit 1
}

# Navega para o diretório deploy
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $ScriptPath "..")

# Verifica se arquivo .env existe
if (-not (Test-Path ".env")) {
    Write-WarningMsg "Arquivo .env não encontrado. Criando a partir de env.example..."
    Copy-Item "env.example" ".env"
}

# Verifica se modelos existem
if (-not (Test-Path "..\Modelos")) {
    Write-ErrorMsg "Pasta de modelos não encontrada em ..\Modelos"
    exit 1
}

# Para containers existentes
Write-Info "⏹️  Parando containers existentes..."
docker-compose down

# Limpa imagens antigas (apenas em produção)
if ($Ambiente -eq "producao") {
    Write-Info "🧹 Limpando imagens antigas..."
    docker system prune -f
}

# Build das imagens
Write-Info "🔨 Construindo imagens Docker..."
if ($Ambiente -eq "producao") {
    docker-compose --profile with-nginx build --no-cache
} else {
    docker-compose build
}

# Inicia containers
Write-Info "▶️  Iniciando containers..."
if ($Ambiente -eq "producao") {
    docker-compose --profile with-nginx up -d
} else {
    docker-compose up -d
}

# Aguarda containers ficarem saudáveis
Write-Info "⏳ Aguardando containers iniciarem..."
Start-Sleep -Seconds 20

# Verifica status
Write-Info "📊 Status dos containers:"
docker-compose ps

# Testa API
Write-Info "🧪 Testando API..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Info "✅ API está respondendo!"
    }
} catch {
    Write-ErrorMsg "❌ API não está respondendo corretamente"
    Write-Info "Verificando logs..."
    docker-compose logs --tail=50 api
    exit 1
}

# Testa Dashboard
Write-Info "🧪 Testando Dashboard..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8501/_stcore/health" -Method Get -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Info "✅ Dashboard está respondendo!"
    }
} catch {
    Write-WarningMsg "⚠️  Dashboard pode estar iniciando ainda..."
}

# Exibe URLs de acesso
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "✅ Deploy concluído com sucesso!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Info "🔗 URLs de Acesso:"
Write-Host "   API:          http://localhost:8000"
Write-Host "   API Docs:     http://localhost:8000/docs"
Write-Host "   Dashboard:    http://localhost:8501"

if ($Ambiente -eq "producao") {
    Write-Host "   Nginx:        http://localhost:80"
}

Write-Host ""
Write-Info "📋 Comandos úteis:"
Write-Host "   Ver logs:     docker-compose logs -f"
Write-Host "   Parar:        docker-compose down"
Write-Host "   Reiniciar:    docker-compose restart"
Write-Host ""

