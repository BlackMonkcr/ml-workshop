#!/bin/bash
"""
SCRIPT DE TEST RÁPIDO - Sin modelos pesados
"""

# Configuración conservadora
export MAX_WORKERS=16
export OMP_NUM_THREADS=2
export NUMBA_NUM_THREADS=2

echo "🧪 TEST RÁPIDO - Sin modelos pesados"
echo "   📊 MAX_WORKERS: $MAX_WORKERS"
echo "   🔧 OMP_NUM_THREADS: $OMP_NUM_THREADS"
echo ""

# Verificar archivo
if [ ! -f "spanish_songs.pickle" ]; then
    echo "❌ Falta spanish_songs.pickle"
    exit 1
fi

echo "🚀 Iniciando test rápido..."
python3 quick_test.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ TEST EXITOSO"
    echo "   Sistema listo para processing completo"
    echo "   Próximo paso: ejecutar ./server_48_cores.sh"
else
    echo "❌ TEST FALLÓ"
    exit 1
fi
