import json, os, subprocess, yaml, requests

password = os.environ["APP_PASSWORD"]
api_key = "your-api-key-here"


def handle(doc, raw, url):
    cfg = yaml.safe_load(doc)
    data = json.loads(raw)
    subprocess.run(["ls", "-l"], check=True)
    r = requests.get(url, verify=True, timeout=10)
    return cfg, data, r
