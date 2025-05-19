import json
import time
import asyncio
import websockets

from aiortc import RTCDataChannel

from iot.speaker import Speaker
from iot.camera_manager import CameraManager

from helper.buffer import Buffer
from helper.ip_backend import uri_backend
from helper.data_format import dataChannel_response

# ! THIẾT LẬP DATA CHANNEL
def setup_data_channel(
    dataChannel: RTCDataChannel,
    backend_server_future: asyncio.Future,
    camera_manager: CameraManager,
):
    tasks = []  # lưu trữ các task để hủy
    send_keypoints_task = None
    receive_error_task = None
    user_id = None
    exercise_id = None
    config = None
    state = {"workout_summary_id": None, "session_id": None}
    buffer = Buffer()
    
    # ! HÀM GỬI URL ẢNH CHO BACKEND
    async def send_url_buffer(buffer: Buffer, backend_server_future: asyncio.Future):
        if backend_server_future.done():
            backend_server = backend_server_future.result()
            url_buffer = buffer.image_url_buffer.copy()
            if url_buffer:
                try:
                    await backend_server.send(json.dumps({
                        "key": "IMAGE_BUFFER",
                        "data": url_buffer
                    }))
                    print("📤 Đã gửi image_url_buffer tới backend.")
                except Exception as e:
                    print(f"⚠️ Không thể gửi image_url_buffer: {e}")
            buffer.image_url_buffer.clear()
        else:
            print("⚠️ Backend chưa kết nối. Không gửi được image_url_buffer.")

    # ! HÀM DỌN DẸP TRAINING
    async def cleanup_training(close_channel=False):
        nonlocal send_keypoints_task, receive_error_task, backend_server_future

        print("🧹 Đang dọn dẹp training...")

        # Gọi hàm gửi url ảnh cho backend
        # await send_url_buffer(buffer, backend_server_future)

        # Hủy các task
        for task, name in [(send_keypoints_task, "keypoints"), (receive_error_task, "phát âm thanh")]:
            if task and not task.done():
                task.cancel()
                print(f"✅ Đã dừng {name}")
        
        send_keypoints_task = None
        receive_error_task = None

        # Đóng backend
        if backend_server_future.done():
            backend_server = backend_server_future.result()
            await backend_server.close()
            backend_server_future = asyncio.Future()
            print("✅ Đã đóng backend và reset future.")

        # Đóng dataChannel nếu được yêu cầu
        if close_channel and dataChannel and dataChannel.readyState == "open":
            await dataChannel.close()
            print("✅ Đã đóng dataChannel.")

    # ! KẾT NỐI TỚI BACKEND
    async def connect_backend(user_id, exercise_id, summary_id):
        if not backend_server_future.done():
            print("🔗 Đang kết nối tới backend...")
            ws_url = uri_backend(user_id, exercise_id, summary_id)
            print(ws_url)
           
            start_time = time.time()
            while True:
                try:
                    backend_server = await websockets.connect(ws_url)
                    backend_server_future.set_result(backend_server)
                    print("✅ Đã kết nối tới backend.")

                    if dataChannel is not None and dataChannel.readyState == "open":
                        dataChannel.send(dataChannel_response("STATUS", "OK"))
                    break  # thoát vòng lặp khi kết nối thành công

                except Exception as e:
                    print(f"⚠️ Kết nối backend thất bại: {e}")
                    if time.time() - start_time > 30:
                        print("⏰ Hết thời gian thử kết nối (30 giây), ngưng retry.")
                        break
                    await asyncio.sleep(2)
        else:
            print("Backend đã được kết nối trước đó.")

    # ! BẮT ĐẦU TRAINING
    async def start_training():
        nonlocal send_keypoints_task, receive_error_task
        if backend_server_future.done():
            backend_server = backend_server_future.result()
            print(f"backend_server: {backend_server}")
            
            speaker = Speaker(state, dataChannel, backend_server_future, config, buffer)

            # Tạo task phát âm thanh
            receive_error_task = asyncio.create_task(
                speaker.speaker_output()
            )
            
            while state.get("session_id") is None:
                print("⏳ Chờ session id được cập nhật...")
                await asyncio.sleep(0.1)
            
            send_keypoints_task = asyncio.create_task(
                camera_manager._send_keypoints(backend_server, user_id, state, buffer)
            )

            
            tasks.extend([send_keypoints_task, receive_error_task])
            
            print("▶️ Đã bắt đầu gửi keypoints và nhận lỗi.")
        else:
            print("⚠️ Chưa kết nối backend. Vui lòng gửi TRAINING trước.")

    # ! TẠM DỪNG TRAINING
    async def pause_training():
        print("⏸️ Tạm dừng training...")
        if dataChannel.readyState == "open":
            dataChannel.send(dataChannel_response("STATUS", "OK"))
        await cleanup_training(close_channel=False)

    # ! DỪNG TRAINING
    async def stop_training():
        print("🛑 Dừng training...")
        await cleanup_training(close_channel=True)

    # ! NHẬN DỮ LIỆU TỪ DATA CHANNEL
    async def on_message(message):
        nonlocal config, user_id, exercise_id
        try:
            req = json.loads(message)
            print(f"📥 Đã nhận: {req}")
            key = req.get("key", "").upper()

            if key == "TRAINING":
                data = req["data"]
                state["workout_summary_id"] = data["workout_summary_id"] or None
                user_id = data["user_id"]
                exercise_id = data["exercise_id"]
                config = data["config"]["mute"] != True
                await connect_backend(user_id, exercise_id, state["workout_summary_id"])

            elif key == "REQUEST_TRAINING":
                data = req.get("data", "").upper()
                if data == "START":
                    await start_training()
                elif data == "PAUSE":
                    await pause_training()
                elif data == "STOP":
                    await stop_training()

        except json.JSONDecodeError:
            print(f"⚠️ JSON không hợp lệ: {message}")
        except Exception as e:
            print(f"⚠️ Lỗi không xác định: {e}")
            
    #  ! ĐÓNG DATA CHANNEL VÀ DỌN DẸP TÀI NGUYÊN
    def on_close():
        print("⚠️ DataChannel đã đóng, hủy các task...")
        for task in tasks:
            if task and not task.done():
                task.cancel()
        if backend_server_future.done():
            backend_server = backend_server_future.result()
            asyncio.create_task(backend_server.close())


    dataChannel.on("message", lambda msg: asyncio.create_task(on_message(msg)))
    dataChannel.on("close", on_close)

# ! GỬI DỮ LIỆU QUA DATA CHANNEL
async def send_data(dataChannel: RTCDataChannel, key: str, data: dict):
    if dataChannel and dataChannel.readyState == "open":
        payload = json.dumps({"key": key, "data": data})
        await dataChannel.send(payload)
        print(f"📤 Đã gửi: {payload}")
    else:
        print("⚠️ dataChannel chưa sẵn sàng để gửi.")


