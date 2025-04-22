import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
sys.path.append(parent_dir)

import uvicorn
import asyncio
from fastapi import FastAPI, WebSocket
from iot.camera_manager import CameraManager
from iot.speaker import speaker_output

from mobile.webrtc_handler import handleWebRTC
from mobile.webrtc_bluetooth import handle_webrtc_via_bluetooth
import websockets

app = FastAPI()
camera_manager = CameraManager()
ai_server_ip = "192.168.23.100"


# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()

@app.on_event("startup")
async def start_main_tasks():

    print("🚀 Server khởi động...")
    # Kết nối đến WebSocket server để gửi keypoints
    ai_socket = None
    try:
        ai_socket = await websockets.connect(f"ws://{ai_server_ip}:8000/ws")
        print("Đã kết nối đến ai_socket")
    except Exception as e:
        print(f"⚠️ Không thể kết nối đến ai_socket: {e}")
        return

    # Khởi động camera
    camera_manager.start_camera()

    # Tạo các task bất đồng bộ
    send_keypoint_task = asyncio.create_task(camera_manager._send_keypoints(ai_socket))

    # dùng ws làm signaling server
    # webrtc_task = asyncio.create_task(handleWebRTC(websocket, camera_manager))

    # dùng bluetooth làm signaling server
    # webrtc_task = asyncio.create_task(handle_webrtc_via_bluetooth())

    # xử lý với loa
    listen_ai_socket_task = asyncio.create_task(speaker_output(ai_socket))

    try:
        await asyncio.gather(
            # webrtc_task,
            send_keypoint_task,
            listen_ai_socket_task,
        )
    except Exception as e:
        print(f"⚠️ Lỗi WebSocket: {e}")
    finally:
        # Hủy các task
        send_keypoint_task.cancel()
        # webrtc_task.cancel()
        listen_ai_socket_task.cancel()

        # Đợi các task thực sự dừng lại
        try:
            await asyncio.gather(
                send_keypoint_task,
                # webrtc_task,
                return_exceptions=True,
            )
        except asyncio.CancelledError:
            print("error")
            pass

        camera_manager.stop_camera()

        if ai_socket:
            try:
                await ai_socket.close()
                print("Đã đóng ai_socket")
            except Exception as e:
                print(f"⚠️ Lỗi khi đóng ai_socket: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
