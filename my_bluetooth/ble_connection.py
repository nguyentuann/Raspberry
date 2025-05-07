import base64
from bluezero import peripheral
from bluezero import adapter
import time

import socket


def get_real_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


class BLEPeripheral:
    def __init__(self):
        self.service_uuid = "12345678-1234-5678-1234-56789abcdeff"
        self.char_uuid = "12345678-1234-5678-1234-56789abcdef0"
        self.last_message = ""  # Biến lưu tin nhắn nhận được từ Flutter

        adapters = list(adapter.Adapter.available())
        if not adapters:
            raise RuntimeError("❌ Không tìm thấy adapter BLE nào.")
        self.adapter_address = adapters[0].address
        print(f"✅ Adapter Bluetooth được phát hiện: {self.adapter_address}")

        # Tạo Peripheral
        self.ble = peripheral.Peripheral(adapter_address=self.adapter_address)
        print("✅ Peripheral đã được khởi tạo thành công.")

        # Thêm dịch vụ
        self.ble.add_service(srv_id=1, uuid=self.service_uuid, primary=True)
        print("✅ Dịch vụ đã được thêm thành công.")

        # Thêm characteristic có thể đọc và ghi
        try:
            self.ble.add_characteristic(
                srv_id=1,
                chr_id=1,
                uuid=self.char_uuid,
                value=[0x00],
                notifying=False,  # Tắt notifying để đơn giản hóa
                flags=["read", "write"],
                read_callback=self.on_read,
                # write_callback=self.on_write,
            )
            print("✅ Characteristic đã được thêm thành công.")
        except Exception as e:
            print(f"⚠️ Không thể tạo characteristic: {e}")
            raise RuntimeError(
                "⚠️ Không thể khởi tạo characteristic. Dừng chương trình."
            )

    def on_read(self):
        response = get_real_local_ip()
        return [ord(c) for c in response]

    # def on_write(self, value, options):
    #     try:
    #         message = bytes(value).decode("utf-8")
    #         if (
    #             len(message) > 16
    #         ):  # Giới hạn tin nhắn để tổng "OK: " + tin nhắn < 20 byte
    #             print(f"⚠️ [{time.time()}] Tin nhắn quá dài: {message}")
    #             return
    #         self.last_message = message  # Lưu tin nhắn nhận được
    #         print(f"📥 [{time.time()}] Tin nhắn nhận được từ client: {message}")
    #     except Exception as e:
    #         print(f"⚠️ [{time.time()}] Lỗi khi xử lý tin nhắn: {e}")

    def start(self):
        print("📡 Đang quảng bá BLE, chờ kết nối từ client...")
        self.ble.publish()

    def stop(self):
        print("🛑 Dừng quảng bá BLE.")


if __name__ == "__main__":
    ble_peripheral = None
    try:
        ble_peripheral = BLEPeripheral()
        ble_peripheral.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🧹 Ngắt kết nối BLE và thoát...")
    except Exception as e:
        print(f"⚠️ Lỗi: {e}")
    finally:
        if ble_peripheral:
            ble_peripheral.stop()
