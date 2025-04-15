from aiortc import (
    RTCConfiguration,
    RTCIceCandidate,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
from fastapi import WebSocket
from iot.camera_manager import CameraManager  

async def handleWebRTC(websocket: WebSocket, camera_manager: CameraManager):

    """Xử lý WebRTC"""
    configuration = RTCConfiguration(
        iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")]
    )
    pc = RTCPeerConnection(configuration)
    pc.addTrack(camera_manager)

    @pc.on("icecandidate")
    async def on_ice_candidate(candidate):
        if candidate:
            print("📡 Gửi ICE Candidate đến client")
            await websocket.send_json(
                {
                    "type": "candidate",
                    "candidate": {
                        "candidate": candidate.to_sdp(),
                        "sdpMid": candidate.sdpMid,
                        "sdpMLineIndex": candidate.sdpMLineIndex,
                    },
                }
            )
    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "join":
                offer = await pc.createOffer()
                await pc.setLocalDescription(offer)
                await websocket.send_json(
                    {
                        "type": "offer",
                        "offer": {
                            "sdp": pc.localDescription.sdp,
                            "type": pc.localDescription.type,
                        },
                    }
                )
                print("✅ Đã gửi Offer")

            elif data["type"] == "answer":
                print("✅ Nhận Answer từ client")
                remoteDesc = RTCSessionDescription(
                    sdp=data["answer"]["sdp"], type=data["answer"]["type"]
                )
                await pc.setRemoteDescription(remoteDesc)

            elif data["type"] == "candidate":
                print('nhận candidate')
                candidate = data["candidate"]
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
        