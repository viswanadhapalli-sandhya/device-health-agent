import psutil
import platform
from datetime import datetime


def get_cpu_usage():
    return psutil.cpu_percent(interval=1)


def get_ram_usage():
    memory = psutil.virtual_memory()
    return memory.percent


def get_disk_usage():
    disk = psutil.disk_usage('/')
    return disk.percent


def get_battery_status():
    battery = psutil.sensors_battery()
    if battery:
        return {
            "percent": battery.percent,
            "plugged": battery.power_plugged
        }
    return None


def get_system_info():
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine()
    }


def get_all_stats():
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu": get_cpu_usage(),
        "ram": get_ram_usage(),
        "disk": get_disk_usage(),
        "battery": get_battery_status(),
        "system": get_system_info()
    }