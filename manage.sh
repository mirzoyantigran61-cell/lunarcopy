#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# 🎮 Nitro Proxy - Management Script
# ═══════════════════════════════════════════════════════════════

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_menu() {
    clear
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🎮 Nitro Proxy - Management Panel${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "1) 🚀 Start All Services"
    echo "2) 🛑 Stop All Services"
    echo "3) 🔄 Restart All Services"
    echo "4) 📊 Check Status"
    echo "5) 📋 View Logs (Auth Server)"
    echo "6) 📋 View Logs (Telegram Bots)"
    echo "7) 📋 View Logs (Proxy Server)"
    echo "8) 🔧 Restart Auth Server"
    echo "9) 🔧 Restart Telegram Bots"
    echo "10) 🔧 Restart Proxy Server"
    echo "11) 📈 System Resources"
    echo "12) 🔒 Firewall Status"
    echo "13) 🔄 Update Project"
    echo "0) ❌ Exit"
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -n "Select option: "
}

start_all() {
    echo -e "${YELLOW}Starting all services...${NC}"
    systemctl start nitro-auth
    sleep 2
    systemctl start nitro-bots
    sleep 1
    systemctl start nitro-proxy
    echo -e "${GREEN}✅ All services started${NC}"
    sleep 2
}

stop_all() {
    echo -e "${YELLOW}Stopping all services...${NC}"
    systemctl stop nitro-proxy
    systemctl stop nitro-bots
    systemctl stop nitro-auth
    echo -e "${GREEN}✅ All services stopped${NC}"
    sleep 2
}

restart_all() {
    echo -e "${YELLOW}Restarting all services...${NC}"
    systemctl restart nitro-auth
    sleep 2
    systemctl restart nitro-bots
    sleep 1
    systemctl restart nitro-proxy
    echo -e "${GREEN}✅ All services restarted${NC}"
    sleep 2
}

check_status() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}📊 Services Status${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    echo -e "${YELLOW}Auth Server:${NC}"
    systemctl status nitro-auth --no-pager -l | head -n 5
    echo ""
    
    echo -e "${YELLOW}Telegram Bots:${NC}"
    systemctl status nitro-bots --no-pager -l | head -n 5
    echo ""
    
    echo -e "${YELLOW}Proxy Server:${NC}"
    systemctl status nitro-proxy --no-pager -l | head -n 5
    echo ""
    
    read -p "Press Enter to continue..."
}

view_logs() {
    service=$1
    echo -e "${YELLOW}Viewing logs for $service (Press Ctrl+C to exit)${NC}"
    sleep 2
    journalctl -u $service -f
}

restart_service() {
    service=$1
    echo -e "${YELLOW}Restarting $service...${NC}"
    systemctl restart $service
    echo -e "${GREEN}✅ $service restarted${NC}"
    sleep 2
}

system_resources() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}📈 System Resources${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    echo -e "${YELLOW}CPU & Memory:${NC}"
    top -bn1 | head -n 5
    echo ""
    
    echo -e "${YELLOW}Disk Usage:${NC}"
    df -h | grep -E '^/dev/'
    echo ""
    
    echo -e "${YELLOW}Network Connections:${NC}"
    netstat -tulpn | grep -E ':(5000|9999)'
    echo ""
    
    read -p "Press Enter to continue..."
}

firewall_status() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🔒 Firewall Status${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    ufw status verbose
    echo ""
    read -p "Press Enter to continue..."
}

update_project() {
    echo -e "${YELLOW}Updating project...${NC}"
    echo ""
    echo "1) Update from Git"
    echo "2) Manual update (upload files via FileZilla)"
    echo "0) Cancel"
    echo ""
    read -p "Select option: " update_option
    
    case $update_option in
        1)
            cd /root/nitro-proxy
            echo -e "${YELLOW}Pulling from Git...${NC}"
            git pull
            echo -e "${GREEN}✅ Project updated${NC}"
            echo -e "${YELLOW}Restarting services...${NC}"
            restart_all
            ;;
        2)
            echo -e "${YELLOW}Upload files via FileZilla, then press Enter${NC}"
            read
            echo -e "${YELLOW}Restarting services...${NC}"
            restart_all
            ;;
        0)
            return
            ;;
    esac
    sleep 2
}

# Main Loop
while true; do
    show_menu
    read choice
    
    case $choice in
        1) start_all ;;
        2) stop_all ;;
        3) restart_all ;;
        4) check_status ;;
        5) view_logs "nitro-auth" ;;
        6) view_logs "nitro-bots" ;;
        7) view_logs "nitro-proxy" ;;
        8) restart_service "nitro-auth" ;;
        9) restart_service "nitro-bots" ;;
        10) restart_service "nitro-proxy" ;;
        11) system_resources ;;
        12) firewall_status ;;
        13) update_project ;;
        0) 
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            sleep 1
            ;;
    esac
done
