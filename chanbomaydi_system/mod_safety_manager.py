"""
Modification Safety Status Manager
"""
import json
import os
import time

MOD_SAFETY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "mod_safety_status.json")

def load_mod_safety_status():
    """Load modification safety status"""
    if not os.path.exists(MOD_SAFETY_FILE):
        default = {
            "9999": {"name": "Drag Only", "status": "safe", "updated_at": 0, "updated_by": None},
            "9998": {"name": "Antenna Hand", "status": "safe", "updated_at": 0, "updated_by": None},
            "9997": {"name": "Magic Bullet", "status": "not_safe", "updated_at": 0, "updated_by": None},
            "9996": {"name": "Body 90%", "status": "safe", "updated_at": 0, "updated_by": None},
            "9995": {"name": "Drag + Antenna", "status": "safe", "updated_at": 0, "updated_by": None}
        }
        save_mod_safety_status(default)
        return default
    try:
        with open(MOD_SAFETY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_mod_safety_status(data):
    """Save modification safety status"""
    os.makedirs(os.path.dirname(MOD_SAFETY_FILE), exist_ok=True)
    with open(MOD_SAFETY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_mod_status(port, status, updated_by):
    """Update status for a specific modification"""
    data = load_mod_safety_status()
    if str(port) in data:
        data[str(port)]["status"] = status
        data[str(port)]["updated_at"] = time.time()
        data[str(port)]["updated_by"] = updated_by
        save_mod_safety_status(data)
        return True
    return False

def get_mod_status(port):
    """Get status for a specific modification"""
    data = load_mod_safety_status()
    return data.get(str(port))
