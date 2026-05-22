# core/matching.py
"""
모델 예측값 vs 사용자 입력 차량정보 → 요소별 일치율과 전체 일치율 계산.
모델 출력은 softmax 확률값을 그대로 사용. 사용자가 입력한 클래스에 대한 모델의 확률이
'그 요소의 일치율'이 된다.
"""
import numpy as np


def softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - np.max(x))
    return e / e.sum()


def _resolve_label(user_value, label_dict: dict):
    """
    사용자 입력값을 encoders의 실제 키로 매핑.
    1) 완전 일치 우선
    2) 부분 일치(substring) 차선
    3) 그래도 없으면 None
    """
    if user_value is None:
        return None
    if user_value in label_dict:
        return user_value
    # 부분 일치 시도
    for key in label_dict.keys():
        if key == "unknown":
            continue
        if user_value in key or key in user_value:
            return key
    return None


def compute_match(probs_dict: dict, target_dict: dict, encoders: dict) -> dict:
    """
    Args:
        probs_dict: {"brand": np.array, "color": ..., "model": ..., "year": ...}
                    각각 (num_classes,) 형태의 softmax 확률
        target_dict: 사용자가 입력한 정답 라벨 {"brand":"현대자동차", ...}
        encoders: label_encoders.json 내용
    Returns:
        {
          "per_field": {"brand": 0.65, "color": 0.99, "model": 0.87, "year": 0.73},
          "overall":   0.81,
          "grade":     "A (확실함)",
          "resolved":  {"brand":"현대자동차", ...}  # 실제 매칭된 라벨
        }
    """
    per_field = {}
    resolved = {}

    for field in ["brand", "color", "model", "year"]:
        user_val = target_dict.get(field)
        actual_label = _resolve_label(user_val, encoders[field])
        resolved[field] = actual_label

        if actual_label is None:
            per_field[field] = 0.0
            continue

        target_idx = encoders[field][actual_label]
        probs = probs_dict[field]
        per_field[field] = float(probs[target_idx])

    # 전체 일치율: 가중평균 (색상·차종 가중치를 약간 높임)
    weights = {"brand": 0.2, "color": 0.3, "model": 0.3, "year": 0.2}
    overall = sum(per_field[k] * weights[k] for k in per_field)

    # 등급 산정
    if overall >= 0.85:
        grade = "A (확실함)"
    elif overall >= 0.70:
        grade = "B (높음)"
    elif overall >= 0.55:
        grade = "C (보통)"
    else:
        grade = "D (낮음)"

    return {
        "per_field": per_field,
        "overall": overall,
        "grade": grade,
        "resolved": resolved,
    }