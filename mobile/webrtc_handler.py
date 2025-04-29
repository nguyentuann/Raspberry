from aiortc import (
    RTCConfiguration,
    RTCIceCandidate,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
from fastapi import WebSocket
from iot.camera_manager import CameraManager  

# async def handleWebRTC(client_socket: WebSocket, camera_manager: CameraManager):

#     """Xử lý WebRTC"""
#     configuration = RTCConfiguration(
#         iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")]
#     )
#     pc = RTCPeerConnection(configuration)
#     # pc.addTrack(camera_manager)
    
    
#     # Xử lý datachannel
#     dataChannel = pc.createDataChannel("sendError")
    
#     @dataChannel.on("open")
#     def openDataChannel():
#         dataChannel.send("Hello World")
    
#     @dataChannel.on("message")
#     def sendMessage(messsage):
#         dataChannel.send(messsage)
        
#     # ----------------------------- #

#     # Kết nối WebRTC
#     @pc.on("icecandidate")
#     async def on_ice_candidate(candidate):
#         if candidate:
#             print("📡 Gửi ICE Candidate đến client")
#             await client_socket.send_json(
#                 {
#                     "type": "candidate",
#                     "candidate": {
#                         "candidate": candidate.to_sdp(),
#                         "sdpMid": candidate.sdpMid,
#                         "sdpMLineIndex": candidate.sdpMLineIndex,
#                     },
#                 }
#             )
#     try:
#         while True:
#             data = await client_socket.receive_json()

#             if data["type"] == "join":
#                 offer = await pc.createOffer()
#                 await pc.setLocalDescription(offer)
#                 await client_socket.send_json(
#                     {
#                         "type": "offer",
#                         "offer": {
#                             "sdp": pc.localDescription.sdp,
#                             "type": pc.localDescription.type,
#                         },
#                     }
#                 )
#                 print("✅ Đã gửi Offer")

#             elif data["type"] == "answer":
#                 print("✅ Nhận Answer từ client")
#                 remoteDesc = RTCSessionDescription(
#                     sdp=data["answer"]["sdp"], type=data["answer"]["type"]
#                 )
#                 await pc.setRemoteDescription(remoteDesc)

#             elif data["type"] == "candidate":
#                 print('nhận candidate')
#                 candidate = data["candidate"]
#                 parts = candidate["candidate"].split()

#                 foundation = parts[0].split(":")[1]
#                 component = int(parts[1])
#                 protocol = parts[2]
#                 priority = int(parts[3])
#                 ip = parts[4]
#                 port = int(parts[5])
#                 candidate_type = parts[7]

#                 # Kiểm tra candidate có đủ thông tin cần thiết
#                 if (
#                     "sdpMid" in candidate
#                     and candidate["sdpMid"] is not None
#                     and "sdpMLineIndex" in candidate
#                     and "candidate" in candidate
#                 ):
#                     # Chỉ thêm candidate nếu đã có remoteDescription
#                     if pc.remoteDescription is None:
#                         print("Chưa có remoteDescription, bỏ qua ICE Candidate")
#                     else:
#                         try:

#                             ice_candidate = RTCIceCandidate(
#                                 component=component,
#                                 foundation=foundation,
#                                 ip=ip,
#                                 port=port,
#                                 priority=priority,
#                                 protocol=protocol,
#                                 type=candidate_type,
#                                 sdpMid=candidate["sdpMid"],
#                                 sdpMLineIndex=candidate["sdpMLineIndex"],
#                             )
#                             await pc.addIceCandidate(ice_candidate)
#                             print("Done")
#                         except Exception as e:
#                             print("Lỗi khi thêm ICE Candidate:", e)

#     except Exception as e:
#         print(f"⚠️ Lỗi WebRTC: {e}")
#     finally:
#         await pc.close()
        
#     return dataChannel
        
async def receive_signaling(client_socket, pc):
    
    """Xử lý signaling từ WebSocket client để thiết lập WebRTC"""
    while True:
        data = await client_socket.receive_json()

        if data["type"] == "join":
            offer = await pc.createOffer()
            await pc.setLocalDescription(offer)
            await client_socket.send_json({
                "type": "offer",
                "offer": {
                    "sdp": pc.localDescription.sdp,
                    "type": pc.localDescription.type,
                },
            })
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
                print("✅ Đã thêm ICE Candidate")
            except Exception as e:
                print("⚠️ Lỗi khi thêm ICE Candidate:", e)



async def handleWebRTC(client_socket: WebSocket, camera_manager: CameraManager):
    configuration = RTCConfiguration(
        iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")]
    )
    pc = RTCPeerConnection(configuration)
    pc.addTrack(camera_manager)

    # thiết lập dataChannel
    dataChannel = pc.createDataChannel("sendError")

    # Gửi ICE candidate về client
    @pc.on("icecandidate")
    async def on_ice_candidate(candidate):
        if candidate:
            await client_socket.send_json({
                "type": "candidate",
                "candidate": {
                    "candidate": candidate.to_sdp(),
                    "sdpMid": candidate.sdpMid,
                    "sdpMLineIndex": candidate.sdpMLineIndex,
                },
            })

    # ✅ Trả về pc và dataChannel ngay sau khi thiết lập xong
    return pc, dataChannel