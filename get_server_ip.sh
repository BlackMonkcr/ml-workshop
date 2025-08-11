#!/bin/bash
# get_server_ip.sh
# Script para obtener todas las IPs del servidor

echo "🌐 INFORMACIÓN DE RED DEL SERVIDOR"
echo "=================================="

echo "📍 IP Pública (externa):"
# Método 1: usando curl
curl -s https://api.ipify.org
echo ""

# Método 2: alternativo
echo "📍 IP Pública (alternativa):"
curl -s https://ifconfig.me
echo ""

echo ""
echo "📍 IPs Locales (internas):"
# En Linux
if command -v ip &> /dev/null; then
    ip addr show | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}' | cut -d'/' -f1
elif command -v ifconfig &> /dev/null; then
    # En macOS/BSD
    ifconfig | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}'
fi

echo ""
echo "📍 Nombre del servidor:"
hostname

echo ""
echo "📍 Información completa de red:"
if command -v ip &> /dev/null; then
    ip route get 8.8.8.8 | head -1 | awk '{print "Gateway:", $3, "Interface:", $5, "Source IP:", $7}'
fi

echo ""
echo "🔧 Para MongoDB Atlas, necesitas la IP PÚBLICA (externa)"
