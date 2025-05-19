import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
sys.path.append(parent_dir)

import signal
import asyncio
import uvicorn
import threading
from fastapi import FastAPI, WebSocket

from iot.camera_manager import CameraManager
from training_process import setup_data_channel
from mobile.webrtc_handler import WebRTCHandler
from my_bluetooth.ble_connection import BLEPeripheral, power_on_bluetooth_adapter_shell

camera_manager = None

app = FastAPI()
ble_peripheral = None

active_connections = set()
cleanup_lock = asyncio.Lock()


# ! XỬ LÝ SỰ KIỆN TẮT CHƯƠNG TRÌNH
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Đang tắt ứng dụng, dọn dẹp tài nguyên...")
    global ble_peripheral

    # Đóng tất cả các kết nối trước khi thoát
    cleanup_tasks = []
    for ws in active_connections.copy():
        cleanup_tasks.append(asyncio.create_task(cleanup_connection(ws)))

    if cleanup_tasks:
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)

    # Dừng Bluetooth
    if ble_peripheral:
        ble_peripheral.stop()

# ! ĐÓNG KẾT NỐI VỚI BACKEND SERVER
async def close_backend_server(backend_server_future):
    if backend_server_future.done():
        try:
            backend_server = backend_server_future.result()
            await backend_server.close()
        except Exception as e:
            print(f"Lỗi đóng kết nối backend: {e}")


# ! DỌN DẸP TÀI NGUYÊN
async def cleanup_connection(client_socket):
    async with cleanup_lock:
        if client_socket in active_connections:
            active_connections.remove(client_socket)
            try:
                await client_socket.close()
                print(f"✅ Đã giải phóng tài nguyên cho kết nối")
            except Exception as e:
                print(f"⚠️ Lỗi khi dọn dẹp kết nối: {e}")

# ! XỬ LÝ KẾT NỐI WEBSOCKET
@app.websocket("/")
async def websocket_endpoint(client_socket: WebSocket):
    global camera_manager
    await client_socket.accept()

    if camera_manager is None:
        camera_manager = CameraManager()
    else:
        pass

    active_connections.add(client_socket)

    pc = None
    dataChannel = None
    backend_server_future = asyncio.Future()
    web_rtc_handler = WebRTCHandler()
    try:
        # ! THIẾT LẬP WEBRTC
        pc, data_channel_ready = await web_rtc_handler.handleWebRTC(client_socket)
        print(pc.connectionState)
        print("Server khởi động...")

        # # Tạo các task bất đồng bộ
        signaling_task = asyncio.create_task(
            web_rtc_handler.receive_signaling(client_socket, pc, camera_manager)
        )

        try:
            dataChannel = await asyncio.wait_for(data_channel_ready, timeout=100)
            print("✅ DataChannel đã sẵn sàng")
        except asyncio.TimeoutError:
            print("⚠️ Không nhận được dataChannel trong thời gian chờ")
            dataChannel = None

        setup_data_channel(dataChannel, backend_server_future, camera_manager)

        try:
            await signaling_task

        except Exception as e:
            print(f"⚠️ Lỗi WebSocket: {e}")

            # đóng kết nối webrtc
            if pc:
                await pc.close()

            # đóng kết nối backend_server
            if backend_server_future.done() and not backend_server_future.cancelled():
                try:
                    backend_server = backend_server_future.result()
                    await backend_server.close()
                    backend_server_future = asyncio.Future()
                except Exception as e:
                    print(f"⚠️ Lỗi đóng kết nối backend: {e}")

    except Exception as e:
        print(f"⚠️ Lỗi không mong muốn trong websocket_endpoint: {e}")

    finally:
        print("Dọn dẹp tài nguyên...")

        if camera_manager:
            camera_manager.stop_camera()
            camera_manager = None
            print("Camera đã được dừng.")
        else:
            print("Camera manager không tồn tại.")

        if backend_server_future.done() and not backend_server_future.cancelled():
            try:
                backend_server = backend_server_future.result()
                await backend_server.close()
                backend_server_future = asyncio.Future()
            except Exception as e:
                print(f"⚠️ Lỗi đóng kết nối backend: {e}")


if __name__ == "__main__":

    # def signal_handler(sig, frame):
    #     print("🛑 Nhận tín hiệu tắt, dọn dẹp tài nguyên...")
    #     global ble_peripheral
    #     if ble_peripheral:
    #         ble_peripheral.stop()
    #     sys.exit(0)

    # signal.signal(signal.SIGINT, signal_handler)
    # signal.signal(signal.SIGTERM, signal_handler)

    # try:
    #     power_on_bluetooth_adapter_shell()
    #     ble_peripheral = BLEPeripheral()
    #     ble_thread = threading.Thread(target=ble_peripheral.start, daemon=True)
    #     ble_thread.start()
    # except Exception as e:
    #     power_on_bluetooth_adapter_shell()
    #     print(f"⚠️ Lỗi khởi tạo Bluetooth: {e}")

    # ! KHỞI ĐỘNG SERVER
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,  # Sử dụng 1 worker trên Raspberry Pi
        log_level="warning",  # Giảm logs để cải thiện hiệu suất
    )
