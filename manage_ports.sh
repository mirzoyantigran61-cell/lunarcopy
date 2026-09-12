#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# 🎮 Nitro Proxy - Multi-Port Management Script
# ═══════════════════════════════════════════════════════════════

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

PROJECT_DIR="/root/nitro-proxy"

# Port configurations
declare -A PORTS
PORTS[9999]="DragOnly"
PORTS[9998]="Antenna"
PORTS[9997]="MagicBullet"
PORTS[9996]="Body90"
PORTS[9995]="DragAntenna"

show_menu() {
    clear
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🎮 Nitro Proxy - Multi-Port Management${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}Available Ports:${NC}"
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        echo -e "  ${YELLOW}Port $port${NC}: ${PORTS[$port]}"
    done
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "1) 🚀 Start All Proxy Ports"
    echo "2) 🛑 Stop All Proxy Ports"
    echo "3) 🔄 Restart All Proxy Ports"
    echo "4) 📊 Check Status (All Ports)"
    echo "5) 🎯 Manage Specific Port"
    echo "6) 📋 View Logs (Select Port)"
    echo "7) 🔧 Start/Stop Auth & Bots"
    echo "8) 📈 System Resources"
    echo "9) 🔥 Setup All Services (First Time)"
    echo "0) ❌ Exit"
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -n "Select option: "
}

start_all_proxies() {
    echo -e "${YELLOW}Starting all proxy ports...${NC}"
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        echo -e "${CYAN}Starting port $port - ${PORTS[$port]}${NC}"
        systemctl start nitro-proxy-$port
        sleep 1
    done
    echo -e "${GREEN}✅ All proxy ports started${NC}"
    sleep 2
}

stop_all_proxies() {
    echo -e "${YELLOW}Stopping all proxy ports...${NC}"
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        echo -e "${CYAN}Stopping port $port${NC}"
        systemctl stop nitro-proxy-$port
    done
    echo -e "${GREEN}✅ All proxy ports stopped${NC}"
    sleep 2
}

restart_all_proxies() {
    echo -e "${YELLOW}Restarting all proxy ports...${NC}"
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        echo -e "${CYAN}Restarting port $port - ${PORTS[$port]}${NC}"
        systemctl restart nitro-proxy-$port
        sleep 1
    done
    echo -e "${GREEN}✅ All proxy ports restarted${NC}"
    sleep 2
}

check_status() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}📊 Proxy Ports Status${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        echo -e "${YELLOW}Port $port - ${PORTS[$port]}:${NC}"
        systemctl status nitro-proxy-$port --no-pager -l | head -n 3
        echo ""
    done
    
    echo -e "${YELLOW}Auth Server:${NC}"
    systemctl status nitro-auth --no-pager -l | head -n 3
    echo ""
    
    echo -e "${YELLOW}Telegram Bots:${NC}"
    systemctl status nitro-bots --no-pager -l | head -n 3
    echo ""
    
    read -p "Press Enter to continue..."
}

manage_specific_port() {
    echo ""
    echo -e "${CYAN}Select port to manage:${NC}"
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        echo "  $port) ${PORTS[$port]}"
    done
    echo "  0) Back"
    echo ""
    read -p "Enter port number: " selected_port
    
    if [ "$selected_port" = "0" ]; then
        return
    fi
    
    if [ -z "${PORTS[$selected_port]}" ]; then
        echo -e "${RED}Invalid port${NC}"
        sleep 1
        return
    fi
    
    while true; do
        clear
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}Managing Port $selected_port - ${PORTS[$selected_port]}${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "1) Start"
        echo "2) Stop"
        echo "3) Restart"
        echo "4) Status"
        echo "5) View Logs"
        echo "0) Back"
        echo ""
        read -p "Select action: " action
        
        case $action in
            1)
                systemctl start nitro-proxy-$selected_port
                echo -e "${GREEN}✅ Port $selected_port started${NC}"
                sleep 2
                ;;
            2)
                systemctl stop nitro-proxy-$selected_port
                echo -e "${GREEN}✅ Port $selected_port stopped${NC}"
                sleep 2
                ;;
            3)
                systemctl restart nitro-proxy-$selected_port
                echo -e "${GREEN}✅ Port $selected_port restarted${NC}"
                sleep 2
                ;;
            4)
                systemctl status nitro-proxy-$selected_port --no-pager -l
                read -p "Press Enter to continue..."
                ;;
            5)
                echo -e "${YELLOW}Viewing logs for port $selected_port (Press Ctrl+C to exit)${NC}"
                sleep 2
                journalctl -u nitro-proxy-$selected_port -f
                ;;
            0)
                break
                ;;
            *)
                echo -e "${RED}Invalid option${NC}"
                sleep 1
                ;;
        esac
    done
}

