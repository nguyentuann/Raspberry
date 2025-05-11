import io
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
sys.path.append(parent_dir)

import gtts
import uvicorn
import asyncio
from fastapi import FastAPI, WebSocket
import websockets
import pygame

from iot.camera_manager import CameraManager
from iot.speaker import speaker_output

from mobile.webrtc_handler import handleWebRTC, receive_signaling

from my_bluetooth.ble_connection import BLEPeripheral

from training_process import setup_data_channel

from constant.ip_backend import ip_backend

app = FastAPI()
camera_manager = CameraManager()
camera_manager.start_camera()

dataChannel = None


# websocket cho client
@app.websocket("/")
async def websocket_endpoint(client_socket: WebSocket):
    await client_socket.accept()

    # Thiết lập WebRTC connection
    pc, data_channel_ready = await handleWebRTC(client_socket)
    print("Server khởi động...")

    backend_server_future = asyncio.Future()
    

    # Tạo các task bất đồng bộ
    signaling_task = asyncio.create_task(
        receive_signaling(client_socket, pc, camera_manager)
    )
    try:
        dataChannel = await asyncio.wait_for(data_channel_ready, timeout=10)
        print("✅ DataChannel đã sẵn sàng")
    except asyncio.TimeoutError:
        print("⚠️ Không nhận được dataChannel trong thời gian chờ")
        dataChannel = None
        
    setup_data_channel(dataChannel, backend_server_future, camera_manager)

    # receive_error_task = asyncio.create_task(
    #     speaker_output(
    #         dataChannel,
    #         backend_server_future,
    #     )
    # )


    try:
        await asyncio.gather(
            signaling_task,
            # receive_error_task,
        )

    except Exception as e:
        print(f"⚠️ Lỗi WebSocket: {e}")
        await client_socket.close()
        camera_manager.stop_camera()
        print("Camera đã được dừng.")
    finally:
        # Hủy các task
        signaling_task.cancel()
        # receive_error_task.cancel()

        # Đóng kết nối với client_socket
        if client_socket:
            try:
                await client_socket.close()
                print("Đã đóng client_socket")
            except Exception as e:
                print(f"⚠️ Lỗi khi đóng client_socket: {e}")

        # Dừng camera
        try:
            camera_manager.stop_camera()
            print("Camera đã được dừng.")
        except Exception as e:
            print(f"⚠️ Lỗi khi dừng camera: {e}")

        # Đóng kết nối với dataChannel
        if dataChannel:
            try:
                await dataChannel.close()
                print("Đã đóng dataChannel")
            except Exception as e:
                print(f"⚠️ Lỗi khi đóng dataChannel: {e}")


if __name__ == "__main__":
    # kết nối bluetooth để trao đổi IP
    # try:
    #     ble_peripheral = BLEPeripheral()
    #     ble_peripheral.start()
    # except Exception as e:
    #     print(f"⚠️ Lỗi: {e}")
    # finally:
    #     if ble_peripheral:
    #         ble_peripheral.stop()
    # khởi động server
    uvicorn.run(app, host="0.0.0.0", port=8000)
