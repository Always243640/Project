import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np

from state import GestureResult

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands_detector = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)


@dataclass
class HandCrop:
    handedness: str
    surface: Optional[np.ndarray]


def count_fingers(hand_landmarks, handedness: str) -> int:
    tips = [4, 8, 12, 16, 20]
    fingers = []
    if handedness == "Right":
        fingers.append(hand_landmarks.landmark[tips[0]].x < hand_landmarks.landmark[tips[0] - 1].x)
    else:
        fingers.append(hand_landmarks.landmark[tips[0]].x > hand_landmarks.landmark[tips[0] - 1].x)
    for idx in range(1, 5):
        fingers.append(hand_landmarks.landmark[tips[idx]].y < hand_landmarks.landmark[tips[idx] - 2].y)
    return sum(fingers)


def detect_ok(hand_landmarks) -> bool:
    thumb_tip = hand_landmarks.landmark[4]
    index_tip = hand_landmarks.landmark[8]
    dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
    return dist < 0.05


def _hand_bbox(hand_landmarks, frame_shape) -> Tuple[int, int, int, int]:
    h, w, _ = frame_shape
    xs = [int(pt.x * w) for pt in hand_landmarks.landmark]
    ys = [int(pt.y * h) for pt in hand_landmarks.landmark]
    x_min, x_max = max(min(xs) - 20, 0), min(max(xs) + 20, w)
    y_min, y_max = max(min(ys) - 20, 0), min(max(ys) + 20, h)
    return x_min, y_min, x_max, y_max


def detect_gestures(frame) -> Tuple[List[GestureResult], np.ndarray, Dict[str, np.ndarray]]:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands_detector.process(rgb)
    gestures: List[GestureResult] = []
    crops: Dict[str, np.ndarray] = {}
    annotated = frame.copy()
    if result.multi_hand_landmarks and result.multi_handedness:
        for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
            label = handedness.classification[0].label
            gesture_num = count_fingers(hand_landmarks, label)
            gestures.append(
                GestureResult(
                    gesture=gesture_num if 1 <= gesture_num <= 5 else None,
                    is_ok=detect_ok(hand_landmarks),
                    handedness=label,
                )
            )
            mp_drawing.draw_landmarks(annotated, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            x_min, y_min, x_max, y_max = _hand_bbox(hand_landmarks, frame.shape)
            crops[label] = frame[y_min:y_max, x_min:x_max].copy()
    return gestures, annotated, crops
