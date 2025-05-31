"""
LLM service for intelligent conversation handling using Groq.

This module provides LLM capabilities for natural language understanding
and generation in the Autónomos Dona assistant.
"""

import logging
from typing import Dict, Any, Optional, List
import requests
import json

from src.utils.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM interactions using Groq API."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # System prompt for Dona
        self.system_prompt = """
Eres Dona, una asistente ejecutiva AI especializada en ayudar al equipo fundador de la startup Autónomos. 

Tu personalidad:
- Profesional pero amigable
- Eficiente y orientada a resultados
- Bilingüe (español/inglés) - responde en el idioma que te hablen
- Proactiva en sugerir mejoras y organización

Tus capacidades principales:
- Gestión de tareas y proyectos
- Programación de reuniones y recordatorios
- Análisis de productividad
- Coordinación de equipo
- Resúmenes ejecutivos

Contexto: Trabajas dentro de Slack como bot integrado. Puedes ejecutar comandos específicos como crear tareas (/dona-task), configurar recordatorios (/dona-remind), y generar resúmenes (/dona-summary).

Responde de manera concisa y accionable. Si el usuario necesita hacer algo específico, sugiere el comando apropiado.
"""
    
    def generate_response(
        self,
        user_message: str,
        conversation_context: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response using the LLM.
        
        Args:
            user_message: The user's input message
            conversation_context: Previous messages in the conversation
            user_context: Additional context about the user/situation
            
        Returns:
            Generated response from the LLM
        """
        try:
            # Build messages for the API
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation context if provided
            if conversation_context:
                messages.extend(conversation_context[-5:])  # Last 5 messages for context
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            # Make API request
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return self._get_fallback_response(user_message)
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return self._get_fallback_response(user_message)
    
    def extract_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Extract intent and entities from user message.
        
        Args:
            user_message: The user's input message
            
        Returns:
            Dictionary with intent, entities, and confidence
        """
        try:
            intent_prompt = f"""
Analiza el siguiente mensaje y extrae:
1. Intención principal (task, reminder, question, help, summary, status, config)
2. Entidades clave (fechas, nombres, prioridades, etc.)
3. Nivel de confianza (1-10)

Mensaje: "{user_message}"

Responde solo con JSON válido:
{{
    "intent": "categoria_principal",
    "entities": {{"clave": "valor"}},
    "confidence": numero,
    "suggested_command": "comando_slack_sugerido"
}}
"""
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": intent_prompt}],
                "max_tokens": 200,
                "temperature": 0.3
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # Try to parse JSON response
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return self._classify_intent_simple(user_message)
            else:
                return self._classify_intent_simple(user_message)
                
        except Exception as e:
            logger.error(f"Error extracting intent: {e}")
            return self._classify_intent_simple(user_message)
    
    def _classify_intent_simple(self, message: str) -> Dict[str, Any]:
        """Simple rule-based intent classification fallback."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["task", "tarea", "hacer", "create", "crear"]):
            return {
                "intent": "task",
                "entities": {},
                "confidence": 7,
                "suggested_command": "/dona-task create"
            }
        elif any(word in message_lower for word in ["remind", "recordar", "recordatorio", "reminder"]):
            return {
                "intent": "reminder",
                "entities": {},
                "confidence": 7,
                "suggested_command": "/dona-remind"
            }
        elif any(word in message_lower for word in ["help", "ayuda", "commands", "comandos"]):
            return {
                "intent": "help",
                "entities": {},
                "confidence": 8,
                "suggested_command": "/dona-help"
            }
        elif any(word in message_lower for word in ["summary", "resumen", "status", "estado"]):
            return {
                "intent": "summary",
                "entities": {},
                "confidence": 7,
                "suggested_command": "/dona-summary"
            }
        else:
            return {
                "intent": "question",
                "entities": {},
                "confidence": 5,
                "suggested_command": None
            }
    
    def _get_fallback_response(self, user_message: str) -> str:
        """Generate a fallback response when LLM is unavailable."""
        intent_data = self._classify_intent_simple(user_message)
        intent = intent_data["intent"]
        
        fallback_responses = {
            "task": "Entiendo que quieres gestionar tareas. Usa `/dona-task create [descripción]` para crear una nueva tarea.",
            "reminder": "Para configurar un recordatorio, usa `/dona-remind [cuándo] [mensaje]`.",
            "help": "Estos son algunos comandos útiles:\n• `/dona-help` - Ver ayuda completa\n• `/dona-task` - Gestionar tareas\n• `/dona-summary` - Ver resumen",
            "summary": "Para ver tu resumen de actividad, usa `/dona-summary today` o `/dona-summary week`.",
            "question": "¡Hola! Soy Dona, tu asistente ejecutiva. ¿En qué puedo ayudarte? Usa `/dona-help` para ver todos los comandos disponibles."
        }
        
        return fallback_responses.get(intent, fallback_responses["question"])


# Global service instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service