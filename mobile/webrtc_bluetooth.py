import bluetooth
import json
from aiortc import (
    RTCConfiguration,
    RTCIceCandidate,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
from iot.camera_manager import CameraManager  

# Thiết lập Bluetooth server RFCOMM
def setup_bluetooth():
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)

    print("👂 Đang chờ kết nối Bluetooth...")
    client_sock, address = server_sock.accept()
    print(f"📲 Kết nối từ {address}")

    return client_sock

# Xử lý WebRTC
async def handleWebRTC(client_sock, camera_manager: CameraManager):

    """Xử lý WebRTC và nhận tín hiệu qua Bluetooth"""
    configuration = RTCConfiguration(
        iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")]
    )
    pc = RTCPeerConnection(configuration)
    pc.addTrack(camera_manager)

    @pc.on("icecandidate")
    async def on_ice_candidate(candidate):
        if candidate:
            print("📡 Gửi ICE Candidate đến client qua Bluetooth")
            # Gửi ICE candidate qua Bluetooth
            message = {
                "type": "candidate",
                "candidate": {
                    "candidate": candidate.to_sdp(),
                    "sdpMid": candidate.sdpMid,
                    "sdpMLineIndex": candidate.sdpMLineIndex,
                },
            }
            client_sock.send(json.dumps(message).encode())

    try:
        while True:
            # Nhận tín hiệu từ Bluetooth
            data = client_sock.recv(4096).decode()
            if not data:
                break
            print(f"📩 Nhận từ mobile qua Bluetooth: {data}")

            # Chuyển đổi JSON từ dữ liệu nhận được
            data_json = json.loads(data)

            if data_json["type"] == "join":
                offer = await pc.createOffer()
                await pc.setLocalDescription(offer)
                message = {
                    "type": "offer",
                    "offer": {
                        "sdp": pc.localDescription.sdp,
                        "type": pc.localDescription.type,
                    },
                }
                print("✅ Đã gửi Offer qua Bluetooth")
                client_sock.send(json.dumps(message).encode())

            elif data_json["type"] == "answer":
                print("✅ Nhận Answer từ client")
                remoteDesc = RTCSessionDescription(
                    sdp=data_json["answer"]["sdp"], type=data_json["answer"]["type"]
                )
                await pc.setRemoteDescription(remoteDesc)

            elif data_json["type"] == "candidate":
                print('nhận candidate')
                candidate = data_json["candidate"]
                parts = candidate["candidate"].split()

                foundation = parts[0].split(":")[1]
                component = int(parts[1])
                protocol = parts[2]
                priority = int(parts[3])
                ip = parts[4]
                port = int(parts[5])
                candidate_type = parts[7]

                # Kiểm tra candidate có đủ thông tin cần thiết
                if (
                    "sdpMid" in candidate
                    and candidate["sdpMid"] is not None
                    and "sdpMLineIndex" in candidate
                    and "candidate" in candidate
                ):
                    # Chỉ thêm candidate nếu đã có remoteDescription
                    if pc.remoteDescription is None:
                        print("Chưa có remoteDescription, bỏ qua ICE Candidate")
                    else:
                        try:
                            ice_candidate = RTCIceCandidate(
                                component=component,
                                foundation=foundation,
                                ip=ip,
                                port=port,
                                priority=priority,
                                protocol=protocol,
                                type=candidate_type,
                                sdpMid=candidate["sdpMid"],
                                sdpMLineIndex=candidate["sdpMLineIndex"],
                            )
                            await pc.addIceCandidate(ice_candidate)
                            print("Done")
                        except Exception as e:
                            print("Lỗi khi thêm ICE Candidate:", e)

    except Exception as e:
        print(f"⚠️ Lỗi WebRTC: {e}")
    finally:
        await pc.close()
        client_sock.close()


async def main():
    # Setup Bluetooth server và nhận kết nối từ mobile app
    client_sock = setup_bluetooth()

    # Khởi tạo camera manager (giả sử bạn đã cài đặt camera_manager)
    camera_manager = CameraManager()

    # Xử lý WebRTC
    await handleWebRTC(client_sock, camera_manager)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
