from bluezero import peripheral
from bluezero import adapter
import time
import subprocess
import os

import socket

from dbus import SystemBus


def get_real_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

# ! TẮT BLUETOOTH
def turn_off_bluetooth():
    try:
        print("⛔ Đang tắt thiết bị Bluetooth...")
        subprocess.run(["sudo", "hciconfig", "hci0", "down"], check=True)
        subprocess.run(["sudo", "rfkill", "block", "bluetooth"], check=True)
        print("🛑 Bluetooth đã được tắt hoàn toàn.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Lỗi khi tắt Bluetooth: {e}")
    except Exception as e:
        print(f"⚠️ Lỗi không xác định khi tắt Bluetooth: {e}")

# ! BẬT BLUETOOTH      
def power_on_bluetooth_adapter_shell():
    try:
        print("🔓 Mở khóa Bluetooth nếu đang bị block...")
        subprocess.run(["sudo", "rfkill", "unblock", "bluetooth"], check=True)

        print("⚙️ Bật thiết bị Bluetooth adapter...")
        subprocess.run(["sudo", "hciconfig", "hci0", "up"], check=True)

        print("✅ Bluetooth adapter đã được bật.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Không thể bật Bluetooth: {e}")
    except Exception as e:
        print(f"⚠️ Lỗi không xác định khi bật Bluetooth: {e}")



class BLEPeripheral:
    def __init__(self):
        self.service_uuid = "12345678-1234-5678-1234-56789abcdeff"
        self.char_uuid = "12345678-1234-5678-1234-56789abcdef0"

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

    def start(self):
        print("📡 Đang quảng bá BLE, chờ kết nối từ client...")
        self.ble.local_name = "GymBot"
        self.name = "GymBot"
        self.ble.publish()

    def stop(self):
        turn_off_bluetooth()
        print("🛑 Dừng quảng bá BLE.")


