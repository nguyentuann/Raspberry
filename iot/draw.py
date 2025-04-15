'''
  DRAWLANDMARKS
'''
import mediapipe as mp
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
drawing_spec = mp_drawing.DrawingSpec(color=(255, 0, 255), thickness=3, circle_radius=2)


def draw_landmarks(image, landmarks):
  mp_drawing.draw_landmarks(
    image,
    landmarks,
    mp_pose.POSE_CONNECTIONS,
    landmark_drawing_spec=drawing_spec,
    connection_drawing_spec=drawing_spec
  )
  return image
