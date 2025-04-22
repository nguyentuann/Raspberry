import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
sys.path.append(parent_dir)

import asyncio
from aiortc import (
    RTCConfiguration,
    RTCIceCandidate,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
from iot.camera_manager import CameraManager
from iot.bluetooth_manager import BluetoothManager


async def handle_webrtc_via_bluetooth(camera_manager: CameraManager):
    signaling = BluetoothManager()
    signaling.start()

    configuration = RTCConfiguration(
        iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")]
    )
    pc = RTCPeerConnection(configuration)
    pc.addTrack(camera_manager)

    @pc.on("icecandidate")
    async def on_ice_candidate(candidate):
        if candidate:
            print("📡 Gửi ICE Candidate qua Bluetooth")
            signaling.send_json(
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
            data = signaling.receive_json()
            if data is None:
                break

            if data["type"] == "join":
                offer = await pc.createOffer()
                await pc.setLocalDescription(offer)
                signaling.send_json(
                    {
                        "type": "offer",
                        "offer": {
                            "sdp": pc.localDescription.sdp,
                            "type": pc.localDescription.type,
                        },
                    }
                )
                print("✅ Gửi Offer")

            elif data["type"] == "answer":
                print("✅ Nhận Answer")
                answer = data["answer"]
                await pc.setRemoteDescription(
                    RTCSessionDescription(sdp=answer["sdp"], type=answer["type"])
                )

            elif data["type"] == "candidate":
                print("✅ Nhận Candidate")
                candidate = data["candidate"]
                parts = candidate["candidate"].split()
                ice = RTCIceCandidate(
                    foundation=parts[0].split(":")[1],
                    component=int(parts[1]),
                    protocol=parts[2],
                    priority=int(parts[3]),
                    ip=parts[4],
                    port=int(parts[5]),
                    type=parts[7],
                    sdpMid=candidate["sdpMid"],
                    sdpMLineIndex=candidate["sdpMLineIndex"],
                )
                await pc.addIceCandidate(ice)
    except Exception as e:
        print(f"⚠️ Lỗi WebRTC Bluetooth: {e}")
    finally:
        await pc.close()
        signaling.close()


if __name__ == "__main__":
    camera = CameraManager()
    asyncio.run(handle_webrtc_via_bluetooth(camera_manager=camera))
