# Guía Completa para Configurar Bots de Slack con Python Bolt

Esta guía documenta el proceso completo para configurar bots de Slack usando el framework Slack Bolt para Python, incluyendo todas las lecciones aprendidas durante el desarrollo de Autónomos Dona.

## 📋 Tabla de Contenidos

1. [Configuración Inicial de la App de Slack](#1-configuración-inicial-de-la-app-de-slack)
2. [Configuración del Proyecto Python](#2-configuración-del-proyecto-python)
3. [Estructura del Proyecto](#3-estructura-del-proyecto)
4. [Implementación de Middleware](#4-implementación-de-middleware)
5. [Handlers de Eventos y Comandos](#5-handlers-de-eventos-y-comandos)
6. [Integración con LLM](#6-integración-con-llm)
7. [Variables de Entorno](#7-variables-de-entorno)
8. [Troubleshooting Común](#8-troubleshooting-común)
9. [Testing](#9-testing)
10. [Deployment](#10-deployment)

---

## 1. Configuración Inicial de la App de Slack

### 1.1 Crear la App en Slack

1. Ve a [api.slack.com/apps](https://api.slack.com/apps)
2. Clic en "Create New App"
3. Selecciona "From an app manifest"
4. Pega el siguiente manifest (ajusta según tus necesidades):

```yaml
display_information:
  name: Tu Bot
  description: Descripción de tu bot
  background_color: "#2c3e50"
features:
  bot_user:
    display_name: Tu Bot
    always_online: true
  slash_commands:
    - command: /tu-comando
      description: Comando principal de tu bot
      usage_hint: "[mensaje]"
  shortcuts:
    - name: Ayuda
      type: global
      callback_id: help_shortcut
      description: Obtener ayuda
oauth_config:
  scopes:
    bot:
      - app_mentions:read
      - channels:history
      - channels:read
      - chat:write
      - commands
      - im:history
      - im:read
      - im:write
      - users:read
      - users:read.email
settings:
  event_subscriptions:
    bot_events:
      - app_mention
      - message.im
  interactivity:
    is_enabled: true
  socket_mode_enabled: true
  token_rotation_enabled: false
```

### 1.2 Obtener Tokens

Después de crear la app, obtén:

1. **Bot User OAuth Token** (`xoxb-...`) - de "OAuth & Permissions"
2. **Signing Secret** - de "Basic Information" > "App Credentials"
3. **App-Level Token** (`xapp-...`) - de "Basic Information" > "App-Level Tokens"
   - Debe tener el scope `connections:write`

### 1.3 Instalar la App

1. Ve a "Install App"
2. Clic en "Install to Workspace"
3. Autoriza los permisos

---

## 2. Configuración del Proyecto Python

### 2.1 Dependencias Básicas

Crea `requirements.txt`:

```txt
# Slack Bot Framework
slack-bolt==1.21.1
slack-sdk==3.31.0

# Web Framework Support
flask==3.0.3
gunicorn==22.0.0

# Environment Management
python-dotenv==1.0.1
pydantic==2.7.1
pydantic-settings==2.3.0

# Database (ejemplo con Supabase)
supabase==2.4.4
psycopg2-binary==2.9.9

# LLM Integration (ejemplo con Groq)
groq==0.8.0
requests==2.31.0

# Utilities
aiohttp==3.9.3
```

### 2.2 Estructura de Archivos

```
tu_bot/
├── src/
│   ├── __init__.py
│   ├── app.py                 # Punto de entrada principal
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── commands.py        # Manejadores de comandos slash
│   │   └── events.py          # Manejadores de eventos
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── logging_middleware.py
│   │   └── rate_limit_middleware.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── slack_client.py
│   │   ├── llm_service.py
│   │   └── database_client.py
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       └── logger.py
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

---

## 3. Implementación de Middleware

### 3.1 ⚠️ Problema Crítico: Args Object Access

**NUNCA hagas esto:**
```python
def bad_middleware(args, next):
    event = args.get("event", {})  # ❌ ERROR: 'Args' object has no attribute 'get'
    command = args["command"]      # ❌ ERROR: 'Args' object is not subscriptable
    args["context"]["key"] = value # ❌ ERROR: 'Args' object is not subscriptable
```

**SIEMPRE haz esto:**
```python
def correct_middleware(args, next):
    # ✅ CORRECTO: Usar getattr() para acceder a atributos
    event = getattr(args, 'event', None)
    command = getattr(args, 'command', None)
    context = getattr(args, 'context', {})
    
    # ✅ CORRECTO: Modificar context a través de la referencia
    context["key"] = value
    
    next()
```

### 3.2 Middleware de Logging

```python
# src/middleware/logging_middleware.py
import logging
import time
from typing import Dict, Any
from uuid import uuid4

logger = logging.getLogger(__name__)

def logging_middleware(args, next):
    """Middleware para logging de requests."""
    request_id = str(uuid4())
    
    # ✅ Acceso correcto a Args object
    command = getattr(args, 'command', None)
    event = getattr(args, 'event', None)
    context = getattr(args, 'context', {})
    
    # Determinar tipo de request
    if command:
        request_type = f"command:{command.get('command', 'unknown')}"
        user_id = command.get('user_id', 'unknown')
    elif event:
        request_type = f"event:{event.get('type', 'unknown')}"
        user_id = event.get('user', 'unknown')
    else:
        request_type = 'unknown'
        user_id = 'unknown'
    
    # Agregar request_id al contexto
    context['request_id'] = request_id
    
    start_time = time.time()
    
    try:
        logger.info(f"Request started: {request_id} - {request_type}")
        next()
        
        duration = int((time.time() - start_time) * 1000)
        logger.info(f"Request completed: {request_id} - {duration}ms")
        
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        logger.error(f"Request failed: {request_id} - {e} - {duration}ms")
        raise
```

### 3.3 Middleware de Rate Limiting

```python
# src/middleware/rate_limit_middleware.py
def rate_limit_middleware(args, next):
    """Middleware para rate limiting."""
    # ✅ Acceso correcto a Args object
    command = getattr(args, 'command', None)
    
    if not command:
        next()
        return
    
    user_id = command.get('user_id')
    
    # Implementar lógica de rate limiting
    if is_rate_limited(user_id):
        ack = getattr(args, 'ack', None)
        respond = getattr(args, 'respond', None)
        
        if ack:
            ack()
        if respond:
            respond("Rate limit exceeded. Please try again later.")
        return
    
    next()
```

---

## 4. Handlers de Eventos y Comandos

### 4.1 Handler de Comandos Slash

```python
# src/handlers/commands.py
from slack_bolt import App, Ack, Respond
from typing import Dict, Any

def register_command_handlers(app: App) -> None:
    """Registrar handlers de comandos."""
    app.command("/tu-comando")(handle_main_command)

def handle_main_command(ack: Ack, respond: Respond, command: Dict[str, Any], context: Dict[str, Any]) -> None:
    """Handler principal de comandos."""
    ack()  # Siempre acknowledges primero
    
    text = command.get("text", "").strip()
    user_id = command.get("user_id")
    
    if not text:
        respond("¡Hola! ¿En qué puedo ayudarte?")
        return
    
    # Procesar comando
    try:
        # Tu lógica aquí
        response = process_command(text, user_id)
        respond(response)
        
    except Exception as e:
        logger.error(f"Error processing command: {e}")
        respond("Ocurrió un error procesando tu solicitud.")
```

### 4.2 Handler de Eventos

```python
# src/handlers/events.py
from slack_bolt import BoltContext
from typing import Dict, Any

def register_event_handlers(app: App) -> None:
    """Registrar handlers de eventos."""
    app.event("app_mention")(handle_app_mention)
    app.event("message")(handle_message)

def handle_app_mention(event: Dict[str, Any], say: Any, context: BoltContext) -> None:
    """Handler para menciones del bot."""
    text = event.get("text", "")
    user = event.get("user")
    
    # Remover mención del bot del texto
    bot_mention = f"<@{context.get('bot_user_id')}>"
    clean_text = text.replace(bot_mention, "").strip()
    
    if not clean_text:
        say(f"¡Hola <@{user}>! ¿En qué puedo ayudarte?")
        return
    
    # Procesar mención
    response = process_mention(clean_text, user)
    say(f"<@{user}>, {response}")

def handle_message(event: Dict[str, Any], say: Any, context: BoltContext) -> None:
    """Handler para mensajes directos."""
    # Solo procesar DMs (channel_type == "im")
    if event.get("channel_type") != "im":
        return
    
    text = event.get("text", "")
    user = event.get("user")
    
    # Procesar mensaje directo
    response = process_direct_message(text, user)
    say(response)
```

---

## 5. Aplicación Principal

### 5.1 app.py

```python
# src/app.py
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from src.handlers.commands import register_command_handlers
from src.handlers.events import register_event_handlers
from src.middleware.logging_middleware import logging_middleware
from src.middleware.rate_limit_middleware import rate_limit_middleware
from src.utils.config import settings

logger = logging.getLogger(__name__)

def add_context_middleware(args, next):
    """Middleware para agregar contexto."""
    # ✅ Acceso correcto a Args object
    event = getattr(args, 'event', None)
    command = getattr(args, 'command', None)
    context = getattr(args, 'context', {})
    
    # Determinar si es privado/público
    is_private = False
    user_id = None
    
    if event:
        is_private = event.get("channel_type") == "im"
        user_id = event.get("user")
    elif command:
        is_private = command.get("channel_name") == "directmessage"
        user_id = command.get("user_id")
    
    # Agregar al contexto
    context["is_private"] = is_private
    context["user_id"] = user_id
    
    next()

def create_app() -> App:
    """Crear y configurar la aplicación Slack."""
    app = App(
        token=settings.SLACK_BOT_TOKEN,
        signing_secret=settings.SLACK_SIGNING_SECRET,
        token_verification_enabled=True,
    )
    
    # Agregar middleware en orden
    app.middleware(logging_middleware)
    app.middleware(rate_limit_middleware)
    app.middleware(add_context_middleware)
    
    # Registrar handlers
    register_command_handlers(app)
    register_event_handlers(app)
    
    return app

def main():
    """Función principal."""
    try:
        logger.info("Starting Slack bot...")
        
        app = create_app()
        
        # Usar Socket Mode para desarrollo
        handler = SocketModeHandler(app, settings.SLACK_APP_TOKEN)
        
        logger.info("Bot is running! Press Ctrl+C to stop.")
        handler.start()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()
```

---

## 6. Integración con LLM

### 6.1 Servicio LLM (Ejemplo con Groq)

```python
# src/services/llm_service.py
import os
from groq import Groq
from typing import List, Dict, Any, Optional

class LLMService:
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')
    
    def generate_response(
        self,
        user_message: str,
        conversation_context: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generar respuesta inteligente."""
        
        # Construir prompt del sistema
        system_prompt = self._build_system_prompt(user_context)
        
        # Construir mensajes
        messages = [{"role": "system", "content": system_prompt}]
        
        # Agregar contexto de conversación
        if conversation_context:
            messages.extend(conversation_context)
        
        # Agregar mensaje actual del usuario
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return "Lo siento, no pude procesar tu solicitud en este momento."
    
    def extract_intent(self, text: str) -> Dict[str, Any]:
        """Extraer intención del texto."""
        # Implementar lógica de extracción de intención
        return {"intent": "unknown", "confidence": 0.5}
    
    def _build_system_prompt(self, user_context: Optional[Dict[str, Any]]) -> str:
        """Construir prompt del sistema."""
        return """
        Eres un asistente ejecutivo llamado [Nombre del Bot].
        Ayudas con tareas, recordatorios y gestión de equipos.
        Responde en español de manera profesional y útil.
        """

# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
```

---

## 7. Variables de Entorno

### 7.1 .env.example

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_WORKSPACE_ID=your-workspace-id

# Database Configuration (ejemplo)
DATABASE_URL=your-database-url
DATABASE_KEY=your-database-key

# LLM Configuration
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.1-8b-instant

# Application Configuration
LOG_LEVEL=INFO
DEBUG=False
ENV=development

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_USER_MAX=60
RATE_LIMIT_USER_BURST=10
```

### 7.2 Configuración con Pydantic

```python
# src/utils/config.py
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Slack
    SLACK_BOT_TOKEN: str = Field(..., description="Slack bot token")
    SLACK_APP_TOKEN: str = Field(..., description="Slack app token")
    SLACK_SIGNING_SECRET: str = Field(..., description="Slack signing secret")
    
    # LLM
    GROQ_API_KEY: str = Field(..., description="Groq API key")
    GROQ_MODEL: str = Field("llama-3.1-8b-instant", description="Groq model")
    
    # Application
    LOG_LEVEL: str = Field("INFO", description="Log level")
    ENV: str = Field("development", description="Environment")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

## 8. Troubleshooting Común

### 8.1 Error: 'Args' object has no attribute 'get'

**Causa:** Intentar usar `args.get()` o `args["key"]` en middleware

**Solución:**
```python
# ❌ Incorrecto
event = args.get("event", {})

# ✅ Correcto  
event = getattr(args, 'event', None)
```

### 8.2 Error: dispatch_failed

**Causas comunes:**
- Middleware no llama `next()`
- Exception no manejada en middleware
- Args object mal accedido

**Solución:**
```python
def middleware(args, next):
    try:
        # Tu lógica
        next()  # ¡Siempre llamar next()!
    except Exception as e:
        logger.error(f"Middleware error: {e}")
        raise  # Re-raise para que Slack maneje el error
```

### 8.3 Error: missing_scope

**Causa:** App de Slack no tiene los permisos necesarios

**Solución:**
1. Ve a tu app en api.slack.com
2. "OAuth & Permissions" > "Scopes"
3. Agregar scopes faltantes
4. Reinstalar app en workspace

### 8.4 Bot no responde

**Checklist:**
- [ ] Socket Mode habilitado
- [ ] App instalada en workspace
- [ ] Tokens correctos en .env
- [ ] Handlers registrados
- [ ] Bot invitado al canal (si es necesario)

---

## 9. Testing

### 9.1 Test de Handlers

```python
# tests/test_commands.py
import pytest
from unittest.mock import Mock, patch
from src.handlers.commands import handle_main_command

def test_main_command_with_text():
    ack = Mock()
    respond = Mock()
    command = {
        "text": "help",
        "user_id": "U123",
        "channel_id": "C123"
    }
    context = {}
    
    handle_main_command(ack, respond, command, context)
    
    ack.assert_called_once()
    respond.assert_called_once()
    assert "ayuda" in respond.call_args[0][0].lower()
```

### 9.2 Test de Middleware

```python
# tests/test_middleware.py
from src.middleware.logging_middleware import logging_middleware

def test_logging_middleware():
    # Mock Args object
    class MockArgs:
        def __init__(self):
            self.command = {"command": "/test", "user_id": "U123"}
            self.context = {}
    
    args = MockArgs()
    next_called = False
    
    def mock_next():
        nonlocal next_called
        next_called = True
    
    logging_middleware(args, mock_next)
    
    assert next_called
    assert "request_id" in args.context
```

---

## 10. Deployment

### 10.1 Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env .

CMD ["python", "-m", "src.app"]
```

### 10.2 Heroku

```yaml
# Procfile
worker: python -m src.app
```

### 10.3 Railway/Render

```yaml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python -m src.app"
```

---

## 📝 Checklist Final

Antes de lanzar tu bot, verifica:

- [ ] Todos los tokens configurados
- [ ] Middleware usa `getattr()` para Args object
- [ ] Handlers llaman `ack()` apropiadamente  
- [ ] Error handling implementado
- [ ] Tests pasando
- [ ] Variables de entorno configuradas
- [ ] Logs configurados
- [ ] Rate limiting configurado (si es necesario)
- [ ] Base de datos conectada (si es necesario)
- [ ] LLM configurado (si es necesario)

---

## 🚀 Siguientes Pasos

1. **Monitoreo:** Configura logs y métricas
2. **Escalabilidad:** Implementa rate limiting y caching
3. **Features:** Agrega funcionalidades específicas
4. **Security:** Valida inputs y maneja secretos
5. **Documentation:** Documenta APIs y comandos

---

**¡Felicidades! Tu bot de Slack está listo para funcionar.** 🎉

Esta guía cubre todas las lecciones aprendidas durante el desarrollo de Autónomos Dona y te ahorrará horas de debugging en futuros proyectos.