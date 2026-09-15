#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# 🚀 Nitro Proxy - Multi-Port Quick Setup
# ═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Nitro Proxy - Multi-Port Setup"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

PROJECT_DIR="/root/nitro-proxy"
SERVER_IP=$(hostname -I | awk '{print $1}')

# Port configurations
declare -A PORTS
PORTS[9999]="DragOnly"
PORTS[9998]="Antenna"
PORTS[9997]="MagicBullet"
PORTS[9996]="Body90"
PORTS[9995]="DragAntenna"

echo -e "${CYAN}Detected Server IP: ${YELLOW}$SERVER_IP${NC}"
echo ""

# Step 1: Create systemd services for all ports
echo -e "${YELLOW}[1/5]${NC} Creating systemd services for all ports..."
for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    echo -e "${CYAN}  → Port $port (${PORTS[$port]})${NC}"
    
    cat > /etc/systemd/system/nitro-proxy-$port.service << EOF
[Unit]
Description=Nitro Proxy Server - Port $port (${PORTS[$port]})
After=network.target nitro-auth.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment="PROXY_PORT=$port"
ExecStart=/usr/local/bin/mitmdump -s $PROJECT_DIR/proxy.py --listen-host 0.0.0.0 --listen-port $port --set block_global=false
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
done
echo -e "${GREEN}✅ Services created${NC}"
echo ""

# Step 2: Reload systemd
echo -e "${YELLOW}[2/5]${NC} Reloading systemd daemon..."
systemctl daemon-reload
echo -e "${GREEN}✅ Systemd reloaded${NC}"
echo ""

# Step 3: Enable all services
echo -e "${YELLOW}[3/5]${NC} Enabling all proxy services..."
for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    systemctl enable nitro-proxy-$port
done
echo -e "${GREEN}✅ Services enabled${NC}"
echo ""

# Step 4: Configure firewall
echo -e "${YELLOW}[4/5]${NC} Configuring firewall..."
for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    echo -e "${CYAN}  → Opening port $port${NC}"
    ufw allow $port/tcp
done
echo -e "${GREEN}✅ Firewall configured${NC}"
echo ""

# Step 5: Start all services
echo -e "${YELLOW}[5/5]${NC} Starting all proxy services..."
for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    echo -e "${CYAN}  → Starting port $port${NC}"
    systemctl start nitro-proxy-$port
    sleep 1
done
echo -e "${GREEN}✅ All services started${NC}"
echo ""

# Display status
echo "═══════════════════════════════════════════════════════════════"
echo "📊 Services Status"
echo "═══════════════════════════════════════════════════════════════"
echo ""

for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    status=$(systemctl is-active nitro-proxy-$port)
    if [ "$status" = "active" ]; then
        echo -e "${GREEN}✅${NC} Port $port (${PORTS[$port]}): ${GREEN}ACTIVE${NC}"
    else
        echo -e "${RED}❌${NC} Port $port (${PORTS[$port]}): ${RED}$status${NC}"
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Multi-Port Setup Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${CYAN}🌐 Server IP:${NC} ${YELLOW}$SERVER_IP${NC}"
echo ""
echo -e "${CYAN}📋 Available Ports:${NC}"
for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    echo -e "  ${YELLOW}$port${NC}: ${PORTS[$port]}"
done
echo ""
echo -e "${CYAN}📋 Useful Commands:${NC}"
echo "  - Manage all ports: ./manage_ports.sh"
echo "  - Check status: systemctl status nitro-proxy-9998"
echo "  - View logs: journalctl -u nitro-proxy-9998 -f"
echo "  - Restart port: systemctl restart nitro-proxy-9998"
echo "  - Stop all: systemctl stop nitro-proxy-*"
echo ""
echo -e "${CYAN}📖 Full Guide:${NC} See MULTI_PORT_GUIDE.md"
echo ""
echo "═══════════════════════════════════════════════════════════════"
