#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# 🧪 Nitro Proxy - Multi-Port Testing Script
# ═══════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════════════"
echo "🧪 Testing Nitro Proxy Multi-Port System"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_DIR="/root/Main"

# Port configurations
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

echo -e "${CYAN}Test 1: Checking Configuration Files${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check proxy_config.py
if [ -f "$PROJECT_DIR/proxy_config.py" ]; then
    echo -e "${GREEN}✓${NC} proxy_config.py exists"
else
    echo -e "${RED}✗${NC} proxy_config.py missing"
fi

# Check proxy.py
if [ -f "$PROJECT_DIR/proxy.py" ]; then
    echo -e "${GREEN}✓${NC} proxy.py exists"
else
    echo -e "${RED}✗${NC} proxy.py missing"
fi

echo ""
echo -e "${CYAN}Test 2: Checking Game Patches Folders${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    folder="${FOLDERS[$port]}"
    if [ -z "$folder" ]; then
        # Root folder (should not happen now)
        if [ -f "$PROJECT_DIR/game_patches/fileinfo.txt" ]; then
            echo -e "${GREEN}✓${NC} Port $port (${PORTS[$port]}): Root folder OK"
        else
            echo -e "${RED}✗${NC} Port $port (${PORTS[$port]}): Missing fileinfo.txt"
        fi
    else
        # Subfolder
        if [ -d "$PROJECT_DIR/game_patches/$folder" ]; then
            if [ -f "$PROJECT_DIR/game_patches/$folder/fileinfo.txt" ]; then
                echo -e "${GREEN}✓${NC} Port $port (${PORTS[$port]}): Folder exists with fileinfo.txt"
            else
                echo -e "${YELLOW}⚠${NC} Port $port (${PORTS[$port]}): Folder exists but missing fileinfo.txt"
            fi
        else
            echo -e "${RED}✗${NC} Port $port (${PORTS[$port]}): Folder missing: $folder"
        fi
    fi
done

echo ""
echo -e "${CYAN}Test 3: Checking Systemd Services${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    if [ -f "/etc/systemd/system/nitro-proxy-$port.service" ]; then
        echo -e "${GREEN}✓${NC} Service file exists: nitro-proxy-$port.service"
    else
        echo -e "${RED}✗${NC} Service file missing: nitro-proxy-$port.service"
    fi
done

echo ""
echo -e "${CYAN}Test 4: Checking Service Status${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    status=$(systemctl is-active nitro-proxy-$port 2>/dev/null || echo "not-found")
    if [ "$status" = "active" ]; then
        echo -e "${GREEN}✓${NC} Port $port (${PORTS[$port]}): ${GREEN}ACTIVE${NC}"
    elif [ "$status" = "inactive" ]; then
        echo -e "${YELLOW}⚠${NC} Port $port (${PORTS[$port]}): ${YELLOW}INACTIVE${NC}"
    else
        echo -e "${RED}✗${NC} Port $port (${PORTS[$port]}): ${RED}NOT FOUND${NC}"
    fi
done

echo ""
echo -e "${CYAN}Test 5: Checking Network Ports${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Use ss (modern) or netstat (fallback)
if command -v ss &> /dev/null; then
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        if ss -tuln | grep -q ":$port "; then
            echo -e "${GREEN}✓${NC} Port $port: ${GREEN}LISTENING${NC}"
        else
            echo -e "${RED}✗${NC} Port $port: ${RED}NOT LISTENING${NC}"
        fi
    done
elif command -v netstat &> /dev/null; then
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        if netstat -tuln | grep -q ":$port "; then
            echo -e "${GREEN}✓${NC} Port $port: ${GREEN}LISTENING${NC}"
        else
            echo -e "${RED}✗${NC} Port $port: ${RED}NOT LISTENING${NC}"
        fi
    done
else
    echo -e "${YELLOW}⚠${NC} Neither 'ss' nor 'netstat' found. Install net-tools: apt install net-tools"
    echo -e "${CYAN}ℹ${NC} Skipping port listening check..."
fi

echo ""
echo -e "${CYAN}Test 6: Checking Firewall Rules${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    if ufw status | grep -q "$port/tcp"; then
        echo -e "${GREEN}✓${NC} Port $port: Firewall rule exists"
    else
        echo -e "${YELLOW}⚠${NC} Port $port: No firewall rule (may be OK if UFW disabled)"
    fi
done

echo ""
echo -e "${CYAN}Test 7: Checking Python Dependencies${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v mitmdump &> /dev/null; then
    echo -e "${GREEN}✓${NC} mitmproxy installed"
else
    echo -e "${RED}✗${NC} mitmproxy not found"
fi

if python3 -c "import flask" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Flask installed"
else
    echo -e "${RED}✗${NC} Flask not installed"
fi

if python3 -c "import telegram" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} python-telegram-bot installed"
else
    echo -e "${RED}✗${NC} python-telegram-bot not installed"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${CYAN}Test Summary${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Count active services
active_count=0
for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    status=$(systemctl is-active nitro-proxy-$port 2>/dev/null || echo "not-found")
    if [ "$status" = "active" ]; then
        ((active_count++))
    fi
done

total_ports=${#PORTS[@]}
echo -e "Active Ports: ${GREEN}$active_count${NC} / $total_ports"

if [ $active_count -eq $total_ports ]; then
    echo -e "${GREEN}✓ All ports are running!${NC}"
elif [ $active_count -gt 0 ]; then
    echo -e "${YELLOW}⚠ Some ports are not running${NC}"
else
    echo -e "${RED}✗ No ports are running${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "💡 Tips:"
echo "  - To start all ports: systemctl start nitro-proxy-*"
echo "  - To view logs: journalctl -u nitro-proxy-9998 -f"
echo "  - To manage ports: ./manage_ports.sh"
echo ""
