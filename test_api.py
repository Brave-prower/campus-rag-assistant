import urllib.request, json, sys, time

BASE = "http://127.0.0.1:8000/api"

def get(path):
    r = urllib.request.urlopen(f"{BASE}{path}")
    return json.loads(r.read())

def post(path, data=None, file_path=None, file_name="test.pdf"):
    url = f"{BASE}{path}"
    if file_path:
        boundary = "----RAG_TEST_BOUNDARY"
        body = b""
        with open(file_path, "rb") as f:
            file_data = f.read()
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'.encode()
        body += b"Content-Type: application/pdf\r\n\r\n"
        body += file_data
        body += b"\r\n" + f"--{boundary}--\r\n".encode()
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    else:
        body = json.dumps(data or {}).encode()
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()[:500]
        return e.code, body_text

print("=== health ===")
print(get("/health"))

print("\n=== upload ===")
status, data = post("/upload", file_path=r"d:\campus-rag-assistant\backend\uploads\1791471851_3d343f74851b7af4.pdf", file_name="rules.pdf")
print(f"HTTP {status}:", json.dumps(data, ensure_ascii=False, indent=2) if isinstance(data, dict) else data)

print("\n=== chat: 请假制度 ===")
status, data = post("/chat", data={"message": "学校的请假制度是什么？"})
print(f"HTTP {status}:")
if isinstance(data, dict):
    print("回答:", data.get("answer", "")[:500])
    print("来源:", data.get("sources", []))
else:
    print(data[:500])

print("\n=== chat: 毕业证 ===")
status, data = post("/chat", data={"message": "怎样才能拿到毕业证？"})
print(f"HTTP {status}:")
if isinstance(data, dict):
    print("回答:", data.get("answer", "")[:500])
    print("来源:", data.get("sources", []))
else:
    print(data[:500])