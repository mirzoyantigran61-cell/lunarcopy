#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# 🚀 Nitro Proxy - VPS Auto Installation Script
# ═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Nitro Proxy - VPS Installation"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
PROJECT_DIR="/root/Main"
SERVER_IP="@@your vps_public_ip_here@@"  # Replace with your VPS public IP

# Step 1: Update System
echo -e "${YELLOW}[1/8]${NC} Updating system..."
apt update && apt upgrade -y
echo -e "${GREEN}✅ System updated${NC}"
echo ""

# Step 2: Install Dependencies
echo -e "${YELLOW}[2/8]${NC} Installing dependencies..."
apt install -y python3 python3-pip git screen nano curl wget ufw htop
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 3: Install Python Packages
echo -e "${YELLOW}[3/8]${NC} Installing Python packages..."
cd $PROJECT_DIR
pip3 install -r requirements.txt
pip3 install mitmproxy
echo -e "${GREEN}✅ Python packages installed${NC}"
echo ""

# Step 4: Configure Firewall
echo -e "${YELLOW}[4/8]${NC} Configuring firewall..."
ufw --force enable
ufw allow 22/tcp
ufw allow 5000/tcp
ufw allow 9999/tcp
echo -e "${GREEN}✅ Firewall configured${NC}"
echo ""

# Step 5: Update IP Addresses in Code
echo -e "${YELLOW}[5/8]${NC} Updating IP addresses..."

# Update proxy.py
sed -i "s|SERVER_URL = \"http://127.0.0.1:5000\"|SERVER_URL = \"http://$SERVER_IP:5000\"|g" $PROJECT_DIR/proxy.py

# Update auth_server.py
sed -i "s|app.run(host='127.0.0.1', port=5000)|app.run(host='0.0.0.0', port=5000)|g" $PROJECT_DIR/chanbomaydi_system/auth_server.py

echo -e "${GREEN}✅ IP addresses updated${NC}"
echo ""

# Step 6: Create Systemd Services
echo -e "${YELLOW}[6/8]${NC} Creating systemd services..."

# Auth Server Service
cat > /etc/systemd/system/nitro-auth.service << EOF
[Unit]
Description=Nitro Proxy Auth Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR/nitro_system
ExecStart=/usr/bin/python3 $PROJECT_DIR/nitro_system/auth_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Telegram Bots Service
cat > /etc/systemd/system/nitro-bots.service << EOF
[Unit]
Description=Nitro Proxy Telegram Bots
After=network.target nitro-auth.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR/nitro_system
ExecStart=/usr/bin/python3 $PROJECT_DIR/nitro_system/bots.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Proxy Server Service (mitmdump)
# مهم: block_global=false يسمح للموبايل بالاتصال من الإنترنت. بدونها mitmproxy يقتل الاتصال (killed by block_global).
# Important: block_global=false allows remote clients. Default true blocks public IPs connecting to this VPS.
cat > /etc/systemd/system/nitro-proxy.service << EOF
[Unit]
Description=Nitro Proxy Server (mitmdump, block_global off for remote users)
After=network.target nitro-auth.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/mitmdump -s $PROJECT_DIR/proxy.py --listen-host 0.0.0.0 --listen-port 9999 --set block_global=false
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Systemd services created${NC}"
echo ""

# Step 7: Enable and Start Services
echo -e "${YELLOW}[7/8]${NC} Starting services..."
systemctl daemon-reload
systemctl enable nitro-auth nitro-bots nitro-proxy
systemctl start nitro-auth
sleep 3
systemctl start nitro-bots
sleep 2
systemctl start nitro-proxy
echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Step 8: Install Security Tools
echo -e "${YELLOW}[8/8]${NC} Installing security tools..."
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
echo -e "${GREEN}✅ Security tools installed${NC}"
echo ""

# Display Status
echo "═══════════════════════════════════════════════════════════════"
echo "📊 Services Status"
echo "═══════════════════════════════════════════════════════════════"
echo ""

systemctl status nitro-auth --no-pager -l | head -n 5
echo ""
systemctl status nitro-bots --no-pager -l | head -n 5
echo ""
systemctl status nitro-proxy --no-pager -l | head -n 5
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "✅ Installation Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Server IP: $SERVER_IP"
echo "🔒 Auth Server: http://$SERVER_IP:5000"
echo "🔌 Proxy Server: http://$SERVER_IP:9999"
echo ""
echo "📋 Useful Commands:"
echo "  - Check status: systemctl status nitro-bots"
echo "  - View logs: journalctl -u nitro-bots -f"
echo "  - Restart: systemctl restart nitro-bots"
echo "  - Stop: systemctl stop nitro-bots"
echo ""
echo "═══════════════════════════════════════════════════════════════"
