import asyncio
from aiortc import (
    RTCConfiguration,
    RTCIceCandidate,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
from fastapi import WebSocket, WebSocketDisconnect
from iot.camera_manager import CameraManager

class WebRTCHandler:
    def __init__(self):
        pass

    async def receive_signaling(
        self,
        client_socket: WebSocket,
        pc: RTCPeerConnection,
        camera_manager: CameraManager,
    ):
        print("truoc goi start camera")
        camera_manager.connections += 1
        camera_manager.start_camera()
        pc.addTrack(camera_manager)
        print(pc.connectionState)

        # ! GỬI VÀ NHẬN CÁC GÓI TIN
        try:
            while True:
                data = await client_socket.receive_json()

                if data["type"] == "offer":
                    print(f"Nhận offer từ client: {data}")
                    if pc.connectionState == "closed" or pc.signalingState == "closed":
                        print("❌ Không thể xử lý offer vì pc kết nối đã đóng.")
                        return
                    # Nhận offer từ client và thiết lập remote description
                    remoteDesc = RTCSessionDescription(
                        sdp=data["data"]["sdp"], type=data["data"]["type"]
                    )

                    await pc.setRemoteDescription(remoteDesc)

                    # Tạo answer và gửi lại cho client
                    answer = await pc.createAnswer()
                    await pc.setLocalDescription(answer)
                    await client_socket.send_json(
                        {
                            "type": "answer",
                            "data": {
                                "sdp": pc.localDescription.sdp,
                                "type": pc.localDescription.type,
                            },
                        }
                    )
                    print("Đã gửi answer về client")

                elif data["type"] == "icecandidate":
                    candidate = data["data"]
                    print(f"Nhận ICE candidate từ client: {candidate}")
                    parts = candidate["candidate"].split()
                    try:
                        ice_fields = {
                            "foundation": parts[0].split(":")[1],
                            "component": int(parts[1]),
                            "protocol": parts[2],
                            "priority": int(parts[3]),
                            "ip": parts[4],
                            "port": int(parts[5]),
                        }

                        # Tìm các trường theo cặp khóa-giá trị
                        for i in range(6, len(parts), 2):
                            key = parts[i]
                            if i + 1 < len(parts):
                                value = parts[i + 1]
                                ice_fields[key] = value

                        ice_candidate = RTCIceCandidate(
                            foundation=ice_fields["foundation"],
                            component=ice_fields["component"],
                            protocol=ice_fields["protocol"],
                            priority=ice_fields["priority"],
                            ip=ice_fields["ip"],
                            port=ice_fields["port"],
                            type=ice_fields.get("typ", "host"),
                            sdpMid=candidate["sdpMid"],
                            sdpMLineIndex=candidate["sdpMLineIndex"],
                        )
                        await pc.addIceCandidate(ice_candidate)
                    except Exception as e:
                        print(f"⚠️ Lỗi khi thêm ICE Candidate: {e}")

        except WebSocketDisconnect:
            print("❌ WebSocket disconnected")
        except Exception as e:
            print(f"⚠️ Lỗi không mong muốn trong receive_signaling: {e}")
        finally:
            await pc.close()

    # ! XỬ LÝ TÍN HIỆU TỪ CLIENT ĐỂ THIẾT LẬP WEBRTC
    async def handleWebRTC(self, client_socket: WebSocket):
        # Cấu hình RTC với STUN server
        configuration = RTCConfiguration(
            iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")]
        )
        pc = RTCPeerConnection(configuration)

        data_channel_ready = asyncio.get_event_loop().create_future()

        @pc.on("datachannel")
        def on_datachannel(channel):
            data_channel_ready.set_result(channel)

        # Gửi ICE candidate về client
        @pc.on("candidate")
        async def on_ice_candidate(event):
            if event.candidate:
                try:
                    # Gửi ICE candidate về client qua WebSocket
                    await client_socket.send_json(
                        {
                            "type": "icecandidate",
                            "data": {
                                "candidate": event.candidate.to_sdp(),
                                "sdpMid": event.candidate.sdpMid,
                                "sdpMLineIndex": event.candidate.sdpMLineIndex,
                            },
                        }
                    )
                    print("Đã gửi ICE candidate về client")
                except Exception as e:
                    print(f"⚠️ Lỗi khi gửi ICE candidate: {e}")

        # Trả về pc và dataChannel sau khi thiết lập xong
        return pc, data_channel_ready