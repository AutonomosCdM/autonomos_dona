# PRD: Autónomos Dona - Asistente Ejecutivo en Slack

## Resumen Ejecutivo
Autónomos Dona es un agente de inteligencia artificial que opera en Slack como asistente ejecutivo para el equipo fundador de la startup Autónomos. Dona integra capacidades de comunicación con otros agentes especializados (Gmail, Calendar, Docs) mediante una arquitectura A2A (Agent-to-Agent), permitiendo automatizar tareas, mantener trazabilidad y priorizar trabajo sin intervención humana directa.

## Propósito y Objetivos
Dona tiene como propósito principal ordenar y optimizar la operación del equipo fundador, actuando como punto central de coordinación y asistencia. Su evolución planificada permitirá pasar de un asistente con funciones básicas a una secretaria ejecutiva de alto nivel.

## Usuarios y Stakeholders
- **Usuarios Primarios:** Equipo fundador (Tamara, Rodolfo, César)
- **Modos de Interacción:** 
  - Modo Laboral: Visible para todo el equipo
  - Modo Privado: Exclusivo para César y cada integrante del equipo. 

## Requerimientos Funcionales

### Fase 1: Fundación (2-3 semanas)
- Integración con Slack mediante Bolt SDK
- Procesamiento de comandos explícitos
- Diferenciación entre contexto público y privado
- Persistencia básica en Supabase
- Autenticación y manejo de permisos

### Fase 2: Competencia Básica (4-5 semanas)
- Integración con CalendarAgent
- Comandos para gestión de reuniones y recordatorios
- Registro completo de interacciones
- Configuración de permisos para diferentes niveles de acción

### Fase 3: Asistente Funcional (6-8 semanas)
- Integración con GmailAgent y DocsAgent
- Detección de tareas en conversaciones
- Generación de resúmenes de reuniones
- Primeras decisiones autónomas simples

### Fase 4: Asistente Proactivo (8-10 semanas)
- Análisis de patrones en comunicaciones
- Sugerencias de priorización automáticas
- Detección avanzada de tareas implícitas
- Seguimiento proactivo de pendientes

### Fase 5: Secretaria Ejecutiva (12+ semanas)
- Toma de decisiones basada en precedentes
- Manejo autónomo de tareas rutinarias
- Coordinación avanzada entre agentes
- Anticipación de necesidades del equipo

## Capacidades de Onboarding
- Detección automática de nuevos miembros
- Secuencias personalizadas de introducción
- Provisión de documentación contextual según rol
- Seguimiento de progreso de integración
- Presentación automática en canales relevantes
- Compilación de recursos específicos por rol
- Calendario de actividades de integración
- Recordatorios personalizados
- Conexión con mentores asignados
- Reportes de progreso para líderes

## Sistema de Autonomía y Aprobaciones

### Niveles de Autonomía
1. **Observación:** Solo registra información
2. **Sugerencia:** Propone acciones pero no ejecuta
3. **Ejecución Supervisada:** Requiere aprobación explícita
4. **Ejecución Condicionada:** Actúa bajo parámetros predefinidos
5. **Autonomía Completa:** Decide y ejecuta independientemente

### Matriz de Aprobaciones
- Acciones de baja sensibilidad: Nivel 4-5
- Acciones de sensibilidad media: Nivel 3
- Acciones de alta sensibilidad: Nivel 2
- Decisiones con impacto financiero: Nivel 2 con aprobación explícita
- Comunicaciones externas: Nivel 2-3 según importancia

## Arquitectura Técnica

### Componentes Principales
1. **Core de Dona**
   - Gestor de comandos y conversaciones
   - Motor de análisis contextual
   - Sistema de niveles de autonomía
   - Gestor de onboarding

2. **Capa de Integración A2A**
   - Interfaz de comunicación con agentes externos
   - Protocolos de intercambio de mensajes
   - Gestión de estado y sesiones

3. **Agentes Conectados** (implementación progresiva)
   - CalendarAgent: gestión de agenda
   - GmailAgent: gestión de correos
   - DocsAgent: gestión de documentación
   - Agentes específicos según necesidades futuras

4. **Persistencia**
   - Base de datos Supabase
   - Esquema para trazabilidad completa
   - Almacenamiento de configuraciones y precedentes

5. **Orquestador**
   - Control de flujos de trabajo
   - Priorización automática
   - Resolución de dependencias entre tareas

### Modelo de Datos (Supabase)

1. **Tabla Conversaciones**
   - ID, timestamp, canal, usuario_iniciador
   - Contexto (público/privado)
   - Estado (activa, resuelta, etc)

2. **Tabla Mensajes**
   - ID, conversación_id, timestamp
   - Emisor (usuario/Dona/agente)
   - Contenido, intent_detectado
   - Metadatos relevantes

3. **Tabla Tareas**
   - ID, conversación_origen, timestamp
   - Descripción, asignado_a, prioridad
   - Estado, dependencias
   - Agente_responsable (si aplica)

4. **Tabla Acciones_Agentes**
   - ID, tarea_id, agente_id
   - Timestamp, input_enviado
   - Output_recibido, estado
   - Metadatos específicos

5. **Tabla Onboarding**
   - ID, usuario_id, fecha_inicio
   - Etapas_completadas, progreso
   - Recursos_asignados
   - Métricas de efectividad

## Métricas de Éxito

### Métricas de Adopción
- Frecuencia de interacciones por usuario
- Diversidad de comandos utilizados
- Tiempo de respuesta de Dona
- Porcentaje de comandos completados exitosamente

### Métricas de Eficiencia
- Tiempo ahorrado por tarea automatizada
- Reducción en tiempo de coordinación
- Número de interacciones necesarias para completar tareas
- Tasa de acierto en detección de intenciones

### Métricas de Calidad
- Precisión en la ejecución de tareas
- Satisfacción del usuario (feedback explícito)
- Tasa de correcciones necesarias
- Consistencia en resultados similares

### Métricas de Inteligencia
- Precisión en detección de tareas implícitas
- Calidad de resúmenes (evaluación humana)
- Relevancia de sugerencias proactivas
- Tiempo de adaptación a nuevos contextos

### Métricas de Onboarding
- Tiempo hasta productividad completa
- Completitud de tareas de onboarding
- Satisfacción del nuevo miembro
- Integración percibida por el equipo
- Retención temprana

## Consideraciones de Desarrollo

### Enfoque Ágil
- Ciclos de desarrollo cortos (1-2 semanas)
- Revisiones semanales con usuarios clave
- Priorización basada en valor inmediato
- Adaptación continua según feedback

### Requisitos Técnicos
- Python + Slack Bolt SDK
- Supabase para persistencia
- Capa A2A simple pero escalable
- Instrumentación completa para monitoreo

### Seguridad y Privacidad
- Gestión segura de tokens de API
- Separación estricta entre contextos público/privado
- Permisos mínimos necesarios para cada integración
- Cifrado de información sensible

## Roadmap de Implementación
El desarrollo seguirá un enfoque incremental, priorizando funcionalidad básica y expandiendo gradualmente las capacidades de Dona. Cada fase será validada con usuarios reales antes de avanzar a la siguiente.

---

Documento preparado para el inicio del desarrollo de Autónomos Dona.
Versión 1.0 - Mayo 2025