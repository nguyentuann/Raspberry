import stomp
import time
import json
import random
import ssl

class MyListener(stomp.ConnectionListener):
    def on_connected(self, headers, body):
        print("✅ Connected to STOMP server")

    def on_message(self, headers, message):
        print(f"📩 Server: {message}")

    def on_error(self, headers, message):
        print(f"❌ Error: {message}")

# Cấu hình server
HOST = "06e6-2a09-bac5-d5c8-263c-00-3cf-31.ngrok-free.app"
PORT = 443  # Sử dụng cổng 443 cho wss://
ENDPOINT = "/ws"  # Endpoint trong registry.addEndpoint()

# Khởi tạo kết nối với SSL
conn = stomp.Connection12([(HOST, PORT)], vhost=HOST)
conn.set_listener("", MyListener())

# Kết nối tới server
try:
    conn.connect(wait=True)
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

# Subscribe để nhận thông báo lỗi từ server
conn.subscribe(destination="/pose-error", id=1, ack='auto')

# Gửi dữ liệu mỗi 5 giây
try:
    while True:
        message = {
            "user_id": "user123",
            "key_points": {
                "x": round(random.random(), 2),
                "y": round(random.random(), 2),
                "confidence": round(random.uniform(0, 100), 1)
            }
        }
        conn.send(destination="/app/client/message", body=json.dumps(message))
        print(f"📤 Sent: {json.dumps(message)}")
        time.sleep(5)
except KeyboardInterrupt:
    conn.disconnect()
    print("🔌 Disconnected")