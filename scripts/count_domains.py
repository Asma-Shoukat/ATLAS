import pickle
import os
from collections import Counter

BASE_DIR = r"c:\Users\asmas\Downloads\IRRR"
CACHE_DIR = os.path.join(BASE_DIR, "Cache_Storage")
METADATA_PKL_PATH = os.path.join(CACHE_DIR, "master_corpus_metadata.pkl")

with open(METADATA_PKL_PATH, "rb") as f:
    metadata = pickle.load(f)

domain_tags = metadata.get("domain_tags", [])
print("Total passages:", len(domain_tags))
print("Domain counts:")
for tag, count in Counter(domain_tags).items():
    print(f"  {tag}: {count:,}")
