import asyncio
import json
from aiortc import RTCDataChannel
import websockets
from iot.camera_manager import CameraManager
from constant.ip_backend import uri_backend
from iot.speaker import speaker_output


def setup_data_channel(
    dataChannel: RTCDataChannel,
    backend_server_future: asyncio.Future,
    camera_manager: CameraManager,
):
    send_keypoints_task = None
    receive_error_task = None

    async def on_message(message):
        nonlocal send_keypoints_task, receive_error_task, backend_server_future

        try:
            req = json.loads(message)
            print(f"📥 Đã nhận: {req}")

            key = req.get("key", "").upper()

            # Bắt đầu training
            if key == "TRAINING":
                print("nhận yêu cầu training")
                data = req["data"]
                exerciseId = data["exercise_id"]
                workoutSummaryId = None if data["workout_summary_id"] == "" else data["workout_summary_id"]
                userId = data["user_id"]
                config = data["config"]

                if not backend_server_future.done():
                    print("kết nối server backend")
                    ws_url = uri_backend(userId, exerciseId, workoutSummaryId)
                    print(ws_url)
                    backend_server = await websockets.connect(ws_url)
                    backend_server_future.set_result(backend_server)
                    print("✅ Kết nối đến backend_server thành công")

            elif key == "REQUEST_TRAINING":
                data = req.get("data", "").upper()
                if data == "START":
                    print("bắt đầu")
                    if backend_server_future.done():
                        print("kết nối server backend xong")
                        backend_server = backend_server_future.result()
                        send_keypoints_task = asyncio.create_task(
                            camera_manager._send_keypoints(backend_server)
                        )
                        receive_error_task = asyncio.create_task(
                            speaker_output(
                                dataChannel,
                                backend_server_future,
                            )
                        )

                    else:
                        print(
                            "⚠️ Chưa có kết nối đến backend server. Hãy gửi TRAINING trước."
                        )

                elif data == "PAUSE":
                    print("tạm dừng")
                    if send_keypoints_task:
                        send_keypoints_task.cancel()
                        send_keypoints_task = None
                        print("✅ Đã dừng gửi keypoints")
                        
                    if receive_error_task:
                        receive_error_task.cancel()
                        receive_error_task = None
                        print("✅ Đã dừng phát âm thanh")
                        
                    if backend_server_future.done():
                        backend_server = backend_server_future.result()
                        await backend_server.close()
                        print("✅ Đã ngắt kết nối đến backend_server")

                elif data == "STOP":
                    print("dừng lại")
                    if send_keypoints_task:
                        send_keypoints_task.cancel()
                        send_keypoints_task = None
                        print("✅ Đã dừng gửi keypoints")

                    if backend_server_future.done():
                        backend_server = backend_server_future.result()
                        await backend_server.close()
                        print("✅ Đã ngắt kết nối đến backend_server")
                        backend_server_future = asyncio.Future()

                    if dataChannel and dataChannel.readyState == "open":
                        await dataChannel.close()
                        print("✅ Đã ngắt kết nối WebRTC")

        except json.JSONDecodeError:
            print(f"⚠️ Lỗi JSON không hợp lệ: {message}")
        except Exception as e:
            print(f"⚠️ Lỗi không xác định: {e}")

    dataChannel.on("message", lambda msg: asyncio.create_task(on_message(msg)))


async def send_data(dataChannel, key, data):
    if dataChannel and dataChannel.readyState == "open":
        payload = json.dumps({"key": key, "data": data})
        await dataChannel.send(payload)
        print(f"📤 Đã gửi: {payload}")
    else:
        print("⚠️ dataChannel chưa sẵn sàng để gửi.")
