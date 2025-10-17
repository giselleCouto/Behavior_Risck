#!/bin/bash
# Script de Backup - Behavior Score KAB
# Realiza backup dos modelos e configurações

set -e

# Cores
GREEN='\033[0;32m'
NC='\033[0m'

print_msg() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Configurações
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/${DATE}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

print_msg "📦 Criando backup do Behavior Score KAB..."

# Cria diretório de backup
mkdir -p "${BACKUP_DIR}"

# Backup dos modelos
print_msg "Copiando modelos..."
if [ -d "${PROJECT_ROOT}/Modelos" ]; then
    cp -r "${PROJECT_ROOT}/Modelos" "${BACKUP_DIR}/"
else
    print_msg "⚠️  Pasta de modelos não encontrada"
fi

# Backup das políticas
print_msg "Copiando políticas..."
if [ -f "${PROJECT_ROOT}/POLÍTICAS_BEHAVIOR.xlsx" ]; then
    cp "${PROJECT_ROOT}/POLÍTICAS_BEHAVIOR.xlsx" "${BACKUP_DIR}/"
fi

# Backup das configurações
print_msg "Copiando configurações..."
if [ -f "${SCRIPT_DIR}/../.env" ]; then
    cp "${SCRIPT_DIR}/../.env" "${BACKUP_DIR}/"
fi

# Backup do docker-compose
if [ -f "${SCRIPT_DIR}/../docker-compose.yml" ]; then
    cp "${SCRIPT_DIR}/../docker-compose.yml" "${BACKUP_DIR}/"
fi

# Compacta backup
print_msg "Compactando backup..."
tar -czf "${BACKUP_DIR}.tar.gz" -C "backups" "${DATE}"

# Remove diretório temporário
rm -rf "${BACKUP_DIR}"

# Estatísticas
SIZE=$(du -h "${BACKUP_DIR}.tar.gz" | cut -f1)

print_msg "✅ Backup concluído!"
print_msg "   Arquivo: ${BACKUP_DIR}.tar.gz"
print_msg "   Tamanho: ${SIZE}"

# Limpa backups antigos (mantém últimos 5)
print_msg "Limpando backups antigos..."
ls -t backups/*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm --

print_msg "✅ Processo de backup finalizado!"

