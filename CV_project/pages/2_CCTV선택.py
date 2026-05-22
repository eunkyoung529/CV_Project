# pages/2_CCTV선택.py
import streamlit as st
import folium
from streamlit_folium import st_folium

from core.state import init_session_state, reset_search

init_session_state()

st.title("2️⃣ CCTV 선택")
st.caption("사고 지점 주변 CCTV를 지도에서 클릭해 최대 4개까지 선택하세요.")

if not st.session_state.vehicle_info:
    st.warning("먼저 **1️⃣ 차량정보입력** 단계를 완료하세요.")
    st.stop()

# 사고 위치 표시
st.info(f"📍 사고 위치: **{st.session_state.vehicle_info['location']}**")

# --- 더미 CCTV 데이터 (실제로는 DB나 API에서 가져옴) ---
# 부천시 원미구 길주로 일대를 중심으로 한 CCTV 8개
# CCTV_DB = [
#     {"id": 1, "name": "김가네 상동점 앞 CCTV", "lat": 37.5050, "lng": 126.7560, "video": "videos/cctv_01.mp4"},
#     {"id": 2, "name": "길주로 사거리 CCTV", "lat": 37.5042, "lng": 126.7585, "video": "videos/cctv_02.mp4"},
#     {"id": 3, "name": "부천시청 정문 CCTV", "lat": 37.5035, "lng": 126.7660, "video": "videos/cctv_03.mp4"},
#     {"id": 4, "name": "원미구청 후문 CCTV", "lat": 37.5080, "lng": 126.7610, "video": "videos/cctv_04.mp4"},
#     {"id": 5, "name": "상동역 3번출구", "lat": 37.5045, "lng": 126.7530, "video": "videos/cctv_01.mp4"},
#     {"id": 6, "name": "중동역 1번출구", "lat": 37.5060, "lng": 126.7700, "video": "videos/cctv_02.mp4"},
#     {"id": 7, "name": "부천실내체육관 앞", "lat": 37.5025, "lng": 126.7625, "video": "videos/cctv_03.mp4"},
#     {"id": 8, "name": "현대백화점 중동점", "lat": 37.5070, "lng": 126.7550, "video": "videos/cctv_04.mp4"},
# ]
CCTV_DB = [
    {"id": 1, "name": "김가네 상동점 앞 CCTV", "lat": 37.5050, "lng": 126.7560, "video": "videos/cctv_video_test3.mp4"},
    {"id": 2, "name": "길주로 사거리 CCTV",     "lat": 37.5042, "lng": 126.7585, "video": "videos/cctv_video_test3.mp4"},
    {"id": 3, "name": "부천시청 정문 CCTV",     "lat": 37.5035, "lng": 126.7660, "video": "videos/cctv_video_test3.mp4"},
    {"id": 4, "name": "원미구청 후문 CCTV",     "lat": 37.5080, "lng": 126.7610, "video": "videos/cctv_video_test3.mp4"},
    {"id": 5, "name": "상동역 3번출구",          "lat": 37.5045, "lng": 126.7530, "video": "videos/cctv_video_test3.mp4"},
    {"id": 6, "name": "중동역 1번출구",          "lat": 37.5060, "lng": 126.7700, "video": "videos/cctv_video_test3.mp4"},
    {"id": 7, "name": "부천실내체육관 앞",       "lat": 37.5025, "lng": 126.7625, "video": "videos/cctv_video_test3.mp4"},
    {"id": 8, "name": "현대백화점 중동점",       "lat": 37.5070, "lng": 126.7550, "video": "videos/cctv_video_test3.mp4"},
]

CENTER = [37.5050, 126.7600]  # 부천 원미구 중심

# 현재 선택된 ID 셋
selected_ids = {c["id"] for c in st.session_state.selected_cctvs}

# 지도 생성
m = folium.Map(location=CENTER, zoom_start=15, tiles="OpenStreetMap")

# 사고 지점 마커
folium.Marker(
    CENTER,
    popup="🚨 뺑소니 사고 지점",
    icon=folium.Icon(color="red", icon="exclamation-sign"),
).add_to(m)

# CCTV 마커들
for cctv in CCTV_DB:
    is_selected = cctv["id"] in selected_ids
    color = "green" if is_selected else "blue"
    icon = "ok-sign" if is_selected else "camera"
    folium.Marker(
        [cctv["lat"], cctv["lng"]],
        popup=f"CCTV #{cctv['id']}: {cctv['name']}",
        tooltip=f"CCTV #{cctv['id']} — 클릭해 선택",
        icon=folium.Icon(color=color, icon=icon, prefix="glyphicon"),
    ).add_to(m)

# 지도 출력
map_data = st_folium(m, width=900, height=500, returned_objects=["last_object_clicked"])

# 클릭된 마커 처리
clicked = map_data.get("last_object_clicked") if map_data else None
if clicked:
    lat, lng = clicked["lat"], clicked["lng"]
    # 가장 가까운 CCTV 찾기
    target = min(CCTV_DB, key=lambda c: (c["lat"] - lat) ** 2 + (c["lng"] - lng) ** 2)
    # 사고 지점이 아닐 때만
    if abs(target["lat"] - lat) < 0.0005 and abs(target["lng"] - lng) < 0.0005:
        if target["id"] in selected_ids:
            st.session_state.selected_cctvs = [
                c for c in st.session_state.selected_cctvs if c["id"] != target["id"]
            ]
            reset_search()
            st.rerun()
        else:
            if len(st.session_state.selected_cctvs) < 4:
                st.session_state.selected_cctvs.append(target)
                reset_search()
                st.rerun()
            else:
                st.warning("⚠️ CCTV는 최대 4개까지 선택할 수 있습니다. 기존 선택을 먼저 해제하세요.")

# 선택 목록
st.markdown("---")
st.subheader(f"✅ 선택된 CCTV ({len(st.session_state.selected_cctvs)}/4)")

if not st.session_state.selected_cctvs:
    st.info("지도에서 파란색 카메라 마커를 클릭해 선택하세요.")
else:
    cols = st.columns(4)
    for i, cctv in enumerate(st.session_state.selected_cctvs):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"**CCTV #{cctv['id']}**")
                st.caption(cctv["name"])
                if st.button("❌ 해제", key=f"remove_{cctv['id']}"):
                    st.session_state.selected_cctvs = [
                        c for c in st.session_state.selected_cctvs if c["id"] != cctv["id"]
                    ]
                    reset_search()
                    st.rerun()

    st.success("선택 완료! 사이드바에서 **3️⃣ 탐색시작** 단계로 진행하세요.")