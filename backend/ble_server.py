import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
sys.path.append(parent_dir)

import asyncio

from iot.camera_manager import CameraManager
from my_bluetooth.ble_peripheral import BLEPeripheral
from mobile.webrtc_bluetooth import create_ble_message_handler, handleWebRTC

async def main():
    # Khởi tạo camera và BLE
    camera_manager = CameraManager()
    ble = BLEPeripheral()

    # Bắt đầu quảng bá BLE với event loop hiện tại
    loop = asyncio.get_running_loop()
    ble.start(loop)

    # Thiết lập kết nối WebRTC
    pc, data_channel = await handleWebRTC(ble, camera_manager)

    # Gán hàm xử lý BLE nhận dữ liệu
    ble.on_receive_callback = create_ble_message_handler(pc, ble)

    # Duy trì vòng lặp chạy vĩnh viễn
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
