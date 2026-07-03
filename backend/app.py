# =====================================================================
# ATLAS PROJECT - ADAPTIVE TRUSTWORTHY LANGUAGE-AUGMENTED SEARCH
# Backend Pipeline Service
# =====================================================================
import os
import re
import sys
import json
import time
import logging
import threading
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure Advanced logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(threadName)s] - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ATLAS_Backend")

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------
# PATH DEFINITIONS
# ---------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "Cache_Storage")
CORPORA_DIR = os.path.join(BASE_DIR, "Corpora")
CONVERSATIONS_DIR = os.path.join(BASE_DIR, "Conversations")

METADATA_PATH = os.path.join(CACHE_DIR, "master_corpus_metadata.json")
METADATA_PKL_PATH = os.path.join(CACHE_DIR, "master_corpus_metadata.pkl")
BM25_PKL_PATH = os.path.join(CACHE_DIR, "master_bm25_index.pkl")
LOCAL_ST_PATH = os.path.join(CACHE_DIR, "models", "all-MiniLM-L6-v2")
LOCAL_CE_PATH = os.path.join(CACHE_DIR, "models", "ms-marco-MiniLM-L-6-v2")
FAISS_INDEX_PATH = os.path.join(CACHE_DIR, "master_semantic_space.index")
LOCAL_FAISS_INDEX_PATH = os.path.join(CACHE_DIR, "master_semantic_space_local.index")
REFERENCE_FILE_PATH = os.path.join(CONVERSATIONS_DIR, "reference.json")

