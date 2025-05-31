#!/bin/bash

# Script to update Slack app with manifest
echo "Updating Slack app with manifest..."

# Set the app ID
APP_ID="A08MZ21R02D"

# Update the app using the manifest
slack app manifest update --app-id=$APP_ID --manifest=manifest.yml

echo "Slack app updated successfully!"
echo ""
echo "Next steps:"
echo "1. Install the app to your workspace if not already installed"
echo "2. Ensure Socket Mode is enabled"
echo "3. All slash commands should now be configured"