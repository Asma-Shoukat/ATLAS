# ATLAS: Adaptive Trustworthy Language-Augmented Search
An Advanced 7-Pillar Hybrid RAG System for Multi-Domain Information Retrieval

---

## 📂 Project Directory Hierarchy

The project has been cleaned and reorganized into a clean, modular structure. Redundant scripts have been moved to logical subdirectories:

```
ATLAS/
├── Cache_Storage/          # Fast binary search indices & localized transformer model weight caches
│   ├── models/             # Local offline copies of HuggingFace models (SentenceTransformer & CrossEncoder)
│   ├── master_bm25_index.pkl
│   ├── master_corpus_metadata.json
│   ├── master_corpus_metadata.pkl
│   └── master_semantic_space_local.index
├── Conversations/          # Conversational evaluation datasets
│   └── reference.json      # Gold-standard context-evaluation benchmark dataset
├── Corpora/                # Multi-domain raw document corpora in JSONL format
│   ├── clapnq.jsonl        # Open-domain Q&A documents
│   ├── cloud.jsonl         # IBM Cloud documentation
│   ├── fiqa.jsonl          # Financial Q&A documents
│   └── govt.jsonl          # US FEMA & government guidelines
├── backend/                # Flask REST API implementation
│   └── app.py              # Main 7-pillar engine pipeline server
├── frontend/               # Glassmorphic premium UI interface
│   ├── index.html          # Console dashboard with 7-pillar auditor telemetry
│   ├── style.css           # Premium styling & radial animations
│   ├── app.js              # State management & typewriter engine
│   └── glowing_orb.png     # UI assets
├── docs/                   # Documentation & Academic materials
│   ├── ATLAS_Academic_Report.md   # Academic evaluation report (Markdown source)
│   ├── ATLAS_Academic_Report.pdf  # Academic evaluation report (PDF render)
│   ├── echo 1.ipynb        # Exploration notebook
│   ├── testing ques.txt    # Query rewriting test cases & expected outputs
│   └── README.md           # This project guide
├── scripts/                # Diagnostic & generation utility scripts
│   ├── dump_slides.py      # Extracts all PPTX slide text to a file
│   ├── extract_sample_queries.py  # Samples benchmark queries from reference.json
│   ├── generate_pdf.py     # Generates the academic report PDF from code
│   ├── inspect_pptx.py     # Quick PPTX slide content inspector
│   ├── inspect_reference.py  # Inspects reference.json structure
│   ├── inspect_task_13.py  # Inspects specific task entry in reference data
│   ├── test_xml.py         # PPTX XML structure test utility
│   └── update_slides.py    # PPTX slide content update utility
├── tests/                  # Stress-testing scripts and validation benchmark runs
│   ├── test_search.py      # Basic multi-domain retrieval test
│   ├── test_4pillars_wildfire.py # 4-pillar conversational context test
│   ├── test_drifts.py      # Conversation drift stress test
│   └── test_fiqa_nav.py    # Specific financial query test
├── ATLAS_presentation.pptx # 15-slide academic presentation
├── launcher.py             # Python-based multi-process orchestrator
├── run.bat                 # One-click Windows startup batch script
├── ECHO_Launcher.spec      # PyInstaller spec configuration
└── ECHO_Launcher.exe       # Precompiled executable launcher
```

---

## 🔎 1. Information Retrieval (IR) Relevance

This project is a state-of-the-art **Retrieval-Augmented Generation (RAG)** system that addresses core challenges in Information Retrieval:
*   **Lexical vs. Semantic Retrieval Gap**: Standard search engines use either keyword matching (which misses synonyms) or vector embeddings (which miss exact matches like serial numbers). ATLAS implements **Hybrid Search** with both.
*   **Conversational Search & Query Reformulation**: Resolves pronouns and coreferences dynamically so follow-up queries like *"What causes them?"* are successfully retrieved in context.
*   **Verification & Hallucination Guardrails**: Evaluates if the retrieved information contains sufficient evidence before generating a response, preventing hallucinated answers.

