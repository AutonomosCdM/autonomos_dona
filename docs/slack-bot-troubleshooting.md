# Guía de Troubleshooting para Bots de Slack

Esta guía documenta problemas comunes y soluciones rápidas para bots de Slack con Python Bolt.

## 🚨 Errores Críticos

### Error: 'Args' object has no attribute 'get'
```
AttributeError: 'Args' object has no attribute 'get'
```

**Solución:**
```python
# ❌ Incorrecto
event = args.get("event", {})

# ✅ Correcto  
event = getattr(args, 'event', None)
```

### Error: dispatch_failed
```
Unsuccessful Bolt execution result (status: 500, body: )
```

**Causas:**
- Middleware no llama `next()`
- Exception sin manejar
- Args object mal accedido

**Solución:**
```python
def middleware(args, next):
    try:
        # lógica aquí
        next()  # ¡CRITICAL!
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
```

## 📡 Problemas de Conexión

### Bot no responde
**Checklist:**
- [ ] Socket Mode habilitado
- [ ] Tokens correctos
- [ ] App instalada
- [ ] Handlers registrados

### missing_scope error
```
{'error': 'missing_scope', 'needed': 'channels:read'}
```

**Solución:**
1. Ir a api.slack.com
2. OAuth & Permissions
3. Agregar scope faltante
4. Reinstalar app

## ⚙️ Errores de Configuración

### Token inválido
- Verificar SLACK_BOT_TOKEN comienza con `xoxb-`
- Verificar SLACK_APP_TOKEN comienza con `xapp-`
- Regenerar tokens si es necesario

### Environment variables
```python
# .env
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_SIGNING_SECRET=...
```

## 🐛 Debug Tips

### Logs esenciales
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Test middleware
```python
def debug_middleware(args, next):
    print(f"Args attributes: {dir(args)}")
    print(f"Command: {getattr(args, 'command', None)}")
    next()
```

## 📝 Checklist Rápido

Antes de deployar:
- [ ] `getattr()` para Args objects
- [ ] `next()` en todos los middleware
- [ ] `ack()` en command handlers
- [ ] Error handling implementado
- [ ] Tests pasando

## 🔧 Comandos Útiles

```bash
# Ver logs en tiempo real
tail -f bot.log

# Matar proceso bot
pkill -f "python -m src.app"

# Restart bot
nohup python -m src.app > bot.log 2>&1 &
```

---
**Tip:** Siempre usa `getattr(args, 'attribute', default)` para acceder a Args objects.