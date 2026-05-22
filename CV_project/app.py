# app.py
import streamlit as st

st.set_page_config(
    page_title="뺑소니 차량 검거 시스템",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS 로드
try:
    with open("assets/style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# 세션 상태 초기화
from core.state import init_session_state
init_session_state()

# 메인 페이지
st.title("🚨 뺑소니 차량 검거 시스템")
st.markdown("---")

st.markdown(
    """
    ### 프로젝트 소개
    이 시스템은 뺑소니 사고가 발생했을 때, **목격된 차량 정보**와 **주변 CCTV 영상**을 활용해
    용의 차량을 자동으로 추적·식별하는 데모입니다.

    #### 사용 흐름
    1. **차량 정보 입력** — 차종 / 색상 / 제조사 / 연식 입력
    2. **CCTV 선택** — 지도에서 분석할 CCTV 최대 4개 선택
    3. **탐색 시작** — AI 모델이 각 영상에서 후보 차량 검색
    4. **결과 확인** — 임계값 이상 일치 장면을 후보로 출력

    👉 왼쪽 사이드바에서 **1️⃣ 차량정보입력** 페이지부터 시작하세요.
    """
)

# 진행 상황 표시
st.markdown("---")
st.subheader("📋 현재 진행 상황")

col1, col2, col3, col4 = st.columns(4)
with col1:
    done = st.session_state.get("vehicle_info") is not None
    st.metric("1. 차량정보", "✅ 완료" if done else "⏳ 대기")
with col2:
    done = len(st.session_state.get("selected_cctvs", [])) > 0
    st.metric("2. CCTV선택", "✅ 완료" if done else "⏳ 대기")
with col3:
    done = st.session_state.get("search_done", False)
    st.metric("3. 탐색", "✅ 완료" if done else "⏳ 대기")
with col4:
    done = st.session_state.get("results") is not None
    st.metric("4. 결과", "✅ 확인가능" if done else "⏳ 대기")