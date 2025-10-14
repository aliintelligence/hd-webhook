#!/bin/bash
# HD Contract Agent Setup Script

echo "=========================================="
echo "HD Contract Agent - Setup Script"
echo "=========================================="
echo ""

# Install pip if needed
echo "1. Installing pip..."
sudo apt update -qq
sudo apt install python3-pip -y -qq

# Install dependencies
echo ""
echo "2. Installing Python dependencies..."
cd /home/matt/hd-contract-agent
pip3 install -r requirements.txt

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Test configuration: python3 test_setup.py"
echo "  2. Setup headers: python3 outlook_agent.py --setup-headers"
echo "  3. Run agent: python3 outlook_agent.py"
echo ""
