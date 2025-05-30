# Contributing to Autónomos Dona

## Convenciones de Commits

Este proyecto sigue las convenciones de commits para mantener un historial limpio y comprensible.

### Tipos de Commits

- **feat**: Nueva funcionalidad
- **fix**: Corrección de error  
- **docs**: Cambios en documentación
- **style**: Cambios de formato (espacios, punto y coma, etc.)
- **refactor**: Refactorización sin cambio funcional
- **test**: Agregar o modificar tests
- **chore**: Tareas de mantenimiento (actualizar dependencias, configuración, etc.)

### Formato

```
tipo(alcance): breve descripción

[cuerpo opcional]

[footer opcional]
```

### Ejemplos

```bash
feat(commands): agregar comando dona-remind para recordatorios

fix(auth): corregir validación de tokens en middleware

docs(setup): actualizar instrucciones de configuración de Slack

style(handlers): aplicar formato consistente en event handlers

refactor(supabase): simplificar lógica de consultas a base de datos

test(commands): agregar tests para comando dona-task

chore(deps): actualizar slack-bolt a versión 1.18.0
```

### Alcance (Scope)

El alcance es opcional pero recomendado. Algunos alcances comunes:

- **app**: Aplicación principal
- **commands**: Handlers de comandos
- **events**: Handlers de eventos
- **services**: Servicios (Supabase, Slack)
- **models**: Modelos y esquemas
- **utils**: Utilidades
- **db**: Base de datos
- **docs**: Documentación
- **tests**: Pruebas

### Reglas Adicionales

1. Usa el tiempo presente imperativo: "agregar" no "agregado" ni "agrega"
2. No capitalices la primera letra
3. No uses punto al final del título
4. El título debe tener máximo 72 caracteres
5. Separa el título del cuerpo con una línea en blanco
6. Usa el cuerpo para explicar el *qué* y el *por qué*, no el *cómo*

### Commits que Rompen Compatibilidad

Si un commit introduce cambios que rompen compatibilidad hacia atrás, agrega `BREAKING CHANGE:` en el footer:

```
feat(api): cambiar estructura de respuesta de tareas

BREAKING CHANGE: El campo 'task_id' ahora se llama 'id'
```

## Flujo de Trabajo

1. Crea una rama para tu feature/fix: `git checkout -b feat/nueva-funcionalidad`
2. Realiza tus cambios siguiendo los estándares del proyecto
3. Haz commits siguiendo estas convenciones
4. Asegúrate de que todos los tests pasen: `make test`
5. Verifica el linting: `make lint`
6. Push y crea un Pull Request

## Estándares de Código

- Sigue PEP 8 para Python
- Usa type hints en todas las funciones
- Documenta funciones complejas con docstrings
- Mantén las funciones pequeñas y enfocadas
- Escribe tests para nueva funcionalidad

## Tests

- Escribe tests unitarios para nueva lógica
- Mantén cobertura de tests > 80%
- Los tests deben ser determinísticos y rápidos
- Usa mocks para dependencias externas

## Documentación

- Actualiza README.md si agregas funcionalidad significativa
- Documenta APIs públicas
- Agrega ejemplos de uso cuando sea apropiado
- Mantén la documentación actualizada con el código