---

## ⚙️ 2. Retrieval Method & Technical Justification

ATLAS uses a high-performance **2-Stage Hybrid Retrieval Pipeline** with **Rank Fusion**:

```
[User Query] ──> [Query Rewriter]
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
  [Lexical Search]            [Dense Search]
    (BM25 Okapi)           (FAISS Vector Index)
         │                           │
         └─────────────┬─────────────┘
                       ▼
         [Reciprocal Rank Fusion (RRF)]
                       │
                       ▼ (Top Candidates)
         [Neural Cross-Encoder Reranking]
                    (MS-MARCO)
                       │
                       ▼
          [Decision Agent Safeguard]
```

### Technical Details & Justifications:

1.  **Stage 1 - Lexical Retrieval (BM25 Okapi)**:
    *   **How it works**: Uses the BM25 algorithm to score document relevance based on term frequency (TF), inverse document frequency (IDF), and document length normalization.
    *   **Justification**: Extremely efficient at matching exact keywords, numbers, acronyms (e.g. "FEMA", "NAV", "AWS VPC") which dense models sometimes overlook.
2.  **Stage 1 - Dense Retrieval (SentenceTransformers + FAISS)**:
    *   **How it works**: Encodes text into 384-dimensional dense vectors using the `all-MiniLM-L6-v2` transformer model. A **FAISS (Facebook AI Similarity Search)** index computes cosine similarities between query and document vectors.
    *   **Justification**: Captures semantic meaning, synonyms, and conceptual matches even if there is no keyword overlap.
3.  **Reciprocal Rank Fusion (RRF)**:
    *   **How it works**: Combines the rank positions of documents from both BM25 and Dense channels using the formula:
        $$RRF(d) = \sum_{m \in M} \frac{1}{k + \text{rank}_m(d)}$$ (where $k=60$).
    *   **Justification**: Merging ranks rather than raw scores avoids scale mismatches and ensures the top list has high-quality keyword and semantic relevance.
4.  **Stage 2 - Neural Cross-Encoder Reranking (`ms-marco-MiniLM-L-6-v2`)**:
    *   **How it works**: Feeds the top RRF candidates directly into a Cross-Encoder transformer. The query and document are processed together, capturing full token-to-token attention.
    *   **Justification**: Offers much higher accuracy than bi-encoders because it doesn't represent text independently. This reranks documents to place the most factually precise paragraph at Rank #1.

---

## 📊 3. Ranked Demonstration Queries

The system was evaluated against test queries across multiple domains. The results of the ranked retrieval and neural confidence scores are as follows:

### Query 1: `"Which state has more wildfires?"` (Domain: `GOVT`)
*   **Retrieval Method**: `HYBRID` (Lexical BM25 rank merged with Dense Vector rank via RRF).
*   **Neural Reranker Confidence Score**: `3.847` (Exceeds GOVT threshold of `-1.5` ──> **APPROVED**).
*   **Ranked Output Passage**:
    > **Title**: *2020 Fire Season Incident Archive | CAL FIRE*
    > **Document ID**: `2806a7d8f0775d28-14422-16441`
    > **Synthesized Evidence Window**: *"As of the end of the year, nearly 10,000 fires had burned over 4.2 million acres, more than 4% of the state's roughly 100 million acres of land, making 2020 the largest wildfire season recorded in California's modern history. California's August Complex fire has been described as the first 'gigafire' as the area burned exceeded 1 million acres."*

### Query 2: `"What causes most lightning and natural wildfires?"` (Domain: `CLAPNQ`)
*   **Retrieval Method**: `HYBRID`
*   **Neural Reranker Confidence Score**: `2.926` (Exceeds CLAPNQ threshold of `-2.0` ──> **APPROVED**).
*   **Ranked Output Passage**:
    > **Title**: *Thunderstorm*
    > **Document ID**: `833974015_22021-22735-0-714`
    > **Synthesized Evidence Window**: *"Under a regime of low precipitation ( LP ) thunderstorms , where little precipitation is present , rainfall can not prevent fires from starting when vegetation is dry as lightning produces a concentrated amount of extreme heat."*

