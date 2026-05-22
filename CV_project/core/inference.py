# core/inference.py
"""
원본 main_inference.py의 로직을 그대로 유지하되,
Streamlit용 함수형 인터페이스 + 디버그 통계 추가
"""
import os
import json
import cv2
import numpy as np
import onnxruntime as ort
from ultralytics import YOLO
import streamlit as st

from core.matching import softmax, compute_match


# ---------- 모델 로딩 (캐시) ----------
@st.cache_resource(show_spinner=False)
def load_encoders(path: str = "label_encoders.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource(show_spinner=False)
def load_yolo(path: str = "models/yolov8n.onnx"):
    return YOLO(path)


@st.cache_resource(show_spinner=False)
def load_resnet(path: str = "models/resnet50_multihead.onnx"):
    sess = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
    input_name = sess.get_inputs()[0].name
    return sess, input_name


# ---------- 전처리 ----------
def preprocess_roi(roi_img: np.ndarray) -> np.ndarray:
    img = cv2.cvtColor(roi_img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224)).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img = (img - mean) / std
    img = np.transpose(img, (2, 0, 1))
    return np.expand_dims(img, axis=0)


def search_video_for_target(
    video_path: str,
    target: dict,
    encoders: dict,
    yolo_model,
    resnet_sess,
    input_name: str,
    quality_threshold: float = 8000, 
    frame_skip: int = 1,                
    progress_callback=None,
):
    """원본 main_inference.py 로직 충실 재현 + 매칭 + 디버그"""
    id_to = {
        field: {v: k for k, v in encoders[field].items()}
        for field in ["brand", "color", "model", "year"]
    }

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {
            "match": None, "frame": None, "timestamp_sec": 0,
            "predicted": None, "track_id": None,
            "all_classified": [],
            "debug": {"error": f"영상을 열 수 없음: {video_path}"},
        }

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    track_registry = {}

    stats = {
        "total_frames": total_frames,
        "fps": fps,
        "frames_processed": 0,
        "frames_with_detection": 0,
        "total_detections": 0,
        "tracks_seen_set": set(),
        "tracks_classified": 0,
        "max_score_seen": 0,
        "quality_threshold": quality_threshold,
    }

    frame_idx = 0
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_idx += 1
        if progress_callback and frame_idx % 10 == 0:
            progress_callback(min(frame_idx / max(total_frames, 1), 1.0))

        if frame_skip > 1 and frame_idx % frame_skip != 0:
            continue

        stats["frames_processed"] += 1

        # YOLOv8 + ByteTrack
        results = yolo_model.track(
            frame, persist=True, tracker="bytetrack.yaml",
            classes=[2, 3, 5, 7], verbose=False
        )

        if results[0].boxes is None or results[0].boxes.id is None:
            continue

        stats["frames_with_detection"] += 1

        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.int().cpu().tolist()
        confidences = results[0].boxes.conf.cpu().numpy()
        stats["total_detections"] += len(boxes)

        for box, track_id, conf in zip(boxes, track_ids, confidences):
            x1, y1, x2, y2 = map(int, box)
            x1, y1 = max(0, x1), max(0, y1)
            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)
            w, h = x2 - x1, y2 - y1
            if w < 50 or h < 50:
                continue

            current_score = (w * h) * float(conf)
            stats["max_score_seen"] = max(stats["max_score_seen"], current_score)
            stats["tracks_seen_set"].add(track_id)

            if track_id not in track_registry:
                track_registry[track_id] = {
                    "best_score": 0,
                    "is_classified": False,
                }

            if not track_registry[track_id]["is_classified"]:
                if current_score > track_registry[track_id]["best_score"]:
                    track_registry[track_id]["best_score"] = current_score

                    if current_score > quality_threshold:
                        roi = frame[y1:y2, x1:x2]
                        input_tensor = preprocess_roi(roi)
                        outputs = resnet_sess.run(None, {input_name: input_tensor})

                        probs = {
                            "brand": softmax(outputs[0][0]),
                            "color": softmax(outputs[1][0]),
                            "model": softmax(outputs[2][0]),
                            "year":  softmax(outputs[3][0]),
                        }
                        pred = {
                            "brand": id_to["brand"].get(int(np.argmax(outputs[0]))),
                            "color": id_to["color"].get(int(np.argmax(outputs[1]))),
                            "model": id_to["model"].get(int(np.argmax(outputs[2]))),
                            "year":  id_to["year"].get(int(np.argmax(outputs[3]))),
                        }

                        # 박스 그린 프레임
                        vis_frame = frame.copy()
                        cv2.rectangle(vis_frame, (x1, y1), (x2, y2), (0, 255, 100), 3)

                        match = compute_match(probs, target, encoders)

                        track_registry[track_id].update({
                            "is_classified": True,
                            "probs": probs,
                            "pred": pred,
                            "match": match,
                            "frame": vis_frame,
                            "box": (x1, y1, x2, y2),
                            "timestamp_sec": frame_idx / fps,
                        })
                        stats["tracks_classified"] += 1

    cap.release()
    if progress_callback:
        progress_callback(1.0)

    stats["tracks_seen"] = len(stats["tracks_seen_set"])
    del stats["tracks_seen_set"]

    # 분류된 모든 트랙 모으기
    all_classified = []
    for tid, info in track_registry.items():
        if info.get("is_classified"):
            all_classified.append({
                "track_id": tid,
                "pred": info["pred"],
                "match": info["match"],
                "frame": info["frame"],
                "timestamp_sec": info["timestamp_sec"],
            })

    # 베스트 매치
    if not all_classified:
        return {
            "match": None, "frame": None, "timestamp_sec": 0,
            "predicted": None, "track_id": None,
            "all_classified": [],
            "debug": stats,
        }

    best = max(all_classified, key=lambda x: x["match"]["overall"])
    return {
        "match": best["match"],
        "frame": best["frame"],
        "timestamp_sec": best["timestamp_sec"],
        "predicted": best["pred"],
        "track_id": best["track_id"],
        "all_classified": all_classified,
        "debug": stats,
    }