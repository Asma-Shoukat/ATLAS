import pickle
import os
import json

BASE_DIR = r"c:\Users\asmas\Downloads\IRRR"
CACHE_DIR = os.path.join(BASE_DIR, "Cache_Storage")
METADATA_PKL_PATH = os.path.join(CACHE_DIR, "master_corpus_metadata.pkl")

with open(METADATA_PKL_PATH, "rb") as f:
    metadata = pickle.load(f)

passages = metadata.get("passages", [])
doc_ids = metadata.get("doc_ids", [])
titles = metadata.get("titles", [])
domain_tags = metadata.get("domain_tags", [])

targets = ["8bb77f30210c5f4b-277-2698", "031693dc1490c39e-4593-6990"]
for target in targets:
    if target in doc_ids:
        idx = doc_ids.index(target)
        print(f"ID: {target}")
        print(f"  Index: {idx}")
        print(f"  Domain: {domain_tags[idx]}")
        print(f"  Title: {titles[idx]}")
        print(f"  Passage: {passages[idx][:300]}...")
    else:
        # Search by prefix
        found = False
        for idx, d_id in enumerate(doc_ids):
            if d_id.startswith(target[:8]):
                print(f"Prefix Match ID: {d_id}")
                print(f"  Index: {idx}")
                print(f"  Domain: {domain_tags[idx]}")
                print(f"  Title: {titles[idx]}")
                print(f"  Passage: {passages[idx][:300]}...")
                found = True
                break
        if not found:
            print(f"ID {target} not found anywhere in metadata.")
