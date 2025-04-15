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


def getImportantKeypoints(pose_landmarks, threshold=0.052):
    global previous_keypoints

    if pose_landmarks is None:
        return None

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

    importantKeypoints = {}

    for key, idx in keypoints_ids.items():
        landmark = pose_landmarks.landmark[idx]

        if key not in ["left_ankle", "right_ankle"] and landmark.visibility < 0.7:
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
        for key in importantKeypoints:
            for coord in ["x", "y", "z"]:
                old_val = previous_keypoints[key][coord]
                new_val = importantKeypoints[key][coord]
                if abs(new_val - old_val) > threshold:
                    changed = True
                    break
            if changed:
                break

        if not changed:
            print("khong co thay doi, bo qua")
            return None

    # Cập nhật lại keypoint trước đó
    previous_keypoints = importantKeypoints
    return importantKeypoints


# # Hàm lấy các điểm quan trọng
# def getImportantKeypoints(pose_landmarks):
#     if pose_landmarks is None:
#         return None

#     keypoints_ids = {
#         "nose": 0,
#         "left_shoulder": 11,
#         "right_shoulder": 12,
#         "left_hip": 23,
#         "right_hip": 24,
#         "left_knee": 25,
#         "right_knee": 26,
#         "left_ankle": 27,
#         "right_ankle": 28,
#     }

#     importantKeypoints = {}

#     for key, idx in keypoints_ids.items():

#         landmark = pose_landmarks.landmark[idx]

#         if key not in ["left_ankle", "right_ankle"] and landmark.visibility < 0.7:
#             print(f"⚠️ {key} có visibility thấp, bỏ qua.")
#             return None

#         importantKeypoints[key] = {
#             "x": landmark.x,
#             "y": landmark.y,
#             "z": landmark.z,
#             "visibility": landmark.visibility,
#         }

#     return importantKeypoints
