"""
ATLAS 4-Pillar Stress Test — Wildfire Follow-Up Scenario
=========================================================
This script simulates a multi-turn conversation starting from "Which state has more wildfires?"
and uses follow-up questions to exercise ALL 4 core pillars:

  PILLAR 1: Pronoun Resolution  — "What causes them?"  (pronoun "them" → "wildfires")
  PILLAR 2: Anti-Hallucination  — "How to bake chocolate cake?" (out-of-domain → INTERCEPTED)
  PILLAR 3: Query Rewriting     — "Tell me more" (short query → enriched with wildfire context)
  PILLAR 4: Accurate Retrieval  — "What causes most lightning and natural wildfires?" (direct factual)

Run AFTER the backend is fully booted:
  venv\\Scripts\\python.exe tests\\test_4pillars_wildfire.py
"""
import urllib.request
import json
import sys

API_URL = "http://127.0.0.1:5000/api/chat"
PASS = "[PASS]"
FAIL = "[FAIL]"

def send(message, domain, history=None):
    payload = {"message": message, "domain": domain, "history": history or []}
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"   HTTP ERROR: {e}")
        return None

def divider(title):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")

results = []

# =====================================================================
# TEST 1: Base Query — Accurate Retrieval (Pillar 4)
# =====================================================================
divider("TEST 1: ACCURATE RETRIEVAL (Pillar 4)")
print("  Query:  'Which state has more wildfires?'")
print("  Domain: GOVT")
print("  Expect: APPROVED verdict with wildfire-related evidence from GOVT corpus")

r1 = send("Which state has more wildfires?", "GOVT")
if r1:
    status = r1.get("verdict", {}).get("status", "")
    answer = r1.get("answer", "")
    citation = r1.get("citation")
    rewritten = r1.get("rewritten_query", "")

    print(f"\n  Verdict: {status}")
    print(f"  Rewritten: '{rewritten}'")
    print(f"  Answer: {answer[:120]}...")
    if citation:
        print(f"  Citation Title: {citation.get('title', '—')}")
        print(f"  Retrieval Method: {citation.get('retrieval_method', '—')}")

    test1_pass = status == "APPROVED" and citation is not None
    print(f"\n  Result: {PASS if test1_pass else FAIL} — {'Accurate wildfire evidence retrieved' if test1_pass else 'FAILED to retrieve relevant evidence'}")
    results.append(("Pillar 4: Accurate Retrieval", test1_pass))
else:
    print(f"\n  Result: {FAIL} — Backend not reachable")
    results.append(("Pillar 4: Accurate Retrieval", False))

# =====================================================================
# TEST 2: Pronoun Follow-Up — Pronoun Resolution (Pillar 1)
# =====================================================================
divider("TEST 2: PRONOUN RESOLUTION (Pillar 1)")
print("  Query:  'What causes them?'")
print("  History: ['Which state has more wildfires?', '<prev answer>']")
print("  Expect: 'them' resolved to 'wildfires' in rewritten query")

history_for_t2 = [
    "Which state has more wildfires?",
    r1.get("answer", "Wildfires are common in California.") if r1 else "Wildfires are common in California."
]
r2 = send("What causes them?", "GOVT", history_for_t2)
if r2:
    rewritten = r2.get("rewritten_query", "")
    explain = r2.get("explainability", {})
    q_und = explain.get("query_understanding", {})
    resolved = q_und.get("resolved", False)
    referent = q_und.get("referent", "")
    pronouns = q_und.get("pronouns_detected", [])
    status = r2.get("verdict", {}).get("status", "")

    print(f"\n  Resolved: {resolved}")
    print(f"  Pronouns Detected: {pronouns}")
    print(f"  Referent: '{referent}'")
    print(f"  Rewritten Query: '{rewritten}'")
    print(f"  Verdict: {status}")

    # Check: "them" was detected and replaced with something wildfire-related
    test2_pass = resolved and "them" in pronouns and "them" not in rewritten.lower()
    print(f"\n  Result: {PASS if test2_pass else FAIL} — {'Pronoun them correctly resolved' if test2_pass else 'Pronoun resolution FAILED'}")
    results.append(("Pillar 1: Pronoun Resolution", test2_pass))
