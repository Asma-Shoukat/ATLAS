# ATLAS: Adaptive Trustworthy Language-Augmented Search
### Multi-Turn Conversational Search Evaluation Report

**Department of Creative Technologies, Air University, Islamabad**  
**Course:** Information Retrieval (IR) | Session: June 2026  
**Group Members:**  
*   Asma Shoukat (241418)  
*   Amna-tuz-Zahra (241382)  

---

## 1. Problem Statement & Dataset

Traditional Retrieval-Augmented Generation (RAG) models suffer from significant performance degradation in multi-turn conversational search. ATLAS addresses three core operational issues: **(1) Contextual Pronoun Dependency & Query Drift** — follow-up queries contain pronouns ("it", "they", "them") that naive retrieval systems cannot resolve, while naively concatenating history causes vector drift; **(2) Hallucination Risk** — standard systems lack confidence filters and fabricate answers when evidence is insufficient; and **(3) Black-Box Opacity** — conventional neural pipelines provide no verifiable citations or audit trails.

ATLAS was evaluated on the **IBM Research Mt-RAG (SemEval 2026)** conversational benchmark spanning **366,479 plaintext passages** across four domains:

| Domain | Source Type | Passages |
| :--- | :--- | :--- |
| **Government (GOVT)** | NASA Space Missions, FEMA Disaster Safety & Public Policy | 49,607 |
| **Finance (FIQA)** | Financial News Analyst Reports & Q&A Forums | 61,022 |
| **Cloud (CLOUD)** | IBM Cloudant Technical Manuals & Cloud Developer Docs | 72,442 |
| **Wikipedia (CLAPNQ)** | General Knowledge Factoid Q&A & World History | 183,408 |
| **Total Corpus** | **Multi-Domain Mt-RAG Database Pool** | **366,479** |

**Preprocessing:** Source documents are sentence-chunked via regex segmenters; dense 384-dimensional vectors are generated using `all-MiniLM-L6-v2` SentenceTransformers; a FAISS Inner Product (IP) index is compiled for similarity matching. For CPU efficiency, an active local index of ~1,091 passages (250 per domain + gold reference documents from tasks 10–60 in `reference.json`) is used, achieving 0.3s retrieval latency.

---

## 2. Methodology — 7-Pillar Pipeline

**Pillars 1 & 2: Conversational Understanding & Query Rewriting.** ATLAS maintains a **Dual-Channel Context Tracker**: (1) a *User Subjects Channel* extracting noun phrases from user inputs (filtering noise words, truncating to last 3 terms), and (2) a *Proper Nouns Channel* tracking capitalized terms across all turns. When a query contains general pronouns (*"it"*, *"they"*, *"them"*, *"its"*, *"their"*) or is very short (<5 words), the system resolves the pronoun to the most recent subject (e.g., *"What causes them?"* → *"What causes wildfires?"*) or enriches short queries by appending context (e.g., *"Which is more important?"* → *"Which is more important regarding Market Cap and NAV?"*).

**Pillar 3: Dual-Channel Hybrid Retrieval.** ATLAS runs two parallel retrieval channels: *Lexical Search (BM25 Okapi)* evaluates term frequencies across the corpus and returns the top 50 keyword-matched hits; *Dense Vector Search (FAISS)* encodes the query into 384-D space and performs Inner Product search on the FAISS index, returning the top 50 semantic matches.

**Pillar 4: Reciprocal Rank Fusion (RRF).** Candidates from both channels are merged using: **RRF_Score(d) = Σ 1/(60 + Rank_m(d))**. Documents retrieved by both channels are marked `HYBRID`. The top 20 fused candidates are retained.

**Pillar 5: Neural Cross-Encoder Reranking.** The top 10 candidates are reranked using `ms-marco-MiniLM-L-6-v2`, a Cross-Encoder that processes the query and document text jointly via full cross-attention, producing a logit confidence score (range: −10.0 to +10.0).

