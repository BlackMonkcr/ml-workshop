#!/bin/bash
"""
SCRIPT PARA TRANSFERIR VERSIÓN LIMPIA AL SERVIDOR
Envía el archivo prepare_and_export_clean.py al servidor para procesamiento completo
"""

echo "🚀 TRANSFERENCIA DE SCRIPT LIMPIO AL SERVIDOR"
echo "=============================================="

# Archivos a transferir
FILES=(
    "prepare_and_export_clean.py"
    "mongodb_config.py"
    "mongodb_queries.py"
)

# Información del servidor
SERVER_USER="aaron.navarro"
SERVER_HOST="khipu.utec.edu.pe"
SERVER_PATH="~/ml-workshop/"

echo "📦 Archivos a transferir:"
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (no encontrado)"
        exit 1
    fi
done

echo ""
echo "🌐 Destino: $SERVER_USER@$SERVER_HOST:$SERVER_PATH"
echo ""

# Transferir archivos
echo "📤 Iniciando transferencia..."
for file in "${FILES[@]}"; do
    echo "   Enviando: $file"
    scp "$file" "$SERVER_USER@$SERVER_HOST:$SERVER_PATH"
    
    if [ $? -eq 0 ]; then
        echo "   ✅ $file transferido"
    else
        echo "   ❌ Error transferindo $file"
        exit 1
    fi
done

echo ""
echo "📋 INSTRUCCIONES PARA EL SERVIDOR:"
echo "=================================="
echo ""
echo "1. Conectar al servidor:"
echo "   ssh $SERVER_USER@$SERVER_HOST"
echo ""
echo "2. Navegar al directorio:"
echo "   cd ml-workshop"
echo ""
echo "3. Ejecutar limpieza completa + exportación:"
echo "   python3 prepare_and_export_clean.py"
echo ""
echo "4. Verificar resultados:"
echo "   python3 mongodb_queries.py"
echo ""
echo "🎯 VENTAJAS DE LA VERSIÓN LIMPIA:"
echo "- ✅ Eliminados 2,586 placeholders (canciones vacías)"
echo "- ✅ Limpiadas 23,139 letras con contenido HTML/navegación"
echo "- ✅ Dataset final: 23,705 canciones válidas"
echo "- ✅ Letras más limpias para análisis"
echo "- ✅ Exportación directa a MongoDB Atlas"
echo ""
echo "✅ Transferencia completada!"
echo "🌐 Listo para procesar en el servidor"
