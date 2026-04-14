import json
import os
from datetime import datetime


def append_json_log(log_path, payload):
	os.makedirs(os.path.dirname(log_path), exist_ok=True)
	entry = {
		"timestamp": datetime.now().isoformat(timespec="seconds"),
		**payload,
	}
	with open(log_path, "a", encoding="utf-8") as file:
		file.write(json.dumps(entry, ensure_ascii=False) + "\n")