**Pillar 6: Anti-Hallucination Decision Agent.** Four safety gates verify evidence sufficiency: (1) *Domain-Calibrated Thresholds* — logit must exceed per-domain thresholds (CLOUD: −2.0, GOVT: −1.5, CLAPNQ: −2.0, FIQA: +2.0); (2) *Score-Gap Ambiguity* — if the gap between top two candidates is <0.5 with logit <0, the query is flagged; (3) *Semantic Overlap* — at least 2 content words must overlap between query and passage (1 for ≤2-word queries); (4) *Named-Entity Consistency* — capitalized query entities must appear in the passage (2+ missing entities triggers interception). Failure in any check produces a safe fallback: *"I'm sorry, but I cannot find sufficient evidence..."*

**Pillar 7: Extractive Sliding-Window Sentence Scorer.** The approved passage is split into sentences, each scored by query-token overlap, and the contiguous 2–3 sentence window with the highest cumulative score (plus position bias toward earlier content) is extracted. This strictly extractive method guarantees zero generative hallucinations.

---

## 3. Evaluation Results

**Scenario A — GOVT Domain (Wildfire Follow-Up):**
*   **Turn 1:** *"Which state has more wildfires?"* — **APPROVED** (Confidence: 3.847, threshold: −1.5). Output: California wildfire data from 'CAL FIRE' citing 4.2 million acres burned in 2020. Citation: `2806a7d8f0775d28-14422-16441`.
*   **Turn 2:** *"What causes them?"* — Rewritten to *"What causes wildfires?"* (pronoun `"them"` resolved to `"wildfires"`). **APPROVED** (3.363). Output: lightning and human activities as primary causes, from 'Wildfire Hazard Mitigation'. Citation: `8bb77f30210c5f4b-277-2698`.

**Scenario B — FIQA Domain (Market Cap vs NAV):**
*   **Turn 1:** *"What's the difference between Market Cap and NAV?"* — **APPROVED** (7.431, threshold: 2.0). Retrieves definition of market capitalization vs. net asset value. Citation: `414940-0-474`.
*   **Turn 2:** *"Which is more important?"* — Rewritten to *"Which is more important regarding Market Cap and NAV?"*. **APPROVED** (4.652). Retrieves fund valuation comparison.

**Scenario C — Anti-Hallucination Interception:**
*   *"How do you bake a vanilla wedding cake with buttercream frosting?"* (GOVT domain) — **INTERCEPTED**. Reranker score: −10.161 (below −1.5 threshold); score gap: 0.272 (ambiguous); only 1 matching term (below 2-term minimum). Safe fallback message returned.

**Scenario D — Named-Entity Guard:**
*   *"What is the NAV of Apple?"* (FIQA domain) — **INTERCEPTED**. Confidence: −0.856 (below +2.0 threshold). Named-entity "Apple" absent from the retrieved passage discussing Amazon.

---

## 4. Limitations & Individual Contribution

**Limitations:** (1) *Extractive-Only Generation* — the sliding-window scorer cannot paraphrase or combine multiple documents; poorly structured source sentences may reduce readability. (2) *Short Context Window* — rapid topic shifts over 10+ turns may cause pronoun resolution to reference stale subjects. (3) *No Cross-Document Synthesis* — answers are drawn from a single passage; multi-document reasoning is unsupported. (4) *CPU Latency* — global-index retrieval (366,479 passages) requires GPU acceleration for real-time performance; CPU mode is optimized via active sub-indexing.

**Individual Contributions:**
*   **Asma Shoukat (241418):** Core backend search architecture — hybrid retrieval engine (BM25 + FAISS), Reciprocal Rank Fusion merger, Cross-Encoder neural reranker integration, and domain safety threshold calibration.
*   **Amna-tuz-Zahra (241382):** Dialogue state tracking and UI development — dual-channel context tracker for coreference resolution, responsive glassmorphic web interface with live pipeline telemetry, and sliding-window sentence extractor for citation highlighting.
