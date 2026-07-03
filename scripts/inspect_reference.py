import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONVERSATIONS_DIR = os.path.join(BASE_DIR, "Conversations")
REFERENCE_FILE_PATH = os.path.join(CONVERSATIONS_DIR, "reference.json")

print("Reading reference.json structure...")
with open(REFERENCE_FILE_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print("Keys in reference.json:", list(data.keys()))
tasks = data.get("tasks", [])
print(f"Total tasks: {len(tasks)}")
if tasks:
    print("\nFirst task item sample:")
    print(json.dumps(tasks[0], indent=2))
    print("\nEleventh task item sample (start of the active slice 10:60):")
    print(json.dumps(tasks[10], indent=2))
