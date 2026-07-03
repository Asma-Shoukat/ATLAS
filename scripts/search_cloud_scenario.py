import json
import os

BASE_DIR = r"c:\Users\asmas\Downloads\IRRR"
CONVERSATIONS_DIR = os.path.join(BASE_DIR, "Conversations")
REFERENCE_FILE_PATH = os.path.join(CONVERSATIONS_DIR, "reference.json")

with open(REFERENCE_FILE_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

tasks = data.get("tasks", [])

for idx, task in enumerate(tasks):
    input_turns = task.get("input", [])
    for turn in input_turns:
        if "secure compliant deployment" in turn.get("text", "").lower() or "secure compliance deployment" in turn.get("text", "").lower():
            print(f"Task index: {idx}")
            print(f"Task ID: {task.get('task_id')}")
            print("Turns:")
            for t in input_turns:
                print(f"  {t['speaker']}: {t['text']}")
            print("Targets:")
            for t in task.get("targets", []):
                print(f"  {t['speaker']}: {t['text']}")
            print("-" * 50)
