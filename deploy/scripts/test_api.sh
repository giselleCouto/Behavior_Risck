#!/bin/bash
# Script de Teste da API - Behavior Score KAB

set -e

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

API_URL="http://localhost:8000"

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "🧪 Testando API do Behavior Score..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Teste 1: Root endpoint
echo ""
echo "Teste 1: Root endpoint"
if curl -s "${API_URL}/" | grep -q "Behavior Score KAB"; then
    print_success "Root endpoint OK"
else
    print_error "Root endpoint falhou"
    exit 1
fi

# Teste 2: Health check
echo ""
echo "Teste 2: Health check"
HEALTH=$(curl -s "${API_URL}/health")
if echo "$HEALTH" | grep -q "healthy"; then
    print_success "Health check OK"
    echo "$HEALTH" | jq '.'
else
    print_error "Health check falhou"
    echo "$HEALTH"
    exit 1
fi

# Teste 3: Model info
echo ""
echo "Teste 3: Model info"
if curl -s "${API_URL}/model/info" | grep -q "Random Forest"; then
    print_success "Model info OK"
else
    print_error "Model info falhou"
fi

# Teste 4: Expected features
echo ""
echo "Teste 4: Expected features"
if curl -s "${API_URL}/model/features" | grep -q "required_features"; then
    print_success "Expected features OK"
else
    print_error "Expected features falhou"
fi

# Teste 5: Predição individual
echo ""
echo "Teste 5: Predição individual"
PREDICTION=$(curl -s -X POST "${API_URL}/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "cpf_cnpj": "12345678900",
    "idade": 35,
    "renda_valida_new": 3000.0,
    "tempo_relacionamento_kredilig_meses": 24,
    "qtd_contratos": 5,
    "qtd_contratos_nr": 4,
    "dias_maior_atraso": 15,
    "dias_maior_atraso_aberto": 0,
    "valor_pago_nr": 5000.0,
    "valor_principal_total_nr": 8000.0,
    "indice_instabilidade": 12.5,
    "indice_regularidade": 0.85,
    "reneg_vs_liq_ratio_ponderado": 0.2
  }')

if echo "$PREDICTION" | grep -q "score"; then
    print_success "Predição individual OK"
    echo "$PREDICTION" | jq '.'
else
    print_error "Predição individual falhou"
    echo "$PREDICTION"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Todos os testes foram concluídos!"

