import mediapipe as mp
import cv2
import os
import numpy as np

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

class KeypointExtractor:
    def __init__(self):
        mp_pose = mp.solutions.pose
        self.pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            smooth_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )

        # ! LẤY CÁC KEYPOINTS QUAN TRỌNG
        self.keypoints_ids = {
            "nose": 0,
            "left_shoulder": 11,
            "right_shoulder": 12,
            "left_hip": 23,
            "right_hip": 24,
            "left_knee": 25,
            "right_knee": 26,
            "left_ankle": 27,
            "right_ankle": 28,
        }

        # ! CÁC KEYPOINTS KIỂM TRA CHUYỂN ĐỘNG
        self.keypoints_to_check = [
            "left_hip",
            "right_hip",
            "left_knee",
            "right_knee",
        ]

        self.previous_keypoints = None
        self.last_process_time = 0
        self.processing_interval = 0.1  # Xử lý tối đa 10fps cho keypoints

        # Cache frame đã xử lý để tái sử dụng
        self.frame_cache = None
        self.frame_cache_hash = None

    def frame_hash(self, frame):
        """Tạo hash đơn giản cho frame để kiểm tra trùng lặp"""
        if frame is None:
            return None
        return hash(frame[::20,::20,:].tobytes())

    def getKeyPoint(self, image):
        # Kiểm tra cache
        current_hash = self.frame_hash(image)
        if current_hash == self.frame_cache_hash and self.frame_cache is not None:
            return self.frame_cache

        # Resize để xử lý nhanh hơn
        h, w = image.shape[:2]
        if h > 480:
            scale = 480 / h
            image = cv2.resize(image, (int(w * scale), 480))

        # Chuyển từ màu BGR của OpenCV sang RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Chạy mô hình pose
        results = self.pose.process(image_rgb)

        # Cập nhật cache
        self.frame_cache = results.pose_landmarks if results.pose_landmarks else None
        self.frame_cache_hash = current_hash

        return self.frame_cache

    def getImportantKeypoints(self, pose_landmarks, threshold=0.035):
        if pose_landmarks is None:
            return None

        importantKeypoints = {}

        # Chỉ lấy các keypoint quan trọng
        for key, idx in self.keypoints_ids.items():
            landmark = pose_landmarks.landmark[idx]

            if landmark.visibility < 0.6:
                continue

            importantKeypoints[key] = {
                "x": landmark.x,
                "y": landmark.y,
                "z": landmark.z,
                "visibility": landmark.visibility,
            }

        # Kiểm tra xem đã có đủ keypoint chưa
        required_keys = set(self.keypoints_to_check)
        if not required_keys.issubset(set(importantKeypoints.keys())):
            return None

        # Nếu đã có keypoint cũ, kiểm tra sự khác biệt
        if self.previous_keypoints is not None:
            changed = False
            for key in self.keypoints_to_check:
                if key not in self.previous_keypoints or key not in importantKeypoints:
                    changed = True
                    break

                old_y = self.previous_keypoints[key]["y"]
                new_y = importantKeypoints[key]["y"]

                value_change = abs(new_y - old_y)
                if value_change > threshold:
                    changed = True
                    break

            if not changed:
                return None

        # Cập nhật lại keypoint trước đó
        self.previous_keypoints = importantKeypoints.copy()

        return importantKeypoints