#!/bin/bash
# Script de Deploy Automatizado - Behavior Score KAB
# Uso: ./deploy.sh [desenvolvimento|producao]

set -e  # Encerra em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir mensagens
print_msg() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

# Verifica ambiente
AMBIENTE=${1:-desenvolvimento}

print_msg "🚀 Iniciando deploy do Behavior Score KAB..."
print_msg "📦 Ambiente: $AMBIENTE"

# Verifica se Docker está instalado
if ! command -v docker &> /dev/null; then
    print_error "Docker não está instalado!"
    exit 1
fi

# Verifica se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose não está instalado!"
    exit 1
fi

# Navega para o diretório deploy
cd "$(dirname "$0")/.."

# Verifica se arquivo .env existe
if [ ! -f .env ]; then
    print_warning "Arquivo .env não encontrado. Criando a partir de env.example..."
    cp env.example .env
fi

# Verifica se modelos existem
if [ ! -d "../Modelos" ]; then
    print_error "Pasta de modelos não encontrada em ../Modelos"
    exit 1
fi

# Para containers existentes
print_msg "⏹️  Parando containers existentes..."
docker-compose down

# Limpa imagens antigas (apenas em produção)
if [ "$AMBIENTE" == "producao" ]; then
    print_msg "🧹 Limpando imagens antigas..."
    docker system prune -f
fi

# Build das imagens
print_msg "🔨 Construindo imagens Docker..."
if [ "$AMBIENTE" == "producao" ]; then
    docker-compose --profile with-nginx build --no-cache
else
    docker-compose build
fi

# Inicia containers
print_msg "▶️  Iniciando containers..."
if [ "$AMBIENTE" == "producao" ]; then
    docker-compose --profile with-nginx up -d
else
    docker-compose up -d
fi

# Aguarda containers ficarem saudáveis
print_msg "⏳ Aguardando containers iniciarem..."
sleep 20

# Verifica status
print_msg "📊 Status dos containers:"
docker-compose ps

# Testa API
print_msg "🧪 Testando API..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_msg "✅ API está respondendo!"
else
    print_error "❌ API não está respondendo corretamente"
    print_msg "Verificando logs..."
    docker-compose logs --tail=50 api
    exit 1
fi

# Testa Dashboard (apenas verifica se está rodando)
print_msg "🧪 Testando Dashboard..."
if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    print_msg "✅ Dashboard está respondendo!"
else
    print_warning "⚠️  Dashboard pode estar iniciando ainda..."
fi

# Exibe URLs de acesso
print_msg ""
print_msg "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_msg "✅ Deploy concluído com sucesso!"
print_msg "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_msg ""
print_msg "🔗 URLs de Acesso:"
print_msg "   API:          http://localhost:8000"
print_msg "   API Docs:     http://localhost:8000/docs"
print_msg "   Dashboard:    http://localhost:8501"

if [ "$AMBIENTE" == "producao" ]; then
    print_msg "   Nginx:        http://localhost:80"
fi

print_msg ""
print_msg "📋 Comandos úteis:"
print_msg "   Ver logs:     docker-compose logs -f"
print_msg "   Parar:        docker-compose down"
print_msg "   Reiniciar:    docker-compose restart"
print_msg ""

