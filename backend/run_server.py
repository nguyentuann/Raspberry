import io
import sys
import os

import pygame

backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
sys.path.append(parent_dir)

import gtts
import uvicorn
import asyncio
from fastapi import FastAPI, WebSocket
from iot.camera_manager import CameraManager
from iot.speaker import speaker_output

from mobile.webrtc_handler import handleWebRTC, receive_signaling
import websockets

app = FastAPI()
camera_manager = CameraManager()
ai_server_ip = "192.168.1.2"

# Kết nối đến WebSocket server để gửi keypoints
ai_socket = None

def notifySuccess():
    pygame.mixer.init()
    tts = gtts.gTTS("Kết nối hoàn thành, đã sẵn sàng", lang="vi")

    # Lưu vào file tạm vì pygame không hỗ trợ phát từ BytesIO
    audio = io.BytesIO()
    tts.write_to_fp(audio)
    audio.seek(0)

    # Khởi tạo pygame để phát âm thanh
    pygame.mixer.init()
    pygame.mixer.music.load(audio, "mp3")
    pygame.mixer.music.play()


@app.websocket("/ws")
async def websocket_endpoint(client_socket: WebSocket):
    
    # chấp nhận kết nối của client
    await client_socket.accept()
    
    # Thiết lập WebRTC connection
    pc, dataChannel = await handleWebRTC(client_socket, camera_manager)

    print("Server khởi động...")
    
    try:
        # ai_socket = await websockets.connect(f"ws://{ai_server_ip}:8000/ws")
        ai_socket = await websockets.connect("https://f4f1-203-205-50-209.ngrok-free.app/gym-pose/ws")
        print("Đã kết nối đến ai_socket")
        
    except Exception as e:
        print(f"Không thể kết nối đến ai_socket: {e}")
        return

    # Khởi động camera
    camera_manager.start_camera()


    # Tạo các task bất đồng bộ
    signaling_task = asyncio.create_task(receive_signaling(client_socket, pc))
    
    # gửi keypoint 
    send_keypoint_task = asyncio.create_task(camera_manager._send_keypoints(ai_socket))

    # xử lý với loa
    listen_ai_socket_task = asyncio.create_task(speaker_output(dataChannel, ai_socket))

    try:
        await asyncio.gather(
            signaling_task,
            send_keypoint_task,
            listen_ai_socket_task,
        )
        
        notifySuccess()
       
    except Exception as e:
        print(f"⚠️ Lỗi WebSocket: {e}")
    finally:
        # Hủy các task
        send_keypoint_task.cancel()
        listen_ai_socket_task.cancel()

        # Đợi các task thực sự dừng lại
        try:
            await asyncio.gather(
                send_keypoint_task,
                return_exceptions=True,
            )
        except asyncio.CancelledError:
            print("error")
            pass

        # camera_manager.stop_camera()

        if ai_socket:
            try:
                await ai_socket.close()
                print("Đã đóng ai_socket")
            except Exception as e:
                print(f"⚠️ Lỗi khi đóng ai_socket: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
