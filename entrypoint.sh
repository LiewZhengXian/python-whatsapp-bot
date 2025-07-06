#!/bin/bash

# Authenticate ngrok if token is provided
if [ ! -z "$NGROK_AUTH_TOKEN" ]; then
    ngrok config add-authtoken "$NGROK_AUTH_TOKEN"
fi

# Start ngrok in the background with custom domain
ngrok http "$PORT" --domain="$NGROK_DOMAIN" &

# Allow ngrok to establish tunnel
sleep 2

# Start your Python server
python run.py --host
