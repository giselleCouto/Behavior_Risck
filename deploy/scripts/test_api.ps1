# Script de Teste da API para Windows - Behavior Score KAB

$API_URL = "http://localhost:8000"

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Failure {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

Write-Host "🧪 Testando API do Behavior Score..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Teste 1: Root endpoint
Write-Host ""
Write-Host "Teste 1: Root endpoint"
try {
    $response = Invoke-RestMethod -Uri "$API_URL/" -Method Get
    if ($response.message -match "Behavior Score KAB") {
        Write-Success "Root endpoint OK"
    } else {
        Write-Failure "Root endpoint falhou"
        exit 1
    }
} catch {
    Write-Failure "Erro ao acessar root endpoint: $_"
    exit 1
}

# Teste 2: Health check
Write-Host ""
Write-Host "Teste 2: Health check"
try {
    $response = Invoke-RestMethod -Uri "$API_URL/health" -Method Get
    if ($response.status -eq "healthy") {
        Write-Success "Health check OK"
        $response | ConvertTo-Json -Depth 10
    } else {
        Write-Failure "Health check falhou"
        exit 1
    }
} catch {
    Write-Failure "Erro no health check: $_"
    exit 1
}

# Teste 3: Model info
Write-Host ""
Write-Host "Teste 3: Model info"
try {
    $response = Invoke-RestMethod -Uri "$API_URL/model/info" -Method Get
    if ($response.model_type -match "Random Forest") {
        Write-Success "Model info OK"
    } else {
        Write-Failure "Model info falhou"
    }
} catch {
    Write-Failure "Erro ao obter model info: $_"
}

# Teste 4: Expected features
Write-Host ""
Write-Host "Teste 4: Expected features"
try {
    $response = Invoke-RestMethod -Uri "$API_URL/model/features" -Method Get
    if ($response.required_features) {
        Write-Success "Expected features OK"
    } else {
        Write-Failure "Expected features falhou"
    }
} catch {
    Write-Failure "Erro ao obter features: $_"
}

# Teste 5: Predição individual
Write-Host ""
Write-Host "Teste 5: Predição individual"
try {
    $headers = @{
        "Content-Type" = "application/json"
    }
    
    $body = @{
        cpf_cnpj = "12345678900"
        idade = 35
        renda_valida_new = 3000.0
        tempo_relacionamento_kredilig_meses = 24
        qtd_contratos = 5
        qtd_contratos_nr = 4
        dias_maior_atraso = 15
        dias_maior_atraso_aberto = 0
        valor_pago_nr = 5000.0
        valor_principal_total_nr = 8000.0
        indice_instabilidade = 12.5
        indice_regularidade = 0.85
        reneg_vs_liq_ratio_ponderado = 0.2
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$API_URL/predict" -Method Post -Headers $headers -Body $body
    
    if ($response.score) {
        Write-Success "Predição individual OK"
        $response | ConvertTo-Json -Depth 10
    } else {
        Write-Failure "Predição individual falhou"
    }
} catch {
    Write-Failure "Erro na predição: $_"
    Write-Host $_.Exception.Response
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "✅ Todos os testes foram concluídos!" -ForegroundColor Green

