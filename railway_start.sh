#!/bin/bash
# Script para corrigir automaticamente o deploy do Railway

set -e

echo "🚀 Iniciando correção do deploy Railway..."
echo ""

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar se estamos no diretório correto
echo "📁 Verificando diretório..."
if [ ! -d "src/api/schemas" ]; then
    echo -e "${RED}❌ Erro: Diretório src/api/schemas não encontrado!${NC}"
    echo "Execute este script na raiz do projeto."
    exit 1
fi
echo -e "${GREEN}✅ Diretório correto${NC}"
echo ""

# 2. Backup dos arquivos que serão modificados
echo "💾 Criando backups..."
mkdir -p .railway_backup
cp -r src/api/schemas .railway_backup/
cp -r src/utils/logKit .railway_backup/ 2>/dev/null || true
echo -e "${GREEN}✅ Backups criados em .railway_backup/${NC}"
echo ""

# 3. Remover get_logger de todos os schemas
echo "🔧 Removendo loggers dos schemas..."

# Encontrar todos os arquivos de schema com get_logger
SCHEMA_FILES=$(find src/api/schemas -name "*.py" -exec grep -l "get_logger" {} \; 2>/dev/null || true)

if [ -z "$SCHEMA_FILES" ]; then
    echo -e "${GREEN}✅ Nenhum schema com logger encontrado${NC}"
else
    echo -e "${YELLOW}Arquivos com logger encontrados:${NC}"
    echo "$SCHEMA_FILES"
    echo ""

    for file in $SCHEMA_FILES; do
        echo "  Corrigindo: $file"

        # Remover import do get_logger
        sed -i.bak '/from src\.utils\.logKit import get_logger/d' "$file"
        sed -i.bak '/from src\.utils\.logKit\.config_logging import get_logger/d' "$file"

        # Remover declaração do logger
        sed -i.bak '/^logger = get_logger/d' "$file"

        # Remover usos do logger
        sed -i.bak '/logger\./d' "$file"

        # Remover arquivos de backup
        rm -f "$file.bak"

        echo -e "  ${GREEN}✅ Corrigido${NC}"
    done
fi
echo ""

# 4. Verificar se há outros arquivos problemáticos
echo "🔍 Procurando outros arquivos com logger em lugares inadequados..."

# Verificar models
MODEL_LOGGERS=$(find src/models -name "*.py" -exec grep -l "get_logger" {} \; 2>/dev/null || true)
if [ ! -z "$MODEL_LOGGERS" ]; then
    echo -e "${YELLOW}⚠️  Aviso: Loggers encontrados em models:${NC}"
    echo "$MODEL_LOGGERS"
    echo "Considere remover manualmente."
    echo ""
fi

# Verificar database models
DB_LOGGERS=$(grep -l "get_logger" src/database/models.py 2>/dev/null || true)
if [ ! -z "$DB_LOGGERS" ]; then
    echo -e "${YELLOW}⚠️  Aviso: Logger encontrado em database/models.py${NC}"
    echo "Considere remover manualmente."
    echo ""
fi

# 5. Testar imports
echo "🧪 Testando imports..."
if python3 -c "from src.api.schemas.produto_schema import ProdutoCreated; print('Import OK')" 2>/dev/null; then
    echo -e "${GREEN}✅ Imports funcionando corretamente${NC}"
else
    echo -e "${RED}❌ Erro nos imports. Verifique manualmente.${NC}"
    exit 1
fi
echo ""

# 6. Listar alterações
echo "📋 Resumo das alterações:"
git diff --name-only 2>/dev/null || echo "Git não inicializado"
echo ""

# 7. Instruções finais
echo "📝 Próximos passos:"
echo ""
echo "1️⃣  Revise as alterações:"
echo "   git diff src/api/schemas/"
echo ""
echo "2️⃣  Se tudo estiver correto, faça commit:"
echo "   git add ."
echo "   git commit -m 'fix: Remove loggers from schemas for Railway deploy'"
echo ""
echo "3️⃣  Faça push para o Railway:"
echo "   git push origin main"
echo ""
echo "4️⃣  Monitore os logs:"
echo "   railway logs"
echo ""
echo -e "${GREEN}✅ Script concluído com sucesso!${NC}"
echo ""
echo "💡 Dica: Se precisar reverter, os backups estão em .railway_backup/"