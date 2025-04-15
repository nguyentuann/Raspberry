import asyncio
import json
import websockets
import mediapipe as mp
import cv2 as cv



mp_pose = mp.solutions.pose

# khởi tạo mediapipe pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)


#  hàm trả về keypoint
def getKeyPoint(image):
    # cvt từ màu BGR của openCV sang RGB
    image = cv.cvtColor(src=image, code=cv.COLOR_BGR2RGB)

    # chạy mô hình pose
    results = pose.process(image)

    if results.pose_landmarks:

        return results.pose_landmarks
    else:
        return None


def getImportantKeypoints(pose_landmarks):
    if pose_landmarks is None:
        return None

    importantKeypoints = {
        "nose": {
            "x": pose_landmarks.landmark[0].x,
            "y": pose_landmarks.landmark[0].y,
            "z": pose_landmarks.landmark[0].z,
        },
        "left_shoulder": {
            "x": pose_landmarks.landmark[11].x,
            "y": pose_landmarks.landmark[11].y,
            "z": pose_landmarks.landmark[11].z,
        },
        "right_shoulder": {
            "x": pose_landmarks.landmark[12].x,
            "y": pose_landmarks.landmark[12].y,
            "z": pose_landmarks.landmark[12].z,
        },
        "left_hip": {
            "x": pose_landmarks.landmark[23].x,
            "y": pose_landmarks.landmark[23].y,
            "z": pose_landmarks.landmark[23].z,
        },
        "right_hip": {
            "x": pose_landmarks.landmark[24].x,
            "y": pose_landmarks.landmark[24].y,
            "z": pose_landmarks.landmark[24].z,
        },
        "left_knee": {
            "x": pose_landmarks.landmark[25].x,
            "y": pose_landmarks.landmark[25].y,
            "z": pose_landmarks.landmark[25].z,
        },
        "right_knee": {
            "x": pose_landmarks.landmark[26].x,
            "y": pose_landmarks.landmark[26].y,
            "z": pose_landmarks.landmark[26].z,
        },
        "left_ankle": {
            "x": pose_landmarks.landmark[27].x,
            "y": pose_landmarks.landmark[27].y,
            "z": pose_landmarks.landmark[27].z,
        },
        "right_ankle": {
            "x": pose_landmarks.landmark[28].x,
            "y": pose_landmarks.landmark[28].y,
            "z": pose_landmarks.landmark[28].z,
        },
    }
    return importantKeypoints



            
async def send_keypoints():
    uri = f"ws://192.168.1.5:8000/ws"
    async with websockets.connect(uri) as websocket:
        cap = cv.VideoCapture(0)
       
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            keypoints = getImportantKeypoints(getKeyPoint(frame))
            await websocket.send(json.dumps({"keypoints": keypoints}))  
            print(f"Gửi keypoints: {keypoints}")
            
            response = await websocket.recv()  
            print("Phản hồi từ server:", response)
            
            await asyncio.sleep(1/30)  

# Khởi chạy client
asyncio.run(send_keypoints())

