import urllib.request
import json

url = "http://127.0.0.1:5000/api/chat"

test_queries = [
    {"message": "Which state has more wildfires?", "domain": "GOVT"},
    {"message": "Explain secure compliant deployment steps.", "domain": "CLOUD"},
    {"message": "Why doesn't the government prevent people from living in areas prone to flooding?", "domain": "FIQA"},
    {"message": "What causes most lightning and natural wildfires?", "domain": "CLAPNQ"}
]

for q in test_queries:
    print(f"\n=== Query: {q['message']} (Domain: {q['domain']}) ===")
    req = urllib.request.Request(
        url,
        data=json.dumps(q).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print("Verdict Status:", res_data.get("verdict", {}).get("status"))
            print("Verdict Reason:", res_data.get("verdict", {}).get("reason"))
            print("Answer:", res_data.get("answer"))
            if res_data.get("citation"):
                print("Citation Title:", res_data["citation"]["title"])
                print("Citation Pass ID:", res_data["citation"]["passage_id"])
    except Exception as e:
        print("Error:", e)
