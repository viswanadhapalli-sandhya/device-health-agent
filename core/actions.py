import os
import psutil
import tempfile
import time

# 🔹 Clear temporary files
def clear_temp_files():
    temp_dir = tempfile.gettempdir()
    deleted_files = 0

    for file in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file)

        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                deleted_files += 1
        except Exception:
            pass  # skip locked/system files

    return f"Cleared {deleted_files} temp files"


# 🔹 Kill high CPU process (safe version)
def kill_high_cpu_process(threshold=30):
    killed = None

    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            # refresh cpu usage
            proc.cpu_percent(interval=0.5)

            if proc.info['cpu_percent'] > threshold:
                proc.kill()
                killed = proc.info['name']
                break

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        return f"Killed process: {killed}"
    else:
        return "No high CPU process found"


# 🔹 Get top processes (for UI / debugging)


def get_top_processes(limit=5):
    processes = []

    # First call (initialize CPU tracking)
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc.cpu_percent(None)
        except:
            continue

    time.sleep(0.5)  # allow measurement window

    # Second call (actual values)
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            cpu = proc.cpu_percent(None)
            if cpu > 0:
                processes.append((proc.info['name'], cpu))
        except:
            continue

    processes.sort(key=lambda x: x[1], reverse=True)
    return processes[:limit]