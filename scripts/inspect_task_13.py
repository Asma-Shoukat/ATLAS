import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONVERSATIONS_DIR = os.path.join(BASE_DIR, "Conversations")
REFERENCE_FILE_PATH = os.path.join(CONVERSATIONS_DIR, "reference.json")

with open(REFERENCE_FILE_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

tasks = data.get("tasks", [])
task_13 = tasks[13]
print("Task Index 13 full details:")
print(json.dumps(task_13, indent=2))

task_14 = tasks[14]
print("\nTask Index 14 full details:")
print(json.dumps(task_14, indent=2))
