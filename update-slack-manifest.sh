#!/bin/bash

# Script to update Slack app manifest using slack-manifest CLI tool
# Usage: ./update-slack-manifest.sh <access_token>

if [ -z "$1" ]; then
    echo "❌ Error: Se requiere un access token"
    echo ""
    echo "📋 Uso: ./update-slack-manifest.sh <access_token>"
    echo ""
    echo "🔧 Para obtener el token:"
    echo "1. Ve a: https://api.slack.com/apps/A08MZ21R02D/oauth"
    echo "2. Copia el 'User OAuth Token' (empieza con xoxp-)"
    echo "3. O genera un 'App Configuration Token' desde:"
    echo "   https://api.slack.com/apps/A08MZ21R02D/general"
    echo ""
    exit 1
fi

ACCESS_TOKEN="$1"
APP_ID="A08MZ21R02D"

echo "🚀 Actualizando manifest de Slack app..."
echo "   App ID: $APP_ID"
echo "   Token: ${ACCESS_TOKEN:0:20}..."
echo ""

# Validate manifest first
echo "✅ Validando manifest..."
slack-manifest -v -m manifest.yml

if [ $? -eq 0 ]; then
    echo ""
    echo "🔄 Actualizando app..."
    slack-manifest -u -a "$APP_ID" -at "$ACCESS_TOKEN" -m manifest.yml
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ ¡Manifest actualizado exitosamente!"
        echo "🎉 Los slash commands ahora están configurados:"
        echo "   • /dona"
        echo "   • /dona-help"
        echo "   • /dona-task"
        echo "   • /dona-remind"
        echo "   • /dona-summary"
        echo "   • /dona-status"
        echo "   • /dona-config"
        echo "   • /dona-metrics"
        echo "   • /dona-limits"
        echo ""
        echo "🔗 Verifica en: https://api.slack.com/apps/A08MZ21R02D/slash-commands"
    else
        echo ""
        echo "❌ Error al actualizar el manifest"
        echo "💡 Verifica que el token tenga permisos de configuración"
    fi
else
    echo ""
    echo "❌ El manifest no es válido"
fi