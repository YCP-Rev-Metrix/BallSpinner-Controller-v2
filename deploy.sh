#!/bin/bash

# Variables
APP_NAME="sample_app.py"
PI_USER="username"
PI_IP="<RASPBERRY_PI_IP>"
REMOTE_PATH="/home/username/"

# Copy the application to the Raspberry Pi
scp $APP_NAME $PI_USER@$PI_IP:$REMOTE_PATH

# Run the application on the Raspberry Pi
ssh $PI_USER@$PI_IP "python3 $REMOTE_PATH$APP_NAME"