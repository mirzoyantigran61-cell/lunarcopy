"""
🎮 Nitro Proxy - Multi-Port Configuration
Each port serves different game modifications
"""

# Port Configuration: {port: {name, folder, description}}
PROXY_PORTS = {
    9999: {
        "name": "DragOnly",
        "folder": "Drag only",
        "description": "Drag modifications only",
        "patches": {
            "fileinfo": "fileinfo",
            "drag": "drag"
        }
    },
    9998: {
        "name": "Antenna",
        "folder": "Antenna hand",
        "description": "Antenna hand modifications",
        "patches": {
            "fileinfo": "fileinfo",
            "antenna": "antenna"
        }
    },
    9997: {
        "name": "MagicBullet",
        "folder": "Magic Bullet",
        "description": "Magic bullet modifications",
        "patches": {
            "fileinfo": "fileinfo",
            "magic": "Magic"
        }
    },
    9996: {
        "name": "Body90",
        "folder": "Body 90%",
        "description": "Body 90% visibility modifications",
        "patches": {
            "fileinfo": "fileinfo",
            "body": "body"
        }
    },
    9995: {
        "name": "DragAntenna",
        "folder": "DragwithAntenna",
        "description": "Drag + Antenna combined",
        "patches": {
            "fileinfo": "fileinfo",
            "dragantenna": "DragXAntenna"
        }
    }
}

# Get port from environment variable (set by systemd service)
import os
CURRENT_PORT = int(os.environ.get('PROXY_PORT', '9999'))

def get_port_config(port=None):
    """Get configuration for specific port"""
    if port is None:
        port = CURRENT_PORT
    return PROXY_PORTS.get(port, PROXY_PORTS[9999])

def get_all_ports():
    """Get list of all configured ports"""
    return sorted(PROXY_PORTS.keys())

def get_patch_folder(port=None):
    """Get the game_patches subfolder for this port"""
    config = get_port_config(port)
    return config.get("folder", "")
