from bluezero import peripheral
from bluezero import adapter
import time

# Callback khi nhận tin nhắn từ client
def on_write(value, options):
    try:
        message = bytes(value).decode('utf-8')
        print(f'Tin nhắn nhận được từ client: {message}')
    except Exception as e:
        print(f'Lỗi khi xử lý tin nhắn: {e}')

# Tạo dịch vụ BLE
class BLEPeripheral:
    def __init__(self):
        # UUID cho dịch vụ và characteristic
        self.service_uuid = '12345678-1234-5678-1234-56789abcdeff'
        self.char_uuid = '12345678-1234-5678-1234-56789abcdef0'

        # Lấy địa chỉ adapter Bluetooth
        adapter_address = list(adapter.Adapter.available())[0].address

        # Tạo đối tượng Peripheral với adapter_address
        self.ble = peripheral.Peripheral(adapter_address=adapter_address)

        # Thêm dịch vụ với UUID và Service ID
        self.ble.add_service(srv_id=1, uuid=self.service_uuid, primary=True)

        # Thêm characteristic với quyền đọc/ghi
        self.ble.add_characteristic(
            srv_id=1,  # ID của dịch vụ mà characteristic thuộc về
            chr_id=1,  # ID của characteristic
            uuid=self.char_uuid,
            value=[],
            notifying=False,
            flags=['read', 'write'],
            write_callback=on_write
        )

    def start(self):
        print("Đang quảng bá BLE, chờ kết nối từ client...")
        print("Nhấn Ctrl+C để dừng")
        self.ble.publish()

    def stop(self):
        print("Dừng quảng bá BLE")
        return

if __name__ == '__main__':
    ble_peripheral = None  # Đảm bảo biến được định nghĩa
    try:
        ble_peripheral = BLEPeripheral()
        ble_peripheral.start()

        # Vòng lặp vô hạn cho đến khi bị ngắt
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nNgắt kết nối BLE và thoát...")
    except Exception as e:
        print(f"⚠️ Lỗi: {e}")
    finally:
        if ble_peripheral:
            ble_peripheral.stop()
