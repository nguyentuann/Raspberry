import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
sys.path.append(parent_dir)

import stomp
import uvicorn
import asyncio
from fastapi import FastAPI, WebSocket
from iot.camera_manager import CameraManager
from iot.speaker import speaker_output
import json

import websockets

app = FastAPI()
camera_manager = CameraManager()
ai_server_ip = "192.168.1.5"


class MyListener(stomp.ConnectionListener):
    def on_connected(self, headers, body):
        print("Connected to STOMP server.")

    def on_error(self, headers, message):
        print("Received an error:", message)

    def on_message(self, headers, message):
        print("Received a message:", message)


@app.on_event("startup")
async def start():

    # Kết nối đến WebSocket server để gửi keypoints
    ai_socket = None

    try:
        ai_socket = await websockets.connect(
            "wss://f4f1-203-205-50-209.ngrok-free.app/gym-pose/ws"
        )

        # Gửi tin nhắn dưới dạng JSON

        await ai_socket.send(json.dumps({"user_id": "123456", "key_points": {}}))
        conn = stomp.Connection(
            [("f4f1-203-205-50-209.ngrok-free.app", 8696)],
        )
        conn.set_listener("", MyListener())
        conn.connect(wait=True)

        # Gửi message tới endpoint được định nghĩa trong @MessageMapping("/client/message")
        message = {
            "user_id": "123456",
            "key_points": {
                # Các keypoint gửi lên ở đây
            },
        }

        conn.send(destination="/app/client/message", body=json.dumps(message))

        print("Đã kết nối đến ai_socket")

    except Exception as e:
        print(f"⚠️ Không thể kết nối đến ai_socket: {e}")
        return

    # Khởi động camera
    # camera_manager.start_camera()

    # # Tạo các task bất đồng bộ

    # # gửi keypoint
    # send_keypoint_task = asyncio.create_task(camera_manager._send_keypoints(ai_socket))

    # # xử lý với loa
    # listen_ai_socket_task = asyncio.create_task(speaker_output(ai_socket))

    # try:
    #     await asyncio.gather(
    #         send_keypoint_task,
    #         listen_ai_socket_task,
    #     )
    # except Exception as e:
    #     print(f"⚠️ Lỗi WebSocket: {e}")
    # finally:
    #     # Hủy các task
    #     send_keypoint_task.cancel()
    #     listen_ai_socket_task.cancel()

    #     # Đợi các task thực sự dừng lại
    #     try:
    #         await asyncio.gather(
    #             send_keypoint_task,
    #             return_exceptions=True,
    #         )
    #     except asyncio.CancelledError:
    #         print("error")
    #         pass

    #     camera_manager.stop_camera()

    #     if ai_socket:
    #         try:
    #             await ai_socket.close()
    #             print("Đã đóng ai_socket")
    #         except Exception as e:
    #             print(f"⚠️ Lỗi khi đóng ai_socket: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
