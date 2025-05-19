import io
import cv2
import time
import gtts
import json
import pygame
import aiohttp
import asyncio
from aiortc import RTCDataChannel
from helper.buffer import Buffer
from helper.data_format import dataChannel_response, data_backend_response
from helper.ip_backend import url_upload_image

image_path = "/home/nhattuan/Desktop/Raspberry/image"


class Speaker:
    def __init__(
        self,
        state: dict,
        dataChannel: RTCDataChannel,
        backend_server_future: asyncio.Future,
        config: bool,
        buffer: Buffer,
    ):
        self.state = state
        self.dataChannel = dataChannel
        self.backend_server_future = backend_server_future
        self.config = config
        self.buffer = buffer
        self.audio_queue = asyncio.Queue()
        self.first_msg = True


    # ! HÀM PHÁT ÂM THANH
    async def audio_player_loop(self):
        pygame.mixer.init()
        while True:
            try:
                content = await self.audio_queue.get()
                print(f"🔊 Đang phát âm thanh: {content}")
                tts = gtts.gTTS(content, lang="vi")
                audio = io.BytesIO()
                tts.write_to_fp(audio)
                audio.seek(0)

                pygame.mixer.music.load(audio, "mp3")
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)

            except Exception as e:
                print(f"⚠️ Lỗi trong audio_player_loop: {e}")
                await asyncio.sleep(1)

    # ! GỌI API ĐỂ UPLOAD ẢNH
    async def call_api_upload_image(self, frame):
        url = url_upload_image()
        _, img_encoded = cv2.imencode(".jpg", frame)
        img_bytes = img_encoded.tobytes()
        file = io.BytesIO(img_bytes)

        file.name = f"{time.time_ns()}.jpg"  # fake a filename

        # Send POST request with file
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("file", file, filename=file.name, content_type="image/jpeg")

            async with session.post(url, data=data) as resp:
                if resp.status == 200:
                    response_data = await resp.json()
                    return response_data.get("data")
                else:
                    print(f"[ERROR] Upload failed: {resp.status}")
                    return None

    # ! LẤY ẢNH LỖI
    async def handle_error_frame(self, image_id, rep_index, session_id, content):
        frame_buffer = self.buffer.frame_buffer
        image_url_buffer = self.buffer.image_url_buffer

        if frame_buffer:
            print(len(frame_buffer))
            frame = frame_buffer[image_id]
            frame_buffer.clear()

            url = await self.call_api_upload_image(frame)
            print(f"Đã nhận url: {url}")    
            if url:
                data = data_backend_response(rep_index, url)
                image_url_buffer[session_id].append(data)
            else:
                print(f"[ERROR] Upload failed for session_id: {session_id}")

    # ! HÀM CHÍNH
    async def speaker_output(self):
        first_msg = True
        backend_server = await self.backend_server_future

        # Khởi động luồng phát âm thanh
        asyncio.create_task(self.audio_player_loop())

        while True:
            try:
                response_json = await backend_server.recv()
                response = json.loads(response_json)

                print(f"📥 Nhận phản hồi từ backend: {response}")

                if self.first_msg:
                    self.first_msg = False
                    self.state["workout_summary_id"] = response["workout_summary_id"]
                    self.state["session_id"] = response["session_id"]
                    self.dataChannel.send(
                        dataChannel_response(
                            "RESPONSE_TRAINING",
                            {"workout_summary_id": self.state["workout_summary_id"]},
                        )
                    )
                    print("đã gửi workout summary id")
                else:
                    print("nhay vao else")
                    if response["content"] != "Unknow":

                        content = response["content"]
                        print(f"Đã nhận nội dung: {content}")
                        rep_index = response["rep_index"]
                        print(f"Đã nhận rep_index: {rep_index}")
                        user_id = response["user_id"]
                        print(f"Đã nhận user_id: {user_id}")
                        time = response["time"]
                        print(f"Đã nhận time: {time}")
                        image_id = int( response["image_id"])
                        print(f"Đã nhận image_id: {image_id}")
                        session_id = (
                            response["session_id"]
                            if response["session_id"] is not None
                            else "123456789"
                        )
                        print(f"Đã nhận session_id: {session_id}")

                        self.dataChannel.send(
                            dataChannel_response(
                                "AI_RESPONSE",
                                {
                                    "content": content,
                                    "rep_index": rep_index,
                                    "user_id": user_id,
                                    "time": time,
                                },
                            ),
                        )
                        print("Đã gửi đến dataChannel")
                    else:
                        print("Nội dung không hợp lệ, không gửi đến dataChannel")

                    if self.buffer.frame_buffer:
                        asyncio.create_task(
                            self.handle_error_frame(
                                image_id, rep_index, session_id, content
                            )
                        )

                    # if self.config:
                    #     await self.audio_queue.put(content)

            except Exception as e:
                print(f"⚠️ Lỗi trong speaker_output: {e}")
                await asyncio.sleep(1)
