from bluezero import peripheral, adapter
import threading
import asyncio


class BLEPeripheral:
    def __init__(self, on_receive_callback=None):
        # UUID cho dịch vụ và characteristic
        self.service_uuid = "12345678-1234-5678-1234-56789abcdeff"
        self.char_uuid = "12345678-1234-5678-1234-56789abcdef0"
        self.on_receive_callback = on_receive_callback
        self.main_loop = None

        # Lấy địa chỉ adapter Bluetooth
        adapter_address = list(adapter.Adapter.available())[0].address

        # Tạo đối tượng Peripheral
        self.ble = peripheral.Peripheral(adapter_address=adapter_address)

        # Thêm dịch vụ
        print("Đã thêm dịch vụ:", self.service_uuid)
        self.ble.add_service(srv_id=1, uuid=self.service_uuid, primary=True)

        # Thêm characteristic
        print("Đã thêm characteristic:", self.char_uuid)
        self.ble.add_characteristic(
            srv_id=1,
            chr_id=1,
            uuid=self.char_uuid,
            value=[],
            notifying=True,
            flags=["read", "write", "notify"],
            write_callback=self._on_write,
        )

    def _on_write(self, value, options):
        try:
            message = bytes(value).decode("utf-8")
            print(f"📥 Nhận từ client: {message}")
            if self.on_receive_callback and self.main_loop:
                # Chạy coroutine một cách an toàn trong event loop chính từ một luồng khác
                asyncio.run_coroutine_threadsafe(
                    self.on_receive_callback(message), self.main_loop
                )
        except Exception as e:
            print(f"❌ Lỗi khi đọc dữ liệu: {e}")

    def send_message(self, message):
        try:
            if not self.ble.characteristics:
                print("❌ Không tìm thấy characteristic")
                return
                
            char = self.ble.characteristics[0]
            print(f"Characteristic found: {char}")
            encoded = message.encode("utf-8")
            print(f"Encoded message: {encoded}")
            char.set_value(encoded)
            char.notify(encoded)
            print(f"📤 Đã gửi: {message}")
        except Exception as e:
            print(f"❌ Lỗi khi gửi tin nhắn: {e}")
            return
    

    def start(self, loop=None):
        # Lưu event loop chính
        self.main_loop = loop or asyncio.get_event_loop()
        print("🚀 Đang quảng bá BLE, chờ client kết nối...")
        threading.Thread(target=self.ble.publish, daemon=True).start()

    def stop(self):
        print("🛑 Dừng BLE")
        # Hiện tại Bluezero không có stop rõ ràng
