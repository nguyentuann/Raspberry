import json
import cv2
import asyncio

import threading
from aiortc import VideoStreamTrack
from aiortc.mediastreams import VideoFrame

from helper.buffer import Buffer
from iot.get_keypoints import KeypointExtractor

video_path_1 = "/home/nhattuan/Desktop/Raspberry/data/Thanh_demo.mp4"
video_path_2 = "/home/nhattuan/Desktop/Raspberry/data/Tuan_demo.mp4"
sleep_time = 1 / 18


class CameraManager(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.cap = None
        self.latest_frame = None
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self.connections = 0
        self.frame_interval = 1 / 18
        self.frame_scale = 0.5
        self.keypoint_extractor = KeypointExtractor()

    # ! BẮT ĐẦU CAMERA
    def start_camera(self):
        if not self.running:
            self.cap = cv2.VideoCapture(video_path_1)
            if not self.cap.isOpened():
                pass
                # print("❌ Không mở được camera!")
                # self.cap = None
                # return
            self.running = True
            self.thread = threading.Thread(target=self._capture_frames)
            self.thread.start()
            print("Camera started")

    # ! KẾT THÚC CAMERA
    def stop_camera(self):
        self.connections -= 1
        print(f"Số kết nối còn lại: {self.connections}")
        if self.connections <= 0:
            self.running = False
            print("dừng camera")
            if self.cap:
                self.cap.release()
                self.cap = None
            print("Camera stopped")

    # ! ĐƯA VỀ TỈ LỆ 16:9
    def _make_16_9(self, frame):
        h, w = frame.shape[:2]
        target_ratio = 16 / 9
        current_ratio = w / h

        if current_ratio == target_ratio:
            return frame  # Đã đúng tỉ lệ

        elif current_ratio > target_ratio:
            # Cắt chiều rộng
            new_w = int(h * target_ratio)
            offset = (w - new_w) // 2
            return frame[:, offset : offset + new_w]
        else:
            # Thêm viền đen hai bên
            new_w = int(h * target_ratio)
            pad = (new_w - w) // 2
            return cv2.copyMakeBorder(
                frame, 0, 0, pad, new_w - w - pad, cv2.BORDER_CONSTANT, value=(0, 0, 0)
            )

    # ! LẤY FRAME TỪ CAMERA
    def _capture_frames(self):
        while self.running:
            ret, img = self.cap.read()
            if not ret:
                print("🔁 Video kết thúc, phát lại từ đầu.")
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            if self.frame_scale != 1.0:
                img = cv2.resize(img, (0, 0), fx=self.frame_scale, fy=self.frame_scale)

            # Đưa về tỷ lệ 16:9
            img = self._make_16_9(img)

            with self.lock:
                self.latest_frame = img.copy()

    # ! LẤY FRAME MỚI NHẤT
    def get_latest_frame(self):
        with self.lock:
            return self.latest_frame

    # ! GỬI FRAME CHO MOBILE
    async def recv(self):
        try:
            pts, time_base = await self.next_timestamp()
            # print(f"pts: {pts}, time_base: {time_base}")
            img = self.get_latest_frame()
            if img is None:
                print("⚠️ Không có frame nào để gửi qua WebRTC!")
                return None

            img2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            video_frame = VideoFrame.from_ndarray(img2, format="rgb24")
            video_frame.pts = pts
            video_frame.time_base = time_base

            if video_frame is None:
                print("⚠️ Không có frame nào để gửi qua WebRTC!")
                return None
            return video_frame
        except Exception as e:
            print(f"⚠️ Lỗi trong recv: {e}")
            return None

    # ! GỬI KEYPOINTS
    async def _send_keypoints(self, backend_server, user_id, state, buffer: Buffer):
        if backend_server is None:
            print("Không thể gửi keypoints vì không có kết nối đến backend server.")
            return

        session_id = state["session_id"]
        print(f"session_id: {session_id}")

        while self.running:
            try:
                img = self.get_latest_frame()
                if img is None:
                    continue  # Nếu không có frame mới thì bỏ qua
                loop = asyncio.get_running_loop()
                lastest_landmarks = await loop.run_in_executor(
                    None, self.keypoint_extractor.getKeyPoint, img
                )
                important_keypoints = await loop.run_in_executor(
                    None,
                    self.keypoint_extractor.getImportantKeypoints,
                    lastest_landmarks,
                )

                if important_keypoints is not None:
                    # lưu frame vào buffer
                    buffer.frame_buffer.append(img)
                    print("co thay doi, da gui keypoints")
                    await backend_server.send(
                        json.dumps(
                            {
                                "key_points": important_keypoints,
                                "user_id": user_id,
                                "session_id": session_id,
                            }
                        )
                    )
            except Exception as e:
                print(f"⚠️ Lỗi trong _send_keypoints: {e}")
                await asyncio.sleep(sleep_time)
