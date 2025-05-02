from aiortc import (
    RTCConfiguration,
    RTCIceCandidate,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
from iot.camera_manager import CameraManager
from my_bluetooth.ble_peripheral import BLEPeripheral

import json


def create_ble_message_handler(pc: RTCPeerConnection, ble: BLEPeripheral):
    async def handle_message(message: str):
        try:
            data = json.loads(message)
            print(f"data: {data}")
            if data["type"] == "join":
                offer = await pc.createOffer()
                await pc.setLocalDescription(offer)
                await ble.send_message(
                    json.dumps(
                        {
                            "type": "offer",
                            "offer": {
                                "sdp": pc.localDescription.sdp,
                                "type": pc.localDescription.type,
                            },
                        }
                    )
                )
                print("✅ Đã gửi offer tới client")

            elif data["type"] == "answer":
                remoteDesc = RTCSessionDescription(
                    sdp=data["answer"]["sdp"], type=data["answer"]["type"]
                )
                await pc.setRemoteDescription(remoteDesc)
                print("✅ Nhận answer và thiết lập remote description")

            elif data["type"] == "candidate":
                candidate = data["candidate"]
                parts = candidate["candidate"].split()
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
                print("✅ Đã thêm ICE Candidate")
        except Exception as e:
            print("⚠️ Lỗi khi thêm ICE Candidate:", e)

    return handle_message


async def handleWebRTC(ble: BLEPeripheral, camera_manager: CameraManager):
    configuration = RTCConfiguration(
        iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")]
    )
    pc = RTCPeerConnection(configuration)
    pc.addTrack(camera_manager)

    dataChannel = pc.createDataChannel("sendError")

    @pc.on("icecandidate")
    async def on_ice_candidate(candidate):
        if candidate:
            await ble.send_message(
                json.dumps(
                    {
                        "type": "candidate",
                        "candidate": {
                            "candidate": candidate.to_sdp(),
                            "sdpMid": candidate.sdpMid,
                            "sdpMLineIndex": candidate.sdpMLineIndex,
                        },
                    }
                )
            )

    return pc, dataChannel
