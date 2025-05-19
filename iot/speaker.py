import asyncio
import io
import pygame
import gtts
import json
from aiortc import RTCDataChannel



# phát thông báo ra loa
async def speaker_output(
    dataChannel: RTCDataChannel,
    backend_server_future: asyncio.Future,
):
    pygame.mixer.init()
    backend_server = await backend_server_future

    while True:
        try:
            response = await backend_server.recv()
            if response is None:
                print("❌ Không có phản hồi từ backend server.")
                await asyncio.sleep(1)
                continue
            # Đợi tin nhắn từ AI server
            # response = json.loads(response)

            print(f"📥 Nhận phản hồi từ backend: {response}")

            # if response["content"] != "Unknow":
            #     print(dataChannel.readyState)
            #     dataChannel.send(json.dumps(response))
            #     print("da gui den dataChannel")

            #     # # Phát ra loa
            #     tts = gtts.gTTS(response["content"], lang="vi")

            #     # Lưu vào file tạm vì pygame không hỗ trợ phát từ BytesIO
            #     audio = io.BytesIO()
            #     tts.write_to_fp(audio)
            #     audio.seek(0)

            #     # Khởi tạo pygame để phát âm thanh
            #     pygame.mixer.init()
            #     pygame.mixer.music.load(audio, "mp3")
            #     pygame.mixer.music.play()

            #     # Đợi phát xong
            #     while pygame.mixer.music.get_busy():
            #         await asyncio.sleep(0.1)

        except Exception as e:
            print(f"⚠️ Lỗi trong speaker_output: {e}")
            return
