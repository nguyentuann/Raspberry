import mediapipe as mp
import cv2
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Model Pose Estimation của MediaPipe, giúp phát hiện tư thế con người.
mp_pose = mp.solutions.pose

# Khởi tạo mediapipe pose
pose = mp_pose.Pose(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
)


# keypoints quan trọng
keypoints_ids = {
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

# keypoints kiểm tra chuyển động
keypoints_to_check = [
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
]


# Hàm trả về keypoint
def getKeyPoint(image):
    # Chuyển từ màu BGR của OpenCV sang RGB
    image = cv2.cvtColor(src=image, code=cv2.COLOR_BGR2RGB)

    # Chạy mô hình pose
    results = pose.process(image)

    if results.pose_landmarks:
        return results.pose_landmarks
    else:
        return None


# Biến toàn cục để lưu keypoint trước đó
previous_keypoints = None


# hàm lấy các keypoint quan trọng
def getImportantKeypoints(pose_landmarks, threshold=0.028):
    global previous_keypoints
    importantKeypoints = {}

    if pose_landmarks is None:
        return None

    for key, idx in keypoints_ids.items():
        landmark = pose_landmarks.landmark[idx]

        if landmark.visibility < 0.7:
            return None

        importantKeypoints[key] = {
            "x": landmark.x,
            "y": landmark.y,
            "z": landmark.z,
            "visibility": landmark.visibility,
        }

    # Nếu đã có keypoint cũ, kiểm tra sự khác biệt
    if previous_keypoints is not None:
        changed = False
        for key in keypoints_to_check:
            old_y = previous_keypoints[key]["y"]
            new_y = importantKeypoints[key]["y"]

            value_change = abs(new_y - old_y)
            # print(f"thay doi y cua {key}:  {value_change}")
            if value_change > threshold:
                changed = True
                break

        if not changed:
            # print("khong co thay doi, bo qua")
            return None

    # Cập nhật lại keypoint trước đó
    previous_keypoints = importantKeypoints

    print("co thay doi, da gui keypoint")

    return importantKeypoints
