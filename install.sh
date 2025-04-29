#!/bin/bash
set -e

echo "Installing Gerrit AI Review..."

# Check if we're in the repository directory
if [ ! -f "patch_aider_api.sh" ]; then
    echo "Error: This script must be run from the root of the Gerrit AI Review repository."
    echo "Please navigate to the repository directory and try again."
    exit 1
fi

# Set up Python virtual environment
echo "Setting up Python virtual environment..."
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Apply necessary patches to Aider
echo "Applying patches to Aider..."
./patch_aider_api.sh

# Configure the tool
echo "Creating configuration file..."
if [[ -f "config/config.yaml" ]]; then
    cp config/config.yaml.example config/config.yaml
    echo "Created config/config.yaml from config/config.yaml.example"
fi

echo "Installation complete!"
echo "Please edit config/config.yaml to add your API keys and customize settings"
echo "Important: Set the correct path to your Lustre repository in the config file"
