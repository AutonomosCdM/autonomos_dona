# Configurar Slash Commands en Slack

Ve a: https://api.slack.com/apps/A08MZ21R02D/slash-commands

## Pasos:

1. **Haz clic en "Create New Command"** para cada uno de estos comandos:

### Comando 1: /dona
- **Command:** `/dona`
- **Request URL:** (déjalo vacío - usamos Socket Mode)
- **Short Description:** `Talk to Dona in natural language`
- **Usage Hint:** `[your request]`
- **Escape channels, users, and links sent to your app:** ❌ (unchecked)

### Comando 2: /dona-help
- **Command:** `/dona-help`
- **Request URL:** (déjalo vacío)
- **Short Description:** `Show help and available commands`
- **Usage Hint:** (déjalo vacío)
- **Escape channels, users, and links sent to your app:** ❌ (unchecked)

### Comando 3: /dona-task
- **Command:** `/dona-task`
- **Request URL:** (déjalo vacío)
- **Short Description:** `Manage your tasks`
- **Usage Hint:** `create|list|complete [task details]`
- **Escape channels, users, and links sent to your app:** ❌ (unchecked)

### Comando 4: /dona-remind
- **Command:** `/dona-remind`
- **Request URL:** (déjalo vacío)
- **Short Description:** `Set a reminder`
- **Usage Hint:** `[when] [message]`
- **Escape channels, users, and links sent to your app:** ❌ (unchecked)

### Comando 5: /dona-summary
- **Command:** `/dona-summary`
- **Request URL:** (déjalo vacío)
- **Short Description:** `View activity summary`
- **Usage Hint:** `today|week`
- **Escape channels, users, and links sent to your app:** ❌ (unchecked)

### Comando 6: /dona-status
- **Command:** `/dona-status`
- **Request URL:** (déjalo vacío)
- **Short Description:** `View your current status and statistics`
- **Usage Hint:** (déjalo vacío)
- **Escape channels, users, and links sent to your app:** ❌ (unchecked)

### Comando 7: /dona-config
- **Command:** `/dona-config`
- **Request URL:** (déjalo vacío)
- **Short Description:** `Configure your preferences`
- **Usage Hint:** `[setting] [value]`
- **Escape channels, users, and links sent to your app:** ❌ (unchecked)

### Comando 8: /dona-metrics
- **Command:** `/dona-metrics`
- **Request URL:** (déjalo vacío)
- **Short Description:** `View system metrics (admin only)`
- **Usage Hint:** (déjalo vacío)
- **Escape channels, users, and links sent to your app:** ❌ (unchecked)

### Comando 9: /dona-limits
- **Command:** `/dona-limits`
- **Request URL:** (déjalo vacío)
- **Short Description:** `Check your rate limit status`
- **Usage Hint:** (déjalo vacío)
- **Escape channels, users, and links sent to your app:** ❌ (unchecked)

## Después de agregar todos los comandos:

1. **Haz clic en "Save Changes"**
2. **Verifica que Socket Mode esté habilitado** en: https://api.slack.com/apps/A08MZ21R02D/socket-mode
3. **Reinstala la app** si es necesario en: https://api.slack.com/apps/A08MZ21R02D/install-on-team

¡Una vez completado, todos los comandos estarán disponibles en tu workspace de Slack!