view_logs_menu() {
    echo ""
    echo -e "${CYAN}Select service to view logs:${NC}"
    echo "  1) Auth Server"
    echo "  2) Telegram Bots"
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        echo "  $port) Proxy Port $port - ${PORTS[$port]}"
    done
    echo "  0) Back"
    echo ""
    read -p "Enter choice: " choice
    
    if [ "$choice" = "0" ]; then
        return
    elif [ "$choice" = "1" ]; then
        echo -e "${YELLOW}Viewing Auth Server logs (Press Ctrl+C to exit)${NC}"
        sleep 2
        journalctl -u nitro-auth -f
    elif [ "$choice" = "2" ]; then
        echo -e "${YELLOW}Viewing Telegram Bots logs (Press Ctrl+C to exit)${NC}"
        sleep 2
        journalctl -u nitro-bots -f
    elif [ ! -z "${PORTS[$choice]}" ]; then
        echo -e "${YELLOW}Viewing logs for port $choice (Press Ctrl+C to exit)${NC}"
        sleep 2
        journalctl -u nitro-proxy-$choice -f
    else
        echo -e "${RED}Invalid choice${NC}"
        sleep 1
    fi
}

manage_auth_bots() {
    while true; do
        clear
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}🔧 Auth Server & Telegram Bots Management${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "1) Start Auth & Bots"
        echo "2) Stop Auth & Bots"
        echo "3) Restart Auth & Bots"
        echo "4) Status"
        echo "0) Back"
        echo ""
        read -p "Select action: " action
        
        case $action in
            1)
                systemctl start nitro-auth
                sleep 2
                systemctl start nitro-bots
                echo -e "${GREEN}✅ Auth & Bots started${NC}"
                sleep 2
                ;;
            2)
                systemctl stop nitro-bots
                systemctl stop nitro-auth
                echo -e "${GREEN}✅ Auth & Bots stopped${NC}"
                sleep 2
                ;;
            3)
                systemctl restart nitro-auth
                sleep 2
                systemctl restart nitro-bots
                echo -e "${GREEN}✅ Auth & Bots restarted${NC}"
                sleep 2
                ;;
            4)
                echo -e "${YELLOW}Auth Server:${NC}"
                systemctl status nitro-auth --no-pager -l | head -n 5
                echo ""
                echo -e "${YELLOW}Telegram Bots:${NC}"
                systemctl status nitro-bots --no-pager -l | head -n 5
                echo ""
                read -p "Press Enter to continue..."
                ;;
            0)
                break
                ;;
            *)
                echo -e "${RED}Invalid option${NC}"
                sleep 1
                ;;
        esac
    done
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
    
    echo -e "${YELLOW}Network Connections (Proxy Ports):${NC}"
    netstat -tulpn | grep -E ':(5000|999[4-9])'
    echo ""
    
    read -p "Press Enter to continue..."
}

setup_all_services() {
    echo -e "${YELLOW}Setting up all services...${NC}"
    echo ""
    
    # Create systemd services for each port
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        echo -e "${CYAN}Creating service for port $port - ${PORTS[$port]}${NC}"
        
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
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable all services
    echo ""
    echo -e "${YELLOW}Enabling all services...${NC}"
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        systemctl enable nitro-proxy-$port
    done
    
    # Open firewall ports
    echo ""
    echo -e "${YELLOW}Configuring firewall...${NC}"
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        ufw allow $port/tcp
    done
    
    echo ""
    echo -e "${GREEN}✅ All services setup complete!${NC}"
    echo ""
    echo -e "${CYAN}Available ports:${NC}"
    for port in $(echo "${!PORTS[@]}" | tr ' ' '\n' | sort -n); do
        echo -e "  ${YELLOW}$port${NC}: ${PORTS[$port]}"
    done
    echo ""
    read -p "Press Enter to continue..."
}

# Main Loop
while true; do
    show_menu
    read choice
    
    case $choice in
        1) start_all_proxies ;;
        2) stop_all_proxies ;;
        3) restart_all_proxies ;;
        4) check_status ;;
        5) manage_specific_port ;;
        6) view_logs_menu ;;
        7) manage_auth_bots ;;
        8) system_resources ;;
        9) setup_all_services ;;
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
