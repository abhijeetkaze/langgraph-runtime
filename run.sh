#!/bin/bash
# Script to install uv, create a virtual environment, activate it, and create a new .env file with GROQ_API_KEY

# Install uv using pip
pip install uv

# Create a virtual environment using uv
uv venv

# Activate the virtual environment
source .venv/bin/activate --yes

uv sync

# Create a new .env file with the required format
cat <<EOF > .env
GROQ_API_KEY=${YOUR_GROQ_API_KEY}
EOF

echo "Setup complete. Virtual environment created and .env file generated."
