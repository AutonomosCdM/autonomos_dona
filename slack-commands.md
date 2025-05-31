# Slash Commands Configuration

Add these commands in your Slack app at:
https://api.slack.com/apps/A08MZ21R02D/slash-commands

## Commands to Add:

1. **Command:** `/dona`
   - **Request URL:** Leave empty (using Socket Mode)
   - **Short Description:** Talk to Dona in natural language
   - **Usage Hint:** `[your request]`

2. **Command:** `/dona-help`
   - **Request URL:** Leave empty (using Socket Mode)
   - **Short Description:** Show help and available commands
   - **Usage Hint:** (leave empty)

3. **Command:** `/dona-task`
   - **Request URL:** Leave empty (using Socket Mode)
   - **Short Description:** Manage your tasks
   - **Usage Hint:** `create|list|complete [task details]`

4. **Command:** `/dona-remind`
   - **Request URL:** Leave empty (using Socket Mode)
   - **Short Description:** Set a reminder
   - **Usage Hint:** `[when] [message]`

5. **Command:** `/dona-summary`
   - **Request URL:** Leave empty (using Socket Mode)
   - **Short Description:** View activity summary
   - **Usage Hint:** `today|week`

6. **Command:** `/dona-status`
   - **Request URL:** Leave empty (using Socket Mode)
   - **Short Description:** View your current status and statistics
   - **Usage Hint:** (leave empty)

7. **Command:** `/dona-config`
   - **Request URL:** Leave empty (using Socket Mode)
   - **Short Description:** Configure your preferences
   - **Usage Hint:** `[setting] [value]`

8. **Command:** `/dona-metrics`
   - **Request URL:** Leave empty (using Socket Mode)
   - **Short Description:** View system metrics (admin only)
   - **Usage Hint:** (leave empty)

9. **Command:** `/dona-limits`
   - **Request URL:** Leave empty (using Socket Mode)
   - **Short Description:** Check your rate limit status
   - **Usage Hint:** (leave empty)

## Important Notes:

- Since we're using Socket Mode, you don't need to provide Request URLs
- Make sure Socket Mode is enabled in your app settings
- After adding all commands, save your changes