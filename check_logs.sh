#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# 📋 Nitro Proxy - Quick Logs Checker
# ═══════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo "═══════════════════════════════════════════════════════════════"
echo "📋 Nitro Proxy - Logs Summary"
echo "═══════════════════════════════════════════════════════════════"
echo ""

declare -A PORTS
PORTS[9999]="DragOnly"
PORTS[9998]="Antenna"
PORTS[9997]="MagicBullet"
PORTS[9996]="Body90"
PORTS[9995]="DragAntenna"

for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Port $port (${PORTS[$port]})${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Check if service is active
    status=$(systemctl is-active nitro-proxy-$port 2>/dev/null || echo "not-found")
    if [ "$status" = "active" ]; then
        echo -e "Status: ${GREEN}ACTIVE${NC}"
    else
        echo -e "Status: ${RED}$status${NC}"
    fi
    
    # Show last 5 log lines
    echo ""
    echo "Last 5 log entries:"
    journalctl -u nitro-proxy-$port -n 5 --no-pager 2>/dev/null || echo "No logs available"
    echo ""
done

echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${CYAN}💡 To view live logs for a specific port:${NC}"
echo "   journalctl -u nitro-proxy-9999 -f"
echo ""
echo -e "${CYAN}💡 To view all proxy logs:${NC}"
echo '   journalctl -u "nitro-proxy-*" -f'
echo ""
