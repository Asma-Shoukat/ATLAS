import json
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONVERSATIONS_DIR = os.path.join(BASE_DIR, "Conversations")
REFERENCE_FILE_PATH = os.path.join(CONVERSATIONS_DIR, "reference.json")

with open(REFERENCE_FILE_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

tasks = data.get("tasks", [])

domain_queries = defaultdict(list)

for idx, task in enumerate(tasks):
    col = task.get("Collection", "")
    answerability = task.get("Answerability", [""])[0]
    
    # Identify domain from collection
    domain = None
    if "govt" in col:
        domain = "GOVT"
    elif "fiqa" in col:
        domain = "FIQA"
    elif "clapnq" in col:
        domain = "CLAPNQ"
    elif "cloud" in col or "ibmcld" in col:
        domain = "CLOUD"
        
    if domain and answerability == "ANSWERABLE":
        inputs = task.get("input", [])
        if inputs:
            last_query = inputs[-1].get("text", "")
            targets = task.get("targets", [])
            target_text = targets[0].get("text", "") if targets else ""
            domain_queries[domain].append({
                "query": last_query,
                "target": target_text[:120] + "...",
                "task_index": idx
            })

for domain, q_list in domain_queries.items():
    print(f"\n=== {domain} Domain Answerable Queries (Sample of 3) ===")
    for q in q_list[:3]:
        print(f"Query: '{q['query']}'")
        print(f"  Target: {q['target']}")
