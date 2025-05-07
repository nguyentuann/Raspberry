import asyncio
import websockets
import json


domain = "3663-2a09-bac5-d5cf-e6-00-17-345.ngrok-free.app"
path = "/gym-pose/ws"
user_id = "111"


class WebSocketBackend:
    def __init__(self):
        self.ws = None

    @classmethod
    async def create(cls):
        self = cls()
        connected = await self.connect()
        if connected:
            return self
        else:
            print("⛔ Không thể thiết lập kết nối")
            return None

    async def connect(self):
        ws_uri = f"wss://{domain}{path}?userId={user_id}"
        try:
            print(f"Kết nối đến: {ws_uri}")
            self.ws = await websockets.connect(ws_uri)
            print("✅ Đã kết nối đến backend server")
            return True
        except Exception as e:
            print(f"❌ Kết nối thất bại: {e}")
            return False

    # async def send_msg(self):
    #     try:
    #         await self.ws.send(json.dumps(self.data))
    #         print(f"📤 Đã gửi: {self.data}")
    #     except Exception as e:
    #         print(f"❌ Gửi thất bại: {e}")

    # async def receive_msg(self):
    #     try:
    #         message = await self.ws.recv()
    #         print(f"📥 Nhận: {message}")
    #         if message != None:
    #             return message
    #     except websockets.ConnectionClosed:
    #         print("❌ Kết nối bị đóng")
    #     except Exception as e:
    #         print(f"❌ Lỗi khi nhận: {e}")
