import bluetooth
import json

class BluetoothManager:
    def __init__(self, uuid="94f39d29-7d6d-437d-973b-fba39e49d4ee"):
        self.uuid = uuid
        self.server_sock = None
        self.client_sock = None

    def start(self):
        self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_sock.bind(("", bluetooth.PORT_ANY))
        self.server_sock.listen(1)

        port = self.server_sock.getsockname()[1]
        print(f"📡 Chờ kết nối Bluetooth tại RFCOMM channel {port}")

        bluetooth.advertise_service(
            self.server_sock,
            "WebRTCSignalingServer",
            service_id=self.uuid,
            service_classes=[self.uuid, bluetooth.SERIAL_PORT_CLASS],
            profiles=[bluetooth.SERIAL_PORT_PROFILE],
        )

        self.client_sock, client_info = self.server_sock.accept()
        print(f"✅ Đã kết nối với {client_info}")

    def receive_json(self):
        raw = b""
        while not raw.endswith(b"\n"):
            chunk = self.client_sock.recv(1024)
            if not chunk:
                return None
            raw += chunk
        return json.loads(raw.decode("utf-8").strip())

    def send_json(self, data):
        message = json.dumps(data) + "\n"
        self.client_sock.send(message.encode("utf-8"))

    def close(self):
        if self.client_sock:
            self.client_sock.close()
        if self.server_sock:
            self.server_sock.close()
        print("🔌 Bluetooth signaling đã đóng")