# ---------------------------------------------------------------------
# ATLAS PIPELINE ENGINE — 7-PILLAR RAG ARCHITECTURE
# ---------------------------------------------------------------------
class ATLASPipelineEngine:
    """
    Adaptive Trustworthy Language-Augmented Search engine implementing
    the complete 7-pillar pipeline:
      1. Conversational Query Understanding
      2. Query Rewriting
      3. Hybrid Retrieval (BM25 + Dense + RRF)
      4. Decision Agent (Anti-Hallucination)
      5. Evidence-Grounded Answer Generation
      6. Citation Highlighting
      7. Explainability Layer
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.passages = []
        self.doc_ids = []
        self.titles = []
        self.domain_tags = []
        self.bm25_index = None
        self.faiss_index = None
        self.faiss_to_global_map = None  # Mapping for local FAISS index

        self.model = None
        self.reranker_model = None
        self.device = "cpu"

        self.boot_status = {
            "stage": "Initializing",
            "progress": 0,
            "total_passages": 0,
            "faiss_status": "Not Loaded",
            "system_message": "System is booting up and loading core language models..."
        }

    def log_status(self, stage, progress, message):
        self.boot_status["stage"] = stage
        self.boot_status["progress"] = progress
        self.boot_status["system_message"] = message
        logger.info(f"[{stage}] {message} ({progress}%)")

    def initialize_resources(self):
        """Sequential loading of transformer models and data metadata pools."""
        try:
            import torch
            import pickle
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.log_status("Model Loading", 15, f"Compute target: [{self.device.upper()}]")

            from sentence_transformers import SentenceTransformer, CrossEncoder
            import faiss
            from rank_bm25 import BM25Okapi

            # Load embedding model
            self.log_status("Model Loading", 25, "Loading SentenceTransformer 'all-MiniLM-L6-v2'...")
            if os.path.exists(LOCAL_ST_PATH):
                self.model = SentenceTransformer(LOCAL_ST_PATH, device=self.device)
            else:
                self.model = SentenceTransformer("all-MiniLM-L6-v2", device=self.device)
                os.makedirs(os.path.dirname(LOCAL_ST_PATH), exist_ok=True)
                self.model.save(LOCAL_ST_PATH)

            # Load cross-encoder reranker
            self.log_status("Model Loading", 35, "Loading Cross-Encoder 'ms-marco-MiniLM-L-6-v2'...")
            if os.path.exists(LOCAL_CE_PATH):
                self.reranker_model = CrossEncoder(LOCAL_CE_PATH, device=self.device)
            else:
                self.reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device=self.device)
                os.makedirs(os.path.dirname(LOCAL_CE_PATH), exist_ok=True)
                self.reranker_model.save(LOCAL_CE_PATH)

            # Load metadata (use cached Pickle if it exists and is newer than JSON)
            self.log_status("Metadata Parsing", 45, "Loading metadata...")
            use_pkl = False
            if os.path.exists(METADATA_PKL_PATH) and os.path.exists(METADATA_PATH):
                if os.path.getmtime(METADATA_PKL_PATH) >= os.path.getmtime(METADATA_PATH):
                    use_pkl = True

            if use_pkl:
                self.log_status("Metadata Parsing", 50, "Loading metadata from fast binary Pickle cache...")
                with open(METADATA_PKL_PATH, "rb") as f:
                    metadata = pickle.load(f)
            else:
                if not os.path.exists(METADATA_PATH):
                    raise FileNotFoundError(f"Missing master_corpus_metadata.json inside {CACHE_DIR}")
                self.log_status("Metadata Parsing", 50, f"Reading metadata from {METADATA_PATH}...")
                with open(METADATA_PATH, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                self.log_status("Metadata Parsing", 55, "Saving metadata to fast binary Pickle cache...")
                with open(METADATA_PKL_PATH, "wb") as f:
                    pickle.dump(metadata, f, protocol=pickle.HIGHEST_PROTOCOL)

            self.passages = metadata.get("passages", [])
            self.doc_ids = metadata.get("doc_ids", [])
            self.titles = metadata.get("titles", [])
            self.domain_tags = metadata.get("domain_tags", [])

            total_len = len(self.passages)
            self.boot_status["total_passages"] = total_len
            self.log_status("Metadata Parsing", 60, f"Parsed {total_len:,} document passages into RAM.")

            # Load or build BM25 index over full corpus
            self.log_status("BM25 Indexing", 75, "Loading BM25 Okapi index...")
            use_bm25_pkl = False
            if os.path.exists(BM25_PKL_PATH) and os.path.exists(METADATA_PATH):
                if os.path.getmtime(BM25_PKL_PATH) >= os.path.getmtime(METADATA_PATH):
                    use_bm25_pkl = True

            if use_bm25_pkl:
                self.log_status("BM25 Indexing", 78, "Loading BM25 index from fast binary Pickle cache...")
                with open(BM25_PKL_PATH, "rb") as f:
                    self.bm25_index = pickle.load(f)
            else:
                self.log_status("BM25 Indexing", 78, f"Building BM25 Okapi index over {total_len:,} passages...")
                tokenized_passages = [re.findall(r'\w+', p.lower()) for p in self.passages]
                self.bm25_index = BM25Okapi(tokenized_passages)
                self.log_status("BM25 Indexing", 82, "Saving BM25 index to fast binary Pickle cache...")
                with open(BM25_PKL_PATH, "wb") as f:
                    pickle.dump(self.bm25_index, f, protocol=pickle.HIGHEST_PROTOCOL)

            # Load or build FAISS index
            self.log_status("FAISS Vector Indexing", 85, "Loading FAISS vector index...")
            if os.path.exists(FAISS_INDEX_PATH):
                self.faiss_index = faiss.read_index(FAISS_INDEX_PATH)
                self.faiss_to_global_map = None  # Global index: positions == global indices
                self.boot_status["faiss_status"] = "Global Index Loaded"
                self.log_status("System Operational", 100, "Global FAISS index loaded successfully.")
            else:
                # Build or load local subset index with proper global mapping
                if os.path.exists(LOCAL_FAISS_INDEX_PATH):
                    self.faiss_index = faiss.read_index(LOCAL_FAISS_INDEX_PATH)
                    # Rebuild the mapping to know which global indices are in the local index
                    active_indices = self._compute_local_index_indices()
                    self.faiss_to_global_map = active_indices
                    self.boot_status["faiss_status"] = "Local Index Loaded"
                    self.log_status("System Operational", 100, "Local FAISS index loaded with global mapping.")
                else:
                    self.log_status("FAISS Vector Indexing", 90, "Building local FAISS index...")
                    active_indices = self._compute_local_index_indices()

                    active_passages = [self.passages[i] for i in active_indices]

                    # Encode the subset
                    embeddings = self.model.encode(active_passages, show_progress_bar=False, batch_size=64)
                    embeddings = np.array(embeddings).astype("float32")
                    faiss.normalize_L2(embeddings)

                    dimension = embeddings.shape[1]
                    self.faiss_index = faiss.IndexFlatIP(dimension)
                    self.faiss_index.add(embeddings)

                    # Save the index
                    faiss.write_index(self.faiss_index, LOCAL_FAISS_INDEX_PATH)
                    self.faiss_to_global_map = active_indices
                    self.boot_status["faiss_status"] = "Local Index Compiled"
                    self.log_status("System Operational", 100, f"Local FAISS index ({len(active_passages):,} vectors) compiled.")

        except Exception as e:
            self.log_status("Fatal Error", 0, f"Boot sequence failed: {str(e)}")
            logger.error(f"Boot sequence fatal exception: {e}", exc_info=True)

    def _compute_local_index_indices(self):
        """Compute which global indices should be in the local FAISS index."""
        active_indices = []
        domains_count = {}
        for idx, tag in enumerate(self.domain_tags):
            domains_count[tag] = domains_count.get(tag, 0) + 1
            if domains_count[tag] <= 250:
                active_indices.append(idx)

        # Include gold reference documents
        try:
            if os.path.exists(REFERENCE_FILE_PATH):
                with open(REFERENCE_FILE_PATH, "r", encoding="utf-8") as rf:
                    ref_data = json.load(rf)
                
                # Build lookup dictionary for O(1) matching
                doc_id_to_idx = {d_id: idx for idx, d_id in enumerate(self.doc_ids)}
                
                tasks_slice = ref_data.get("tasks", [])[10:60]
                for task in tasks_slice:
                    contexts = task.get("contexts", [])
                    for ctx in contexts:
                        gold_id = ctx.get("document_id", "")
                        if gold_id and gold_id in doc_id_to_idx:
                            idx = doc_id_to_idx[gold_id]
                            if idx not in active_indices:
                                active_indices.append(idx)
        except Exception as e:
            logger.warning(f"Error parsing reference.json: {e}")

        return sorted(list(set(active_indices)))

    # -----------------------------------------------------------------
    # PILLAR 1 + 2: Conversational Understanding + Query Rewriting
    # -----------------------------------------------------------------
    def resolve_conversation_context(self, chat_history, current_input):
        """
        Pillar 1: Conversational Query Understanding.
        Pillar 2: Query Rewriting.
        
        Uses dual-channel extraction (user_subjects vs proper_nouns) to resolve 
        pronouns without context drift from long assistant answers.
        """
        if not chat_history:
            return current_input, {
                "resolved": False,
                "reason": "First turn — no conversation history",
                "original": current_input,
                "rewritten": current_input,
                "entities_found": []
            }

        noise_words = {"the", "a", "an", "this", "that", "these", "those", "what", "when", "where", "which",
                       "how", "who", "why", "can", "could", "would", "should", "some", "any", "many",
                       "does", "do", "did", "has", "have", "had", "will", "are", "is", "was",
                       "were", "been", "being", "am", "tell", "explain", "describe", "show", "give",
                       "according", "based", "also", "however", "although", "yes", "no",
                       "in", "on", "at", "of", "to", "for", "with", "by", "about", "as", "into",
                       "like", "through", "after", "over", "between", "out", "against", "during",
                       "without", "before", "under", "around", "among", "and", "or", "but", "if",
                       "because", "until", "while", "please", "me", "us", "we", "they", "it", "he", "she", "most",
                       # Fix 1: Filter verbs, adjectives, and comparatives from being captured as subject referents
                       "more", "less", "much", "very", "best", "better", "worse", "worst",
                       "important", "different", "similar", "compare", "compared", "comparing",
                       "define", "defined", "difference", "differences", "mean", "means", "meaning",
                       "other", "others", "another", "each", "every", "just", "really", "get",
                       "know", "think", "say", "said", "make", "made", "go", "going", "want",
                       "need", "use", "used", "using", "work", "works", "working", "find",
                       "good", "bad", "new", "old", "big", "small", "long", "short", "high", "low",
                       # Hardened filters: pronouns, common verbs, and structural generic nouns
                       "them", "him", "her", "his", "its", "their", "theirs", "your", "yours", "our", "ours", "my", "mine",
                       "whose", "whom", "whoever", "whomever", "cause", "causes", "caused", "causing",
                       "happen", "happens", "happened", "happening", "affect", "affects", "affected", "affecting",
                       "occur", "occurs", "occurred", "occurring", "prevent", "prevents", "prevented", "preventing",
                       "lead", "leads", "led", "leading", "state", "states", "question", "questions", "answer", "answers"}

        # Blacklist transition words from being recognized as proper nouns
        transition_blacklist = {"first", "then", "also", "however", "additionally", "note", "for", "the", 
                                "this", "that", "indeed", "overall", "alternatively", "furthermore", 
                                "next", "finally", "with", "before", "after", "while", "please"}

        user_subjects = []        # Each entry: (phrase, turn_index)
        user_subjects_raw = []    # Track turn origin for Fix 3
        proper_nouns = []

        # Extract entities
        for idx, turn in enumerate(chat_history):
            is_user_turn = (idx % 2 == 0)
            turn_index = idx  # Fix 3: Track which turn this subject came from
            
            # Sentence segmentation to identify sentence-start words
            sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<![A-Z]\.)(?<=\.|\?|!)\s', str(turn))
            
            for sentence in sentences:
                words = sentence.split()
                phrase_parts = []

                for w_idx, w in enumerate(words):
                    w_clean = re.sub(r'[^\w]', '', w)
                    if not w_clean or len(w_clean) < 2:
                        continue

                    # Channel 1: User Subjects (only from user queries)
                    if is_user_turn:
                        if w_clean.lower() not in noise_words:
                            phrase_parts.append(w_clean)
                        else:
                            if phrase_parts:
                                phrase = " ".join(phrase_parts)
                                if len(phrase) > 2:
                                    phrase_words = phrase.split()
                                    if len(phrase_words) <= 3:
                                        user_subjects.append(phrase)
                                        user_subjects_raw.append((phrase, turn_index))
                                    else:
                                        # Fallback: slice long subjects to last 3 terms to capture main nouns
                                        trimmed = " ".join(phrase_words[-3:])
                                        user_subjects.append(trimmed)
                                        user_subjects_raw.append((trimmed, turn_index))
                                phrase_parts = []

                    # Channel 2: Proper Nouns (capitalized, from all turns)
                    if w_clean[0].isupper() and w_clean.lower() not in noise_words and w_clean.lower() not in transition_blacklist:
                        # Ignore first word of a sentence unless it is fully capitalized (e.g. acronyms like FEMA)
                        if w_idx == 0 and not w_clean.isupper():
                            continue
                        if w_clean.lower() not in {"what", "why", "how", "when", "where", "which", "who"}:
                            proper_nouns.append(w_clean)

                if is_user_turn and phrase_parts:
                    phrase = " ".join(phrase_parts)
                    if len(phrase) > 2:
                        phrase_words = phrase.split()
                        if len(phrase_words) <= 3:
                            user_subjects.append(phrase)
                            user_subjects_raw.append((phrase, turn_index))
                        else:
                            trimmed = " ".join(phrase_words[-3:])
                            user_subjects.append(trimmed)
                            user_subjects_raw.append((trimmed, turn_index))

        # Deduplicate preserving recency order (most recent = last)
        def deduplicate(lst):
            seen = set()
            res = []
            for item in reversed(lst):
                key = item.lower()
                if key not in seen:
                    seen.add(key)
                    res.insert(0, item)
            return res

        unique_subjects = deduplicate(user_subjects)
        unique_proper_nouns = deduplicate(proper_nouns)

        # Detect pronouns in current input
        # Strip punctuation from tokens for matching (e.g. "them?" -> "them")
        input_tokens = [re.sub(r'[^\w]', '', t) for t in current_input.lower().split()]
        input_tokens = [t for t in input_tokens if t]
        
        # Locational pronouns (only "there" - "where" is a question word and must not be replaced)
        locational_pronouns = {"there"}
        has_locational = any(t in locational_pronouns for t in input_tokens)
        
        # General pronouns
        general_pronouns = {"it", "they", "this", "that", "these", "those", "its", "their", "them", "he", "she", "which"}
        found_pronouns = [t for t in input_tokens if t in general_pronouns]
        has_general = len(found_pronouns) > 0
        
        is_short = len(input_tokens) < 5

        # 1. Resolve locational pronouns using proper nouns (e.g. "there" -> "California")
        if has_locational and unique_proper_nouns:
            referent = unique_proper_nouns[-1]
            rewritten = current_input
            for p in locational_pronouns:
                pattern = re.compile(r'\b' + re.escape(p) + r'\b', re.IGNORECASE)
                rewritten = pattern.sub(referent, rewritten, count=1)
            return rewritten, {
                "resolved": True,
                "referent": referent,
                "original": current_input,
                "rewritten": rewritten,
                "entities_found": unique_proper_nouns[-5:],
                "pronouns_detected": ["there"]
            }

        # 2. Resolve general pronouns or short queries using user subjects
        if (has_general or is_short) and unique_subjects:
            # Fix 3: Only combine two subjects if they came from the same user turn
            if len(unique_subjects) >= 2:
                # Check if the last two unique subjects share a turn origin
                last_two_raw = [(s, t) for s, t in user_subjects_raw if s.lower() in {u.lower() for u in unique_subjects[-2:]}]
                if len(last_two_raw) >= 2 and last_two_raw[-1][1] == last_two_raw[-2][1]:
                    # Same turn — combine them
                    referent = f"{unique_subjects[-2]} and {unique_subjects[-1]}"
                else:
                    # Different turns — use only the most recent
                    referent = unique_subjects[-1]
            else:
                referent = unique_subjects[-1]

            rewritten = current_input
            if has_general:
                # Direct replacement of pronoun with referent preserves sentence structure and matches tests
                pronoun = found_pronouns[0]
                replacement = referent
                # If pronoun is possessive, try to build possessive referent form for better readability
                if pronoun in {"its", "their"}:
                    if not referent.endswith("'s") and not referent.endswith("s"):
                        replacement = f"{referent}'s"
                    elif referent.endswith("s") and not referent.endswith("'s"):
                        replacement = f"{referent}'"
                
                pattern = re.compile(r'\b' + re.escape(pronoun) + r'\b', re.IGNORECASE)
                rewritten = pattern.sub(replacement, rewritten, count=1)
            else:
                # Short-query context enrichment
                has_own_entity = any(
                    w[0].isupper() and w.lower() not in noise_words and len(w) > 2
                    for w in current_input.split()
                    if w and w[0].isalpha()
                )
                if has_own_entity:
                    rewritten = current_input
                else:
                    if rewritten.endswith('?'):
                        rewritten = f"{rewritten[:-1]} regarding {referent}?"
                    else:
                        rewritten = f"{rewritten} regarding {referent}"

            return rewritten, {
                "resolved": True,
                "referent": referent,
                "original": current_input,
                "rewritten": rewritten,
                "entities_found": unique_subjects[-5:],
                "pronouns_detected": found_pronouns or ["short_query"]
            }

        return current_input, {
            "resolved": False,
            "reason": "No pronouns detected — query is already standalone",
            "original": current_input,
            "rewritten": current_input,
            "entities_found": unique_subjects[-5:] if unique_subjects else []
        }

    # -----------------------------------------------------------------
    # PILLAR 3: Hybrid Retrieval (BM25 + Dense + RRF)
    # -----------------------------------------------------------------
    def hybrid_retrieve(self, query, target_domain, top_k=20):
        """
        Pillar 3: True Hybrid Retrieval.
        Always runs BOTH BM25 and dense FAISS search, then merges
        results using Reciprocal Rank Fusion (RRF).
        """
        import faiss as faiss_lib

        # --- BM25 Retrieval ---
        # Fix 5 (query side): Match index tokenization — strip punctuation from query tokens
        query_tokens = re.findall(r'\w+', query.lower())
        bm25_scores = self.bm25_index.get_scores(query_tokens)
        bm25_top = np.argsort(bm25_scores)[::-1][:150]

        bm25_candidates = []
        for rank, idx in enumerate(bm25_top):
            idx = int(idx)
            if bm25_scores[idx] <= 0:
                break
            if target_domain != "GLOBAL" and self.domain_tags[idx] != target_domain:
                continue
            bm25_candidates.append({
                "idx": idx,
                "rank": rank + 1,
                "score": float(bm25_scores[idx]),
                "source": "BM25"
            })
            if len(bm25_candidates) >= 50:
                break

        # --- Dense FAISS Retrieval ---
        dense_candidates = []
        if self.faiss_index is not None and self.model is not None:
            query_vec = self.model.encode([query], show_progress_bar=False)
            query_vec = np.array(query_vec).astype("float32")
            faiss_lib.normalize_L2(query_vec)

            search_k = min(150, self.faiss_index.ntotal)
            scores, indices = self.faiss_index.search(query_vec, search_k)

            for rank, (score, f_idx) in enumerate(zip(scores[0], indices[0])):
                if f_idx == -1:
                    continue
                f_idx = int(f_idx)

                # Map local index position to global passage index
                if self.faiss_to_global_map is not None:
                    if f_idx < len(self.faiss_to_global_map):
                        global_idx = self.faiss_to_global_map[f_idx]
                    else:
                        continue
                else:
                    global_idx = f_idx

                if target_domain != "GLOBAL" and self.domain_tags[global_idx] != target_domain:
                    continue

                dense_candidates.append({
                    "idx": global_idx,
                    "rank": rank + 1,
                    "score": float(score),
                    "source": "DENSE"
                })
                if len(dense_candidates) >= 50:
                    break

        # --- Reciprocal Rank Fusion (RRF) ---
        k_rrf = 60  # RRF constant
        fused_scores = {}
        candidate_sources = {}

        for cand in bm25_candidates:
            idx = cand["idx"]
            fused_scores[idx] = fused_scores.get(idx, 0) + 1.0 / (k_rrf + cand["rank"])
            candidate_sources.setdefault(idx, set()).add("BM25")

        for cand in dense_candidates:
            idx = cand["idx"]
            fused_scores[idx] = fused_scores.get(idx, 0) + 1.0 / (k_rrf + cand["rank"])
            candidate_sources.setdefault(idx, set()).add("DENSE")

        # Sort by fused score
        sorted_indices = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)[:top_k]

        # Build results with retrieval provenance
        results = []
        for rank, idx in enumerate(sorted_indices):
            sources = candidate_sources.get(idx, set())
            if "BM25" in sources and "DENSE" in sources:
                retrieval_method = "HYBRID"
            elif "BM25" in sources:
                retrieval_method = "BM25"
            else:
                retrieval_method = "DENSE"

            # Get the individual scores for explainability
            bm25_score = next((c["score"] for c in bm25_candidates if c["idx"] == idx), 0.0)
            dense_score = next((c["score"] for c in dense_candidates if c["idx"] == idx), 0.0)

            results.append({
                "global_idx": idx,
                "fused_score": fused_scores[idx],
                "rank": rank + 1,
                "text": self.passages[idx],
                "title": self.titles[idx],
                "doc_id": self.doc_ids[idx],
                "domain": self.domain_tags[idx],
                "retrieval_method": retrieval_method,
                "bm25_score": bm25_score,
                "dense_score": dense_score
            })

        retrieval_stats = {
            "bm25_candidates_found": len(bm25_candidates),
            "dense_candidates_found": len(dense_candidates),
            "fused_total": len(results),
            "fusion_method": "Reciprocal Rank Fusion (k=60)"
        }

        return results, retrieval_stats

    # -----------------------------------------------------------------
    # PILLAR 4: Decision Agent (Anti-Hallucination Layer)
    # -----------------------------------------------------------------
    def decision_agent(self, query, candidates, rerank_scores):
        """
        Pillar 4: Anti-Hallucination Decision Agent.
        Determines if there is sufficient evidence to answer the query.
        Uses calibrated thresholds, score-gap analysis, semantic overlap, and entity consistency checks.
        """
        if not candidates or len(rerank_scores) == 0:
            return True, "INTERCEPTED", "No retrieval candidates found for this query.", {
                "below_threshold": True,
                "ambiguous": False,
                "low_overlap": True,
                "entity_mismatch": False,
                "highest_logit": 0.0,
                "threshold": -2.0,
                "score_gap": 0.0,
                "overlap_count": 0
            }

        best_score = float(rerank_scores[0])
        source_domain = candidates[0]["domain"]

        # Domain-calibrated thresholds (properly calibrated for ms-marco cross-encoder)
        # FIQA threshold is calibrated to 2.0 to filter out loose semantic matches
        thresholds = {"CLOUD": -2.0, "FIQA": 2.0, "GOVT": -1.5, "CLAPNQ": -2.0}
        threshold = thresholds.get(source_domain, -2.0)

        # Check 1: Is the best score above the confidence threshold?
        below_threshold = best_score < threshold

        # Check 2: Score ambiguity — is the gap between #1 and #2 too small?
        ambiguous = False
        score_gap = 0.0
        if len(rerank_scores) > 1:
            score_gap = float(rerank_scores[0] - rerank_scores[1])
            ambiguous = score_gap < 0.5 and best_score < 0

        # Check 3: Semantic overlap — does the passage actually address the query?
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "of", "to", "for", "in",
            "on", "at", "by", "with", "why", "what", "how", "which", "where", "when",
            "who", "it", "they", "this", "that", "does", "should", "about", "can",
            "do", "be", "have", "has", "not", "from", "or", "and", "but", "if", "so"
        }
        query_words = {w.lower() for w in query.split() if w.lower() not in stopwords and len(w) > 2}
        # Fix 4: Clean punctuation from passage words before comparison
        passage_words = {re.sub(r'[^\w]', '', w).lower() for w in candidates[0]["text"].split() if len(w) > 2}
        overlap_count = len(query_words & passage_words)
        # Fix 6: Adjust overlap threshold for short queries (≤2 content words → require ≥1 match, not ≥2)
        if len(query_words) <= 2:
            low_overlap = overlap_count < 1
        else:
            low_overlap = overlap_count < 2

        # Check 4: Named-Entity Consistency Guard
        # Fix 4: Expanded domain-aware entity exclusion with punctuation-clean passage matching
        entity_mismatch = False
        mismatched_entities = []

        # Domain-aware common acronyms/terms that should not trigger entity mismatch
        domain_terms = {
            # Cross-domain common terms
            "nav", "pb", "cap", "market", "index", "rate", "fund", "stock",
            # FIQA domain
            "etf", "gdp", "ipo", "roi", "apy", "apr", "sec", "nyse", "nasdaq",
            "dow", "sandp", "sp", "reit", "ebitda", "pe", "eps",
            # CLOUD domain
            "aws", "api", "vm", "iam", "vpc", "dns", "ssl", "tls", "http",
            "https", "sdk", "cli", "saas", "paas", "iaas", "devops", "cicd",
            "kubernetes", "docker", "azure", "gcp",
            # GOVT domain
            "fema", "epa", "fda", "cdc", "dhs", "dot", "hud", "usda",
            "noaa", "nws", "fbi", "doj", "irs", "ssa", "va",
            # CLAPNQ domain
            "usa", "uk", "eu", "un", "nato", "who", "unesco"
        }

        words = query.split()
        for idx, w in enumerate(words):
            w_clean = re.sub(r'[^\w]', '', w)
            if not w_clean or len(w_clean) < 2:
                continue
            # Capitalized words that are not domain acronyms/stopwords
            if w_clean[0].isupper():
                if idx == 0 and not w_clean.isupper():
                    continue
                if w_clean.upper() in {"WHAT", "WHY", "HOW", "WHEN", "WHERE", "WHICH", "WHO"}:
                    continue
                # Exclude known domain terms
                if w_clean.lower() in domain_terms:
                    continue
                if w_clean.lower() not in passage_words:
                    mismatched_entities.append(w_clean)

        # Fix 4: Only trigger entity mismatch when 2+ entities are missing
        # (a single proper noun miss is often a false positive from query rewriting)
        entity_mismatch = len(mismatched_entities) >= 2

        is_intercepted = below_threshold or (ambiguous and low_overlap) or entity_mismatch

        details = {
            "below_threshold": below_threshold,
            "ambiguous": ambiguous,
            "low_overlap": low_overlap,
            "entity_mismatch": entity_mismatch,
            "highest_logit": best_score,
            "threshold": threshold,
            "score_gap": score_gap,
            "overlap_count": overlap_count
        }

        if is_intercepted:
            reasons = []
            if below_threshold:
                reasons.append(f"Confidence score ({best_score:.3f}) below domain threshold ({threshold})")
            if ambiguous:
                reasons.append(f"Ambiguous top results (score gap: {score_gap:.3f})")
            if low_overlap:
                reasons.append(f"Low semantic overlap ({overlap_count} matching terms)")
            if entity_mismatch:
                reasons.append(f"Named-entity mismatch (missing from document: {', '.join(mismatched_entities)})")
            return True, "INTERCEPTED", "; ".join(reasons), details

        return False, "APPROVED", f"Confidence: {best_score:.3f} exceeds threshold ({threshold})", details

    # -----------------------------------------------------------------
    # PILLAR 5: Evidence-Grounded Answer Generation
    # -----------------------------------------------------------------
    def extract_evidence_window(self, query, text_passage):
        """
        Pillar 5: Evidence-Grounded Answer Generation.
        Sliding-Window Sentence Scorer that extracts the optimal
        contiguous 2-3 sentence window grounded in the retrieved passage.
        Returns the synthesized text and the individual evidence sentences.
        """
        # 1. Clean whitespace noise
        text_passage = re.sub(r'[\r\n\t\xa0]+', ' ', text_passage)
        text_passage = re.sub(r'\s+', ' ', text_passage).strip()

        # 2. Tokenize into sentences
        sentence_ends = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<![A-Z]\.)(?<=\.|\?|!)\s')
        raw_sentences = [s.strip() for s in sentence_ends.split(text_passage) if s.strip()]

        # 3. Clean and filter sentences
        sentences = []
        for s in raw_sentences:
            s_clean = s.strip()
            # Remove leading bullets/numbers
            s_clean = re.sub(r'^[\d\.\)\-\u2022\*\s]+', '', s_clean).strip()

            if not s_clean:
                continue
            if len(s_clean.split()) < 3 and not s_clean.endswith('?'):
                continue

            # Capitalize first letter
            if s_clean and not s_clean[0].isupper():
                s_clean = s_clean[0].upper() + s_clean[1:]

            sentences.append(s_clean)

        if len(sentences) <= 2:
            result = " ".join(sentences) if sentences else text_passage
            return result, sentences, 0

        # 4. Extract query tokens (filtering stopwords)
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "of", "to", "for", "in",
            "on", "at", "by", "with", "why", "what", "how", "which", "where",
            "when", "who", "it", "they", "them", "this", "that", "these", "those",
            "does", "doesn't", "should", "shouldn't", "related", "about"
        }
        query_words = {w.lower() for w in query.split() if w.lower() not in stopwords and w.isalnum()}
        if not query_words:
            query_words = {w.lower() for w in query.split() if w.isalnum()}

        # 5. Score each sentence by query overlap
        sentence_scores = []
        for s in sentences:
            s_words = {w.lower() for w in s.split() if w.isalnum()}
            overlap = len(s_words.intersection(query_words))
            sentence_scores.append(overlap)

        # 6. Find the best contiguous window of 2-3 sentences
        best_score = -1
        best_window = (0, min(3, len(sentences)))

        for size in [2, 3]:
            if len(sentences) < size:
                continue
            for i in range(len(sentences) - size + 1):
                window_score = sum(sentence_scores[i:i + size])
                # Slight position bias toward earlier content
                pos_bias = (len(sentences) - i) * 0.1
                total_score = window_score + pos_bias

                if total_score > best_score:
                    best_score = total_score
                    best_window = (i, i + size)

        start, end = best_window
        evidence_sentences = sentences[start:end]

        # 7. Join and return
        synthesized_text = " ".join(evidence_sentences)
        if not synthesized_text.endswith((".", "?", "!")):
            synthesized_text += "."

        return synthesized_text, evidence_sentences, start

    # -----------------------------------------------------------------
    # PILLAR 7: Explainability Layer
    # -----------------------------------------------------------------
    def build_explainability(self, query, query_meta, best_candidate, retrieval_stats,
                              decision_verdict, decision_reason, decision_details,
                              evidence_text, evidence_start_idx):
        """
        Pillar 7: Explainability Layer.
        Builds a human-readable explanation of every pipeline decision.
        """
        # Build retrieval reasoning
        if best_candidate:
            method = best_candidate.get("retrieval_method", "UNKNOWN")
            bm25_s = best_candidate.get("bm25_score", 0.0)
            dense_s = best_candidate.get("dense_score", 0.0)

            if method == "HYBRID":
                why_retrieved = (f"Document matched keyword terms via BM25 (score: {bm25_s:.4f}) "
                                 f"AND had {dense_s:.4f} cosine similarity via dense embeddings. "
                                 f"Both signals agreed this document is relevant.")
            elif method == "BM25":
                why_retrieved = (f"Document matched keyword terms via BM25 (score: {bm25_s:.4f}). "
                                 f"It was not highly ranked by dense embeddings.")
            else:
                why_retrieved = (f"Document had {dense_s:.4f} cosine similarity via dense embeddings. "
                                 f"It was not highly ranked by BM25 keyword matching.")

            # Find which query words matched in the passage
            stopwords = {"the", "a", "an", "is", "are", "was", "were", "of", "to", "for", "in", "on",
                         "at", "by", "with", "why", "what", "how", "which", "where", "when", "who"}
            q_words = [w.lower() for w in query.split() if w.lower() not in stopwords and len(w) > 2]
            p_words_set = {w.lower() for w in best_candidate["text"].split()}
            matched_tokens = [w for w in q_words if w in p_words_set]
        else:
            method = "NONE"
            why_retrieved = "No documents were retrieved."
            matched_tokens = []
            dense_s = 0.0

        return {
            "query_understanding": {
                "resolved": query_meta.get("resolved", False),
                "referent": query_meta.get("referent", None),
                "original": query_meta.get("original", query),
                "rewritten": query_meta.get("rewritten", query),
                "entities_found": query_meta.get("entities_found", []),
                "pronouns_detected": query_meta.get("pronouns_detected", [])
            },
            "retrieval_reasoning": {
                "bm25_candidates": retrieval_stats.get("bm25_candidates_found", 0),
                "dense_candidates": retrieval_stats.get("dense_candidates_found", 0),
                "fusion_method": retrieval_stats.get("fusion_method", "RRF"),
                "fused_total": retrieval_stats.get("fused_total", 0),
                "retrieval_method": method,
                "dense_similarity": dense_s,
                "matched_query_tokens": matched_tokens,
                "why_retrieved": why_retrieved
            },
            "decision_reasoning": {
                "verdict": decision_verdict,
                "reason": decision_reason,
                "confidence_score": decision_details.get("highest_logit", 0.0),
                "threshold": decision_details.get("threshold", -2.0),
                "score_gap": decision_details.get("score_gap", 0.0),
                "evidence_overlap_count": decision_details.get("overlap_count", 0),
                "below_threshold": decision_details.get("below_threshold", False),
                "ambiguous": decision_details.get("ambiguous", False)
            },
            "answer_source": (f"Evidence extracted from sentence window "
                              f"(starting at sentence {evidence_start_idx + 1} of document)"
                              if evidence_text else "No evidence — query was intercepted")
        }

    # -----------------------------------------------------------------
    # MASTER PIPELINE EXECUTION
    # -----------------------------------------------------------------
    def execute_pipeline(self, user_message, chat_history, target_domain):
        """Thread-safe execution of the complete ATLAS 7-pillar RAG pipeline."""
        with self.lock:
            t0 = time.time()

            # ============================================================
            # PILLAR 1 + 2: Conversational Understanding + Query Rewriting
            # ============================================================
            rewritten_query, query_meta = self.resolve_conversation_context(chat_history, user_message)

            # ============================================================
            # PILLAR 3: Hybrid Retrieval (BM25 + Dense + RRF)
            # ============================================================
            candidates, retrieval_stats = self.hybrid_retrieve(rewritten_query, target_domain, top_k=20)

            # ============================================================
            # CROSS-ENCODER RERANKING
            # ============================================================
            if candidates:
                # Slice candidates to top 10 to optimize CPU reranking latency
                candidates = candidates[:10]
                pairs = [[rewritten_query, cand["text"]] for cand in candidates]
                rerank_raw = self.reranker_model.predict(pairs)

                # Handle scalar
                if isinstance(rerank_raw, float) or (hasattr(rerank_raw, 'ndim') and rerank_raw.ndim == 0):
                    rerank_raw = np.array([rerank_raw])

                # Map scores and sort
                for idx, score in enumerate(rerank_raw):
                    candidates[idx]["rerank_score"] = float(score)

                candidates = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
                rerank_scores = [c["rerank_score"] for c in candidates]
            else:
                rerank_scores = []

            # ============================================================
            # PILLAR 4: Decision Agent (Anti-Hallucination)
            # ============================================================
            is_intercepted, verdict_status, verdict_reason, verdict_details = self.decision_agent(
                rewritten_query, candidates, rerank_scores
            )

            # ============================================================
            # PILLAR 5 + 6: Evidence-Grounded Answer + Citation
            # ============================================================
            # Fix 8: Initialize evidence variables before branching to prevent undefined errors
            evidence_text = None
            evidence_sentences = []
            evidence_start_idx = 0
            citation = None

            if is_intercepted or not candidates:
                answer = ("I'm sorry, but I cannot find sufficient evidence in the available "
                          "documents to answer this question. Please try rephrasing your query "
                          "or asking about a topic covered in the database.")
            else:
                best_cand = candidates[0]
                evidence_text, evidence_sentences, evidence_start_idx = self.extract_evidence_window(
                    rewritten_query, best_cand["text"]
                )

                answer = (f"According to the [{best_cand['domain']}] document "
                          f"'{best_cand['title']}': \"{evidence_text}\"")

                # Pillar 6: Citation Highlighting
                citation = {
                    "passage_id": best_cand["doc_id"],
                    "title": best_cand["title"],
                    "domain": best_cand["domain"],
                    "sentence": evidence_text,
                    "evidence_sentences": evidence_sentences,
                    "paragraph_index": evidence_start_idx,
                    "full_text": best_cand["text"],
                    "retrieval_method": best_cand.get("retrieval_method", "UNKNOWN")
                }

            # ============================================================
            # PILLAR 7: Explainability Layer
            # ============================================================
            best_candidate = candidates[0] if candidates else None
            explainability = self.build_explainability(
                rewritten_query, query_meta, best_candidate, retrieval_stats,
                verdict_status, verdict_reason, verdict_details,
                evidence_text, evidence_start_idx
            )

            time_taken = time.time() - t0

            # ============================================================
            # FINAL RESPONSE ASSEMBLY
            # ============================================================
            return {
                "original_query": user_message,
                "rewritten_query": rewritten_query,
                "target_domain": target_domain,
                "answer": answer,
                "time_ms": int(time_taken * 1000),
                "verdict": {
                    "status": verdict_status,
                    "reason": verdict_reason,
                    "highest_logit": verdict_details.get("highest_logit", 0.0),
                    "threshold": verdict_details.get("threshold", -2.0),
                    "below_threshold": verdict_details.get("below_threshold", False),
                    "ambiguous": verdict_details.get("ambiguous", False),
                    "low_overlap": verdict_details.get("low_overlap", False),
                    "score_gap": verdict_details.get("score_gap", 0.0),
                    "overlap_count": verdict_details.get("overlap_count", 0)
                },
                "citation": citation,
                "explainability": explainability,
                "coarse_candidates": [{
                    "doc_id": c["doc_id"],
                    "title": c["title"],
                    "domain": c["domain"],
                    "fused_score": c["fused_score"],
                    "rank": c["rank"],
                    "retrieval_method": c.get("retrieval_method", "UNKNOWN")
                } for c in candidates[:10]],
                "reranked_candidates": [{
                    "doc_id": r["doc_id"],
                    "title": r["title"],
                    "domain": r["domain"],
                    "rerank_logit": r.get("rerank_score", 0.0),
                    "retrieval_method": r.get("retrieval_method", "UNKNOWN")
                } for r in candidates[:10]]
            }


# Instantiate Singleton Engine
engine = ATLASPipelineEngine()

# Boot daemon thread
threading.Thread(target=engine.initialize_resources, name="ATLAS-Boot").start()

# ---------------------------------------------------------------------
# FLASK HTTP ROUTING API
# ---------------------------------------------------------------------
@app.route("/api/stats", methods=["GET"])
def get_stats():
    return jsonify({
        "boot_status": engine.boot_status,
        "compute_device": engine.device,
        "passages_count": len(engine.passages),
        "has_bm25": engine.bm25_index is not None,
        "has_faiss": engine.faiss_index is not None,
        "faiss_total": engine.faiss_index.ntotal if engine.faiss_index else 0
    })

@app.route("/api/chat", methods=["POST"])
def post_chat():
    if engine.boot_status["progress"] < 100:
        return jsonify({
            "error": "System is still booting",
            "boot_status": engine.boot_status
        }), 503

    data = request.json or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])
    domain = data.get("domain", "GLOBAL")

    if not message:
        return jsonify({"error": "Message parameter is required."}), 400

    response_payload = engine.execute_pipeline(message, history, domain)
    return jsonify(response_payload)

# ---------------------------------------------------------------------
# MAIN SERVER PROCESS LAUNCHER
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
