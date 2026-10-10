import urllib.request, json, sys, time, traceback

BASE = "http://127.0.0.1:8000/api"

print("=== health ===")
try:
    r = urllib.request.urlopen(f"{BASE}/health", timeout=5)
    print(r.read().decode())
except Exception as e:
    print(f"health FAIL: {e}")
    sys.exit(1)

print("\n=== upload ===")
try:
    pdf_path = r"d:\campus-rag-assistant\backend\uploads\1791471851_3d343f74851b7af4.pdf"
    boundary = "----RAG_BOUNDARY_12345"
    body = b""
    with open(pdf_path, "rb") as f:
        file_data = f.read()
    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="file"; filename="test.pdf"\r\n'
    body += b"Content-Type: application/pdf\r\n\r\n"
    body += file_data
    body += b"\r\n" + f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(f"{BASE}/upload", data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    start = time.time()
    r = urllib.request.urlopen(req, timeout=120)
    print(f"HTTP {r.status} ({time.time()-start:.1f}s):")
    data = json.loads(r.read())
    print(json.dumps(data, ensure_ascii=False, indent=2)[:800])
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:1000]}")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()

print("\n=== chat ===")
try:
    body = json.dumps({"message": "请假制度"}).encode()
    req = urllib.request.Request(f"{BASE}/chat", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    start = time.time()
    r = urllib.request.urlopen(req, timeout=120)
    data = json.loads(r.read())
    print(f"HTTP {r.status} ({time.time()-start:.1f}s):")
    print("回答:", data.get("answer", "")[:600])
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:1000]}")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()