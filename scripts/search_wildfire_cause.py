import pickle
import os

BASE_DIR = r"c:\Users\asmas\Downloads\IRRR"
CACHE_DIR = os.path.join(BASE_DIR, "Cache_Storage")
METADATA_PKL_PATH = os.path.join(CACHE_DIR, "master_corpus_metadata.pkl")

with open(METADATA_PKL_PATH, "rb") as f:
    metadata = pickle.load(f)

passages = metadata.get("passages", [])
doc_ids = metadata.get("doc_ids", [])
titles = metadata.get("titles", [])
domain_tags = metadata.get("domain_tags", [])

target_phrase = "Although wildfires occur naturally from lightning"
for idx, passage in enumerate(passages):
    if target_phrase in passage or "human activities cause most wildfires" in passage or "Wildfire Hazard Mitigation" in passage or "8bb77f30" in passage or "031693dc" in passage:
        print(f"Index: {idx}")
        print(f"ID: {doc_ids[idx]}")
        print(f"Domain: {domain_tags[idx]}")
        print(f"Title: {titles[idx]}")
        print(f"Passage: {passage[:300]}...")
        print("-" * 50)
