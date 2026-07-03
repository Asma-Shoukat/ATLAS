import urllib.request
import json

url = "http://127.0.0.1:5000/api/chat"
history = [
    "Which state has more wildfires?",
    "According to the [GOVT] document '2020 Fire Season Incident Archive | CAL FIRE': \"As of the end of the year, nearly 10,000 fires had burned over 4.2 million acres, more than 4% of the state's roughly 100 million acres of land, making 2020 the largest wildfire season recorded in California's modern history. California's August Complex fire has been described as the first \"gigafire\" as the area burned exceeded 1 million acres. The fire crossed seven counties and has been described as being larger than the state of Rhode Island.\""
]
payload = {
    "message": "What causes them?",
    "domain": "GOVT",
    "history": history
}
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode('utf-8'))
        print("STATUS:", res.get("verdict", {}).get("status"))
        print("CONFIDENCE:", res.get("verdict", {}).get("highest_logit"))
        print("REWRITTEN:", res.get("rewritten_query"))
        print("ANSWER:", res.get("answer"))
        if res.get("citation"):
            print("CITATION ID:", res["citation"]["passage_id"])
            print("CITATION TITLE:", res["citation"]["title"])
except Exception as e:
    print("Error:", e)
