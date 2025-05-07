import io
import sys
import os


backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
sys.path.append(parent_dir)

# import gtts
import uvicorn
import asyncio
from fastapi import FastAPI, WebSocket
import websockets
# import pygame

from iot.camera_manager import CameraManager
from iot.speaker import speaker_output
from mobile.webrtc_handler import handleWebRTC, receive_signaling
from my_bluetooth.ble_connection import BLEPeripheral
from backend.websocket_backend import WebSocketBackend

app = FastAPI()
camera_manager = CameraManager()
backend_server = None




# thông báo kết nối thành công
def notifySuccess():
    print("Kết nối hoàn thành, đã sẵn sàng")
    # pygame.mixer.init()
    # tts = gtts.gTTS("Kết nối hoàn thành, đã sẵn sàng", lang="vi")

    # # Lưu vào file tạm vì pygame không hỗ trợ phát từ BytesIO
    # audio = io.BytesIO()
    # tts.write_to_fp(audio)
    # audio.seek(0)

    # # Khởi tạo pygame để phát âm thanh
    # pygame.mixer.init()
    # pygame.mixer.music.load(audio, "mp3")
    # pygame.mixer.music.play()


# websocket cho client
# @app.websocket("/ws")
# async def websocket_endpoint(client_socket: WebSocket):
# await client_socket.accept()


async def main():

    # Thiết lập WebRTC connection
    # pc, dataChannel = await handleWebRTC(client_socket, camera_manager)
    print("Server khởi động...")

    try:
        wsBackend = await WebSocketBackend.create()
        if wsBackend:
            backend_server = wsBackend.ws  # backend_server là WebSocket hợp lệ nếu kết nối thành công
        else:
            print("Kết nối WebSocket thất bại.")

        print("Đã kết nối đến backend_server")
    except Exception as e:
        print(f"Không thể kết nối đến backend_server: {e}")

    # khởi động camera
    try:
        camera_manager.start_camera()
        print("Camera đã được khởi động.")
    except Exception as e:
        print(f"⚠️ Không thể khởi động camera: {e}")

    # Tạo các task bất đồng bộ
    # signaling_task = asyncio.create_task(receive_signaling(client_socket, pc))

    send_keypoints_task = asyncio.create_task(
        camera_manager._send_keypoints(backend_server)
    )

    receive_error_task = asyncio.create_task(
        speaker_output(
            # dataChannel,
            backend_server,
        )
    )

    try:
        await asyncio.gather(
            # signaling_task,
            send_keypoints_task,
            receive_error_task,
        )
        notifySuccess()

    except Exception as e:
        print(f"⚠️ Lỗi WebSocket: {e}")
        # await client_socket.close()
        await backend_server.close()
        camera_manager.stop_camera()
        print("Camera đã được dừng.")
    finally:
        # Hủy các task
        send_keypoints_task.cancel()
        receive_error_task.cancel()
        receive_error_task.cancel()

        # Đợi các task thực sự dừng lại
        try:
            await asyncio.gather(
                # signaling_task,
                send_keypoints_task,
                receive_error_task,
            )
        except asyncio.CancelledError:
            print("Error in task cancellation")

        # Đóng kết nối với backend_server
        if backend_server:
            try:
                await backend_server.close()
                print("Đã đóng backend_server")
            except Exception as e:
                print(f"⚠️ Lỗi khi đóng backend_server: {e}")

        # Đóng kết nối với client_socket
        # if client_socket:
        #     try:
        #         await client_socket.close()
        #         print("Đã đóng client_socket")
        #     except Exception as e:
        #         print(f"⚠️ Lỗi khi đóng client_socket: {e}")

        # Dừng camera
        try:
            camera_manager.stop_camera()
            print("Camera đã được dừng.")
        except Exception as e:
            print(f"⚠️ Lỗi khi dừng camera: {e}")


# if __name__ == "__main__":
#     # kết nối bluetooth để trao đổi IP
#     try:
#         ble_peripheral = BLEPeripheral()
#         ble_peripheral.start()
#     except Exception as e:
#         print(f"⚠️ Lỗi: {e}")
#     finally:
#         if ble_peripheral:
#             ble_peripheral.stop()
#     # khởi động server
#     uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    asyncio.run(main())