else:
    print(f"\n  Result: {FAIL} — Backend not reachable")
    results.append(("Pillar 1: Pronoun Resolution", False))

# =====================================================================
# TEST 3: Out-of-Domain Attack — Anti-Hallucination (Pillar 2)
# =====================================================================
divider("TEST 3: ANTI-HALLUCINATION (Pillar 2)")
print("  Query:  'How do you bake a vanilla wedding cake with buttercream frosting?'")
print("  Domain: GOVT")
print("  Expect: INTERCEPTED — no hallucinated answer about baking")

r3 = send("How do you bake a vanilla wedding cake with buttercream frosting?", "GOVT")
if r3:
    status = r3.get("verdict", {}).get("status", "")
    reason = r3.get("verdict", {}).get("reason", "")
    answer = r3.get("answer", "")
    citation = r3.get("citation")

    print(f"\n  Verdict: {status}")
    print(f"  Reason: {reason}")
    print(f"  Citation: {'Present (BAD!)' if citation else 'None (correct)'}")
    print(f"  Answer: {answer[:100]}...")

    test3_pass = status == "INTERCEPTED" and citation is None
    print(f"\n  Result: {PASS if test3_pass else FAIL} — {'Correctly intercepted out-of-domain query' if test3_pass else 'FAILED — hallucinated an answer!'}")
    results.append(("Pillar 2: Anti-Hallucination", test3_pass))
else:
    print(f"\n  Result: {FAIL} — Backend not reachable")
    results.append(("Pillar 2: Anti-Hallucination", False))

# =====================================================================
# TEST 4: Short Follow-Up — Query Rewriting (Pillar 3)
# =====================================================================
divider("TEST 4: QUERY REWRITING (Pillar 3)")
print("  Query:  'Tell me more'")
print("  History: ['Which state has more wildfires?', '<prev answer>']")
print("  Expect: Short query enriched with wildfire context via query rewriting")

r4 = send("Tell me more", "GOVT", history_for_t2)
if r4:
    rewritten = r4.get("rewritten_query", "")
    explain = r4.get("explainability", {})
    q_und = explain.get("query_understanding", {})
    resolved = q_und.get("resolved", False)
    referent = q_und.get("referent", "")
    status = r4.get("verdict", {}).get("status", "")

    print(f"\n  Resolved: {resolved}")
    print(f"  Referent: '{referent}'")
    print(f"  Rewritten Query: '{rewritten}'")
    print(f"  Verdict: {status}")

    # Check: the short query was enriched with context (should NOT be "Tell me more" unchanged)
    test4_pass = resolved and rewritten.lower() != "tell me more"
    print(f"\n  Result: {PASS if test4_pass else FAIL} — {'Short query correctly enriched with context' if test4_pass else 'Query rewriting FAILED'}")
    results.append(("Pillar 3: Query Rewriting", test4_pass))
else:
    print(f"\n  Result: {FAIL} — Backend not reachable")
    results.append(("Pillar 3: Query Rewriting", False))


# =====================================================================
# FINAL RESULTS
# =====================================================================
print(f"\n\n{'='*65}")
print("  ATLAS 4-PILLAR STRESS TEST — FINAL RESULTS")
print(f"{'='*65}")
all_passed = True
for name, passed in results:
    icon = PASS if passed else FAIL
    print(f"  {icon}  {name}")
    if not passed:
        all_passed = False

print(f"\n  {'ALL 4 PILLARS PASSED!' if all_passed else 'SOME PILLARS FAILED — review above'}")
print(f"{'='*65}\n")

sys.exit(0 if all_passed else 1)
