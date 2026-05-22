# core/state.py
import streamlit as st

def init_session_state():
    """세션 상태 초기값 설정"""
    defaults = {
        "vehicle_info": None,        # {"model_type":..., "color":..., "brand":..., "year":..., "location":...}
        "selected_cctvs": [],         # [{"id":1, "name":"...", "lat":..., "lng":..., "video":"..."}]
        "search_done": False,         # 탐색 완료 여부
        "results": None,              # 탐색 결과 리스트
        "threshold": 80,              # 임계값(%)
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def reset_search():
    """탐색 결과만 초기화"""
    st.session_state.search_done = False
    st.session_state.results = None