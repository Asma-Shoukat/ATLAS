import urllib.request
import json

url = "http://127.0.0.1:5000/api/chat"

# Simulated multi-turn conversations
turns = [
    {
        "name": "Turn 1: Base Query (FIQA)",
        "payload": {
            "message": "What's the difference between Market Cap and NAV?",
            "domain": "FIQA",
            "history": []
        }
    },
    {
        "name": "Turn 2: Follow-up Pronoun resolution (Expect Market Cap and NAV rewrite)",
        "payload": {
            "message": "Which is more important?",
            "domain": "FIQA",
            "history": [
                "What's the difference between Market Cap and NAV?",
                "The market cap is share price times number of shares. For Amazon today people are willing to pay 290 a share for a company with a NAV of 22 a share. If of nav and price were equal the P/B (price to book ratio) would be 1, but for Amazon it is 13."
            ]
        }
    },
    {
        "name": "Turn 3: Entity Mismatch Guard (Expect Interception)",
        "payload": {
            "message": "What is the NAV of Apple?",
            "domain": "FIQA",
            "history": []
        }
    },
    {
        "name": "Turn 4: Calibrated Threshold Guard (Expect Interception)",
        "payload": {
            "message": "Why is Amazon's ratio so high?",
            "domain": "FIQA",
            "history": []
        }
    }
]

for t in turns:
    print(f"\n=========================================")
    print(f"Executing: {t['name']}")
    print(f"Query: '{t['payload']['message']}'")
    
    req = urllib.request.Request(
        url,
        data=json.dumps(t['payload']).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print("Rewritten Query:", res_data.get("rewritten_query"))
            print("Verdict Status:", res_data.get("verdict", {}).get("status"))
            print("Verdict Reason:", res_data.get("verdict", {}).get("reason"))
            print("Answer:", res_data.get("answer"))
            if res_data.get("citation"):
                print("Citation Pass ID:", res_data["citation"]["passage_id"])
    except Exception as e:
        print("HTTP Error:", e)
