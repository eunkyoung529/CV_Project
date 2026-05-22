# pages/1_차량정보입력.py
import streamlit as st
import json

from core.state import init_session_state, reset_search

init_session_state()

st.title("1️⃣ 범인 차량 정보 입력")
st.caption("목격된 차량의 정보를 입력하세요. 이후 단계에서 CCTV 영상 분석에 사용됩니다.")

# 인코더 로드해서 선택지 만들기
with open("label_encoders.json", "r", encoding="utf-8") as f:
    encoders = json.load(f)

# 차종은 model 라벨에서 prefix만 뽑아서 그룹으로 (세단/SUV/...)
model_types = sorted({
    k.split("_")[0] for k in encoders["model"].keys() if "_" in k
})

brands = [b for b in encoders["brand"].keys() if b != "unknown"]
colors = [c for c in encoders["color"].keys() if c != "unknown"]
years = [y for y in encoders["year"].keys() if y != "unknown" and "-" in y][:20]
# 세부 모델명도 같이
all_models = [m for m in encoders["model"].keys() if m != "unknown"]

# 입력 방식 토글
mode = st.radio(
    "입력 방식",
    ["토글로 선택", "텍스트로 입력"],
    horizontal=True,
)

with st.container(border=True):
    if mode == "토글로 선택":
        c1, c2 = st.columns(2)
        with c1:
            model_type = st.selectbox(
                "차종", model_types,
                index=model_types.index("세단") if "세단" in model_types else 0,
            )
            color = st.selectbox(
                "색상", colors,
                index=colors.index("검은색") if "검은색" in colors else 0,
            )
        with c2:
            brand = st.selectbox(
                "제조사", brands,
                index=brands.index("현대자동차") if "현대자동차" in brands else 0,
            )
            year = st.selectbox(
                "연식", years,
                index=years.index("2020-") if "2020-" in years else 0,
            )

        # 차종 + 제조사로 가능한 세부 모델 자동 필터링
        candidates = [m for m in all_models if m.startswith(model_type + "_")]

        if not candidates:
            st.warning(f"⚠️ '{model_type}' 차종에 매칭되는 세부 모델이 없습니다.")
            model_label = "unknown"
        else:
            detail_model = st.selectbox(
                "세부 모델 (필수 — 자동탐색 정확도에 직접 영향)",
                candidates,  # "(자동)" 옵션 제거: 무조건 실제 라벨 중에서 고름
            )
            model_label = detail_model

    else:  # 텍스트 입력
        c1, c2 = st.columns(2)
        with c1:
            model_type = st.text_input("차종", value="세단")
            color = st.text_input("색상", value="검은색")
        with c2:
            brand = st.text_input("제조사", value="현대자동차")
            year = st.text_input("연식", value="2020-")
        model_label = st.text_input("세부 모델 (예: 세단_쏘나타)", value="세단_쏘나타")

        # 입력값이 실제 라벨에 있는지 안내
        if model_label not in encoders["model"]:
            st.info(
                f"💡 '{model_label}'은(는) 라벨 목록에 없습니다. "
                f"가까운 라벨로 자동 매칭됩니다. "
                f"정확한 매칭을 원하면 '토글로 선택' 모드를 사용하세요."
            )

    location = st.text_input(
        "사고 위치",
        value="경기도 부천시 원미구 길주로 210",
    )

st.markdown(" ")
register = st.button("✅ 등록", type="primary", use_container_width=True)

if register:
    st.session_state.vehicle_info = {
        "model_type": model_type,
        "color": color,
        "brand": brand,
        "year": year,
        "model": model_label,   
        "location": location,
    }
    reset_search()  # 입력이 바뀌면 이전 결과는 무효화
    st.success("등록 완료! 사이드바에서 **2️⃣ CCTV선택** 단계로 진행하세요.")
    st.json(st.session_state.vehicle_info)

if st.session_state.vehicle_info:
    st.markdown("---")
    st.caption("현재 등록된 정보:")
    st.json(st.session_state.vehicle_info)