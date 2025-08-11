#!/bin/bash
"""
SCRIPT DE LIMPIEZA DESPUÉS DE ERRORES DE MULTIPROCESSING
Usa DESPUÉS de fallos con múltiples workers descargando modelos
"""

echo "🧹 LIMPIEZA DE SERVIDOR DESPUÉS DE ERRORES"
echo "=========================================="

# Función para mostrar progreso
show_status() {
    echo "📊 Estado actual:"
    echo "   Procesos Python: $(ps aux | grep python | grep -v grep | wc -l)"
    echo "   Memoria libre: $(free -h | grep Mem | awk '{print $7}')"
    echo "   Espacio /tmp: $(df -h /tmp | tail -1 | awk '{print $4}')"
    echo ""
}

echo "🔍 Estado ANTES de limpieza:"
show_status

echo "1️⃣ Matando procesos Python colgados..."
sudo pkill -f "python.*server_optimized" 2>/dev/null || true
sudo pkill -f "transformers" 2>/dev/null || true
sudo pkill -f "torch" 2>/dev/null || true
killall python3 2>/dev/null || true
sleep 2

echo "2️⃣ Limpiando memoria y cache del sistema..."
sudo sync
sudo sysctl vm.drop_caches=3 >/dev/null 2>&1 || true
sleep 1

echo "3️⃣ Limpiando cache de HuggingFace (CRÍTICO)..."
rm -rf ~/.cache/huggingface/transformers/ 2>/dev/null || true
rm -rf ~/.cache/huggingface/hub/ 2>/dev/null || true
rm -rf ~/.cache/huggingface/datasets/ 2>/dev/null || true

# Crear nuevo directorio limpio
mkdir -p ~/.cache/huggingface/transformers/
export HF_HOME=/tmp/hf_cache_clean
mkdir -p $HF_HOME

echo "4️⃣ Limpiando archivos temporales..."
rm -rf /tmp/torch_* 2>/dev/null || true
rm -rf /tmp/transformers_* 2>/dev/null || true
rm -rf /tmp/.hf_* 2>/dev/null || true
rm -rf /tmp/pytorch_* 2>/dev/null || true

echo "5️⃣ Limpiando logs de errores..."
rm -f server_processing.log 2>/dev/null || true
rm -f *.log 2>/dev/null || true

sleep 2

echo "✅ Estado DESPUÉS de limpieza:"
show_status

# Verificaciones finales
echo "🔍 Verificaciones finales:"

PYTHON_PROCS=$(ps aux | grep python | grep -v grep | wc -l)
if [ $PYTHON_PROCS -eq 0 ]; then
    echo "   ✅ Sin procesos Python colgados"
else
    echo "   ⚠️  Aún hay $PYTHON_PROCS procesos Python"
    ps aux | grep python | grep -v grep | head -3
fi

if [ -d ~/.cache/huggingface/transformers/ ]; then
    CACHE_SIZE=$(du -sh ~/.cache/huggingface/ 2>/dev/null | cut -f1)
    echo "   📁 Cache HuggingFace: $CACHE_SIZE"
else
    echo "   ✅ Cache HuggingFace limpio"
fi

# Test rápido de memoria
FREE_GB=$(free -g | grep Mem | awk '{print $7}')
echo "   💾 Memoria libre: ${FREE_GB}GB"

if [ $FREE_GB -gt 100 ]; then
    echo "   ✅ Suficiente memoria disponible"
else
    echo "   ⚠️  Poca memoria libre ($FREE_GB GB)"
fi

echo ""
echo "🎯 RECOMENDACIONES POST-LIMPIEZA:"
echo "   1. Ejecuta primero: ./quick_test.sh"
echo "   2. Si funciona bien: ./server_48_cores.sh"
echo "   3. Monitorea: watch -n 2 'free -h'"
echo ""
echo "✅ Limpieza completada - Sistema listo"
