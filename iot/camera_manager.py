import cv2
import asyncio
import threading
from aiortc import VideoStreamTrack
from aiortc.mediastreams import VideoFrame

from iot.get_keypoints import getImportantKeypoints, getKeyPoint

video_path_1 = "/home/nhattuan/Desktop/Raspberry/data/Thanh_demo.mp4"
video_path_2 = "/home/nhattuan/Desktop/Raspberry/data/Tuan_demo.mp4"
sleep_time = 1 / 18

class CameraManager(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.cap = None
        self.latest_frame = None  # Chỉ giữ frame mới nhất
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self.connections = 0

    def start_camera(self):
        if not self.running:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.running = True
            self.thread = threading.Thread(target=self._capture_frames)
            self.thread.start()
            print("Camera started")

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

    def _capture_frames(self):
        while self.running:
            ret, img = self.cap.read()
            if not ret:
                print("camera không mở")
                break
            with self.lock:
                self.latest_frame = img  # Chỉ lưu frame mới nhất

    def get_latest_frame(self):
        with self.lock:
            return self.latest_frame
        
        
    def unsharp_mask(self, image):
        blurred = cv2.GaussianBlur(image, (5, 5), 1.0)
        sharpened = cv2.addWeighted(image, 2.0, blurred, -1.0, 0)
        return sharpened

    # hàm gửi frame cho app mobile
    async def recv(self):
        try:
            pts, time_base = await self.next_timestamp()
            img = self.get_latest_frame()
            if img is None:
                print("⚠️ Không có frame nào để gửi qua WebRTC!")
                return None
            
            img_sharpened = self.unsharp_mask(img)
            
            img2 = cv2.cvtColor(img_sharpened , cv2.COLOR_BGR2RGB)
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

    # hàm gửi keypoints
    async def _send_keypoints(self, backend_server):
        if backend_server is None:
            print("Không thể gửi keypoints vì không có kết nối đến backend server.")
            return
        while self.running:
            try:
                img = self.get_latest_frame()
                if img is None:
                    continue  # Nếu không có frame mới thì bỏ qua
                loop = asyncio.get_running_loop()
                lastest_landmarks = await loop.run_in_executor(None, getKeyPoint, img)
                important_keypoints = await loop.run_in_executor(
                    None, getImportantKeypoints, lastest_landmarks
                )
                if important_keypoints is not None: 
                    pass
                    # await backend_server.send(
                    #     json.dumps(
                    #         {
                    #             "user_id": "111",
                    #             "key_points": important_keypoints,
                    #         }
                    #     )
                    # )
                await asyncio.sleep(sleep_time)
            except Exception as e:
                print(f"⚠️ Lỗi trong _send_keypoints: {e}")
                await asyncio.sleep(sleep_time)

