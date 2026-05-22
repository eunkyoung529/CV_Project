# pages/3_탐색시작.py
import streamlit as st
import time

from core.state import init_session_state
from core.inference import (
    load_encoders, load_yolo, load_resnet, search_video_for_target,
)

init_session_state()

st.title("3️⃣ 차량 탐색 시작")

# 사전 조건 체크
if not st.session_state.vehicle_info:
    st.warning("먼저 **1️⃣ 차량정보입력**을 완료하세요.")
    st.stop()
if not st.session_state.selected_cctvs:
    st.warning("먼저 **2️⃣ CCTV선택**을 완료하세요.")
    st.stop()

# 입력 정보 확인 영역
v = st.session_state.vehicle_info
cctvs = st.session_state.selected_cctvs
cctv_label = ", ".join(f"#{c['id']}" for c in cctvs)

with st.container(border=True):
    st.markdown("### [입력 정보 확인 후 탐색 시작]")
    st.markdown(
        f"**CCTV [{cctv_label}] 내에서 해당 차량을 검색합니다.**"
    )
    st.markdown(
        f"**후보:** `{v['model_type']}`  ·  `{v['color']}`  ·  `{v['brand']}`  ·  `{v['year']}`"
    )

st.markdown(" ")

# 선택된 CCTV 수만 표시
c1, c2, c3 = st.columns(3)
c1.metric("선택된 CCTV 수", f"{len(cctvs)}개")
c2.metric("입력 차종", v["model_type"])
c3.metric("입력 색상", v["color"])

st.markdown(" ")
start = st.button("🔍 차량 탐색하기 시작", type="primary", use_container_width=True)

if start:
    # 로딩 UI
    with st.spinner("🤖 모델을 로드하는 중입니다..."):
        encoders = load_encoders()
        yolo = load_yolo()
        resnet_sess, input_name = load_resnet()

    # target 구성
    target = {
        "brand": v["brand"],
        "color": v["color"],
        "model": v.get("model", "unknown"),
        "year":  v["year"],
    }

    overall_bar = st.progress(0.0, text="전체 진행률")
    status = st.empty()
    results = []

    for i, cctv in enumerate(cctvs):
        status.info(f"🔍 [{i+1}/{len(cctvs)}] CCTV #{cctv['id']} — {cctv['name']} 분석 중...")
        per_bar = st.progress(0.0, text=f"CCTV #{cctv['id']} 진행률")

        def cb(p, _bar=per_bar):
            _bar.progress(p, text=f"CCTV #{cctv['id']} 진행률 ({int(p*100)}%)")

        try:
            res = search_video_for_target(
                video_path=cctv["video"],
                target=target,
                encoders=encoders,
                yolo_model=yolo,
                resnet_sess=resnet_sess,
                input_name=input_name,
                progress_callback=cb,
            )
        except Exception as e:
            st.error(f"CCTV #{cctv['id']} 처리 중 오류: {e}")
            res = None

        per_bar.empty()
        results.append({"cctv": cctv, "result": res})
        overall_bar.progress((i + 1) / len(cctvs), text=f"전체 진행률 ({i+1}/{len(cctvs)})")

    status.empty()
    overall_bar.empty()

    st.session_state.results = results
    st.session_state.search_done = True

    st.success("✅ 탐색이 완료되었습니다! 사이드바에서 **4️⃣ 결과출력** 페이지로 이동하세요.")
    st.balloons()

elif st.session_state.search_done:
    st.info("이미 탐색이 완료되었습니다. **4️⃣ 결과출력** 페이지에서 확인하세요.")