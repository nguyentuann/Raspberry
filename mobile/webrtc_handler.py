import asyncio
from aiortc import (
    RTCConfiguration,
    RTCDataChannel,
    RTCIceCandidate,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
from fastapi import WebSocket
from iot.camera_manager import CameraManager




async def receive_signaling(
    client_socket: WebSocket, pc: RTCPeerConnection, camera_manager: CameraManager
):
    pc.addTrack(camera_manager)

    """Xử lý signaling từ WebSocket client để thiết lập WebRTC"""
    while True:
        data = await client_socket.receive_json()

        if data["type"] == "offer":
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

        elif data["type"] == "icecandidate":
            candidate = data["data"]
            parts = candidate["candidate"].split()
            try:
                ice_candidate = RTCIceCandidate(
                    component=int(parts[1]),
                    foundation=parts[0].split(":")[1],
                    ip=parts[4],
                    port=int(parts[5]),
                    priority=int(parts[3]),
                    protocol=parts[2],
                    type=parts[7],
                    sdpMid=candidate["sdpMid"],
                    sdpMLineIndex=candidate["sdpMLineIndex"],
                )
                await pc.addIceCandidate(ice_candidate)
            except Exception as e:
                print(f"⚠️ Lỗi khi thêm ICE Candidate: {e}")


async def handleWebRTC(client_socket: WebSocket):
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
            except Exception as e:
                print(f"⚠️ Lỗi khi gửi ICE candidate: {e}")

    # Trả về pc và dataChannel sau khi thiết lập xong
    return pc, data_channel_ready
