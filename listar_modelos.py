import requests
import tomllib

with open(".streamlit/secrets.toml", "rb") as f:
    chave = tomllib.load(f)["GEMINI_API_KEY"]

url = "https://generativelanguage.googleapis.com/v1beta/models"
token = None

while True:
    params = {"pageSize": 100}
    if token:
        params["pageToken"] = token
    r = requests.get(url, headers={"x-goog-api-key": chave}, params=params, timeout=30)
    dados = r.json()
    for m in dados.get("models", []):
        metodos = m.get("supportedGenerationMethods", [])
        if "generateContent" in metodos:
            print(m["name"])
    token = dados.get("nextPageToken")
    if not token:
        break