from config.settings import (
    CPU_THRESHOLD,
    RAM_THRESHOLD,
    DISK_THRESHOLD,
    BATTERY_THRESHOLD
)


def analyze(stats):
    issues = []

    # CPU Check
    if stats["cpu"] > CPU_THRESHOLD:
        issues.append({
            "type": "cpu",
            "message": f"High CPU usage: {stats['cpu']}%"
        })

    # RAM Check
    if stats["ram"] > RAM_THRESHOLD:
        issues.append({
            "type": "ram",
            "message": f"High RAM usage: {stats['ram']}%"
        })

    # Disk Check
    if stats["disk"] > DISK_THRESHOLD:
        issues.append({
            "type": "disk",
            "message": f"Low disk space: {stats['disk']}% used"
        })

    # Battery Check
    if stats["battery"]:
        if stats["battery"]["percent"] < BATTERY_THRESHOLD:
            issues.append({
                "type": "battery",
                "message": f"Low battery: {stats['battery']['percent']}%"
            })

    return issues