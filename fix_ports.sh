#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# 🔧 Nitro Proxy - Fix Multi-Port Configuration
# ═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🔧 Fixing Nitro Proxy Multi-Port Configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_DIR="/root/nitro-proxy"

# New port configurations (without 9994)
declare -A PORTS
PORTS[9999]="DragOnly"
PORTS[9998]="Antenna"
PORTS[9997]="MagicBullet"
PORTS[9996]="Body90"
PORTS[9995]="DragAntenna"

declare -A FOLDERS
FOLDERS[9999]="Drag only"
FOLDERS[9998]="Antenna hand"
FOLDERS[9997]="Magic Bullet"
FOLDERS[9996]="Body 90%"
FOLDERS[9995]="DragwithAntenna"

echo -e "${YELLOW}Step 1: Stopping all proxy services...${NC}"
systemctl stop nitro-proxy-* 2>/dev/null || true
echo -e "${GREEN}✓ Services stopped${NC}"
echo ""

echo -e "${YELLOW}Step 2: Removing old service (9994)...${NC}"
if [ -f "/etc/systemd/system/nitro-proxy-9994.service" ]; then
    systemctl disable nitro-proxy-9994 2>/dev/null || true
    rm -f /etc/systemd/system/nitro-proxy-9994.service
    echo -e "${GREEN}✓ Removed nitro-proxy-9994.service${NC}"
else
    echo -e "${CYAN}ℹ Service 9994 not found (OK)${NC}"
fi
echo ""

echo -e "${YELLOW}Step 3: Creating/Updating service files...${NC}"
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
echo -e "${GREEN}✓ Service files created${NC}"
echo ""

echo -e "${YELLOW}Step 4: Checking game_patches folders...${NC}"
for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    folder="${FOLDERS[$port]}"
    folder_path="$PROJECT_DIR/game_patches/$folder"
    
    if [ -d "$folder_path" ]; then
        if [ -f "$folder_path/fileinfo.txt" ]; then
            echo -e "${GREEN}✓${NC} Port $port: $folder (fileinfo.txt exists)"
        else
            echo -e "${RED}✗${NC} Port $port: $folder (MISSING fileinfo.txt)"
        fi
    else
        echo -e "${RED}✗${NC} Port $port: Folder missing: $folder"
    fi
done
echo ""

echo -e "${YELLOW}Step 5: Reloading systemd...${NC}"
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd reloaded${NC}"
echo ""

echo -e "${YELLOW}Step 6: Enabling services...${NC}"
for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    systemctl enable nitro-proxy-$port
done
echo -e "${GREEN}✓ Services enabled${NC}"
echo ""

echo -e "${YELLOW}Step 7: Starting services...${NC}"
for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    echo -e "${CYAN}  → Starting port $port${NC}"
    systemctl start nitro-proxy-$port
    sleep 1
done
echo -e "${GREEN}✓ Services started${NC}"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "📊 Service Status"
echo "═══════════════════════════════════════════════════════════════"
echo ""

for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    status=$(systemctl is-active nitro-proxy-$port)
    if [ "$status" = "active" ]; then
        echo -e "${GREEN}✓${NC} Port $port (${PORTS[$port]}): ${GREEN}ACTIVE${NC}"
    else
        echo -e "${RED}✗${NC} Port $port (${PORTS[$port]}): ${RED}$status${NC}"
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🔍 Checking Listening Ports"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Use ss instead of netstat (more modern)
if command -v ss &> /dev/null; then
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        if ss -tuln | grep -q ":$port "; then
            echo -e "${GREEN}✓${NC} Port $port: LISTENING"
        else
            echo -e "${RED}✗${NC} Port $port: NOT LISTENING"
        fi
    done
else
    echo -e "${YELLOW}⚠ 'ss' command not found, skipping port check${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Fix Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${CYAN}📋 Next Steps:${NC}"
echo "1. Check logs: journalctl -u nitro-proxy-9999 -f"
echo "2. Test connection from your device"
echo "3. If issues persist, check game_patches folders"
echo ""
