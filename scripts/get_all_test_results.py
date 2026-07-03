import urllib.request
import json

url = "http://127.0.0.1:5000/api/chat"

scenarios = [
    {
        "name": "Scenario A - Turn 1 (GOVT)",
        "payload": {
            "message": "Which state has more wildfires?",
            "domain": "GOVT",
            "history": []
        }
    },
    {
        "name": "Scenario A - Turn 2 (GOVT)",
        "payload": {
            "message": "What causes them?",
            "domain": "GOVT",
            "history": [
                "Which state has more wildfires?",
                'According to the [GOVT] document \'2020 Fire Season Incident Archive | CAL FIRE\': "As of the end of the year, nearly 10,000 fires had burned over 4.2 million acres, more than 4% of the state\'s roughly 100 million acres of land, making 2020 the largest wildfire season recorded in California\'s modern history. California\'s August Complex fire has been described as the first \"gigafire\" as the area burned exceeded 1 million acres. The fire crossed seven counties and has been described as being larger than the state of Rhode Island."'
            ]
        }
    },
    {
        "name": "Scenario B (CLOUD)",
        "payload": {
            "message": "Explain secure compliant deployment steps.",
            "domain": "CLOUD",
            "history": []
        }
    },
    {
        "name": "Scenario C (CLAPNQ)",
        "payload": {
            "message": "What causes most lightning and natural wildfires?",
            "domain": "CLAPNQ",
            "history": []
        }
    },
    {
        "name": "Scenario D - Turn 1 (FIQA)",
        "payload": {
            "message": "What's the difference between Market Cap and NAV?",
            "domain": "FIQA",
            "history": []
        }
    },
    {
        "name": "Scenario D - Turn 2 (FIQA)",
        "payload": {
            "message": "Which is more important?",
            "domain": "FIQA",
            "history": [
                "What's the difference between Market Cap and NAV?",
                'According to the [FIQA] document \'\': "The market cap is share price times number of shares. For Amazon today people are willing to pay 290 a share for a company with a NAV of 22 a share. If of nav and price were equal the P/B (price to book ratio) would be 1, but for Amazon it is 13."'
            ]
        }
    },
    {
        "name": "Case 1: Entity Mismatch (FIQA)",
        "payload": {
            "message": "What is the NAV of Apple?",
            "domain": "FIQA",
            "history": []
        }
    },
    {
        "name": "Case 2: Out of Domain (GOVT)",
        "payload": {
            "message": "How do you bake a vanilla wedding cake with buttercream frosting?",
            "domain": "GOVT",
            "history": []
        }
    }
]

for sc in scenarios:
    print(f"\n--- {sc['name']} ---")
    req = urllib.request.Request(
        url,
        data=json.dumps(sc['payload']).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            print("  Rewritten Query:", res.get("rewritten_query"))
            print("  Verdict Status: ", res.get("verdict", {}).get("status"))
            print("  Confidence Score:", res.get("verdict", {}).get("highest_logit"))
            print("  Answer:         ", res.get("answer"))
            if res.get("citation"):
                print("  Citation ID:    ", res["citation"]["passage_id"])
                print("  Citation Title: ", res["citation"]["title"])
    except Exception as e:
        print("  Error:", e)