---

## ⚠️ 4. Failure Cases & Interception Analysis

To prevent hallucinated answers, the system uses a **Decision Agent** which serves as an anti-hallucination guardrail.

### Failure Case 1: Out-of-Domain Query
*   **Query**: `"How do you bake a vanilla wedding cake with buttercream frosting?"` (Domain: `GOVT`)
*   **Expected Behavior**: The system should refuse to answer instead of hallucinating.
*   **Actual System Behavior**: **INTERCEPTED**
*   **Technical Reason**:
    *   The best retrieved document in the GOVT database had a Cross-Encoder Reranker confidence score of **`-10.161`**, which falls far below the domain threshold of **`-1.5`**.
    *   The Decision Agent computed a semantic keyword overlap of only **`1 matching term`** (violating the minimum overlap constraint of 2 terms).
    *   As a result, the query was safely intercepted, outputting a trustworthy fallback response: *"I'm sorry, but I cannot find sufficient evidence in the available documents..."*

### Failure Case 2: Incomplete Evidence (Conceptual Mismatch)
*   **Query**: `"Why doesn't the government prevent people from living in areas prone to flooding?"` (Domain: `FIQA`)
*   **Actual System Behavior**: **INTERCEPTED**
*   **Technical Reason**:
    *   The best candidate received a rerank score of **`-3.330`**, which is below the highly calibrated FIQA domain threshold of **`2.0`**.
    *   While the system successfully retrieved documents discussing floods and government insurance, they did not contain direct evidence explaining the *philosophical or legislative reasoning* of why the government doesn't ban citizens from living there.
    *   The high threshold prevented the system from stretching loose contexts into a false answer.

---

## 🛠️ 5. Installation and Setup Instructions

Follow these step-by-step instructions to set up the project locally on your machine.

### Prerequisites
1.  **Python**: Ensure Python 3.10 or 3.11 is installed on your machine.
2.  **OS**: Windows (tested with PowerShell/CMD commands).

### Step 1: Clone or Open the Directory
Open your terminal and navigate to the project directory:
```bash
cd c:\Users\asmas\Downloads\IRRR
```

### Step 2: Set up a Virtual Environment
Create a Python virtual environment to isolate the project dependencies:
```bash
python -m venv venv
```

### Step 3: Activate the Virtual Environment
*   **PowerShell**:
    ```powershell
    .\venv\Scripts\Activate.ps1
    ```
*   **Command Prompt**:
    ```cmd
    .\venv\Scripts\activate.bat
    ```

### Step 4: Install Dependencies
Install the required packages. The project depends on Flask, PyTorch, SentenceTransformers, FAISS, and Rank-BM25:
```bash
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu
pip install SentenceTransformers==2.5.1 faiss-cpu==1.7.4 rank-bm25==0.2.2 Flask==3.0.2 flask-cors==4.0.0 numpy==1.26.4
```
*(Note: Using CPU-specific PyTorch limits disk space and speeds up installation)*

---

## 🚀 6. Running the Project

### One-Click execution (Recommended)
Double-click the `run.bat` file in the root directory. This will automatically:
1.  Locate port `5000` and kill any zombie backend processes.
2.  Start the Flask server background service using the venv interpreter.
3.  Launch the `frontend/index.html` dashboard in your default browser.

### Manual execution
If you prefer running the components separately:
1.  **Start the Backend REST API**:
    ```bash
    venv\Scripts\python.exe backend\app.py
    ```
2.  **Open the Frontend**:
    Simply open the file `frontend/index.html` in any web browser.
3.  **Run Stress-Test Scripts**:
    While the backend is running, open a separate terminal window and execute:
    ```bash
    venv\Scripts\python.exe tests\test_4pillars_wildfire.py
    ```
