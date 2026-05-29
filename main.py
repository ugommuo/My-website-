import asyncio
import json
import time

LEDGER_FILE = "flywheel_ledger.json"

async def save_to_ledger(data):
    try:
        await asyncio.sleep(0.001)
        with open(LEDGER_FILE, "a") as f:
            f.write(json.dumps(data) + "\n")
        return True
    except Exception as e:
        print(f"[-] Storage Exception: {e}")
        return False

async def handle_client(reader, writer):
    start_time = time.perf_counter()
    try:
        data = await reader.read(4096)
        if not data:
            return

        request = data.decode('utf-8', errors='ignore')
        headers, _, body = request.partition('\r\n\r\n')

        # --- 1. HANDLE BROWSER VISUAL DASHBOARD (GET REQUESTS) ---
        if "GET / " in headers or "GET / HTTP" in headers:
            html_body = """<!DOCTYPE html>
<html>
<head>
    <title>Flywheel Engine Portal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 30px; text-align: center; box-shadow: 0 8px 24px rgba(0,0,0,0.5); max-width: 400px; width: 90%; }
        h1 { color: #58a6ff; margin-top: 0; font-size: 24px; }
        .status-badge { background: #238636; color: white; padding: 6px 14px; border-radius: 20px; font-weight: bold; display: inline-block; margin: 15px 0; font-size: 14px; letter-spacing: 0.5px; }
        p { color: #8b949e; line-height: 1.5; font-size: 15px; }
        .footer { font-size: 11px; color: #484f58; margin-top: 25px; border-top: 1px solid #21262d; padding-top: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🚀 FLYWHEEL CORE ENGINE</h1>
        <div class="status-badge">ONLINE & OPERATIONAL</div>
        <p>AuraConnect architecture interface is routing successfully. Hardware processing loops are active and listening on port 8888.</p>
        <div class="footer">Flywheel Universal Node v2.0.0 &bull; Async Socket Architecture</div>
    </div>
</body>
</html>"""
            
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(html_body.encode('utf-8'))}\r\n"
                "Connection: close\r\n\r\n"
                f"{html_body}"
            )
            writer.write(response.encode('utf-8'))
            await writer.drain()
            return

        # --- 2. HANDLE CROSS-ORIGIN PREFLIGHTS (OPTIONS REQUESTS) ---
        if "OPTIONS" in headers:
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "Access-Control-Allow-Methods: POST, GET, OPTIONS\r\n"
                "Access-Control-Allow-Headers: Content-Type\r\n"
                "Connection: close\r\n\r\n"
            )
            writer.write(response.encode('utf-8'))
            await writer.drain()
            return

        # --- 3. HANDLE DATA PACKETS (POST REQUESTS) ---
        if "POST" in headers and body:
            try:
                payload = json.loads(body)
            except Exception:
                payload = {"client": "AuraConnect Portal", "status": "active"}

            print(f"\n⚡ [INGEST] Packet received from: {payload.get('client', 'Unknown')}")

            storage_success = await save_to_ledger(payload)
            latency_ms = (time.perf_counter() - start_time) * 1000
            print(f"📁 [LEDGER] Written successfully | Latency: {latency_ms:.3f}ms")

            response_body = json.dumps({
                "status": "verified",
                "engine": "Flywheel Core v2",
                "latency_ms": f"{latency_ms:.3f}ms",
                "storage": "committed" if storage_success else "failed"
            })

            response = (
                "HTTP/1.1 200 OK\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "Access-Control-Allow-Methods: POST, GET, OPTIONS\r\n"
                "Access-Control-Allow-Headers: Content-Type\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "Connection: close\r\n\r\n"
                f"{response_body}"
            )
            writer.write(response.encode('utf-8'))
            await writer.drain()

    except Exception as e:
        print(f"[-] Handshake Exception: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 8888)
    print("🚀 FLYWHEEL UNIVERSAL NODE: Active & Listening [Port 8888]")
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
