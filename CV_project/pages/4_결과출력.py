# pages/4_결과출력.py
import streamlit as st
import cv2
from datetime import datetime, timedelta

from core.state import init_session_state

init_session_state()

st.title("4️⃣ 탐색 결과")

if not st.session_state.search_done or not st.session_state.results:
    st.warning("아직 탐색이 완료되지 않았습니다. **3️⃣ 탐색시작**을 먼저 실행하세요.")
    st.stop()

results = st.session_state.results

# 임계값 슬라이더
st.markdown("#### 🎚️ 일치율 임계값 조정")
st.caption("슬라이더를 움직여 후보로 출력할 일치율 기준을 조정하세요. (탐색은 다시 안 합니다)")

threshold_pct = st.slider(
    "임계값 (%)",
    min_value=10, max_value=99, 
    value=int(st.session_state.threshold), step=1,
    label_visibility="collapsed",
)
st.session_state.threshold = threshold_pct
threshold = threshold_pct / 100.0

st.markdown("---")

# 각 CCTV의 "분류된 모든 차량" 중에서 임계값 이상인 것만 후보로 추출 
candidates = []
for r in results:
    res = r["result"]
    if res is None or not res.get("all_classified"):
        continue
    for cls in res["all_classified"]:
        if cls["match"]["overall"] >= threshold:
            candidates.append({
                "cctv": r["cctv"],
                "result": {
                    "match": cls["match"],
                    "predicted": cls["pred"],
                    "frame": cls["frame"],
                    "timestamp_sec": cls["timestamp_sec"],
                    "track_id": cls["track_id"],
                },
            })

# 일치율 내림차순 정렬
candidates.sort(key=lambda r: r["result"]["match"]["overall"], reverse=True)

# 요약 메트릭
total_classified = sum(
    len(r["result"]["all_classified"]) if r["result"] and r["result"].get("all_classified") else 0
    for r in results
)
m1, m2, m3, m4 = st.columns(4)
m1.metric("분석한 CCTV", f"{len(results)}개")
m2.metric("분류된 차량 (전체)", f"{total_classified}대")
m3.metric("임계값 이상 후보", f"{len(candidates)}건")
m4.metric("적용 임계값", f"{threshold_pct}%")

st.markdown("---")

# 후보가 없을 때
if not candidates:
    st.error(
        f"⚠️ 임계값 {threshold_pct}% 이상 일치하는 차량이 검출되지 않았습니다. "
        "슬라이더를 더 낮춰보세요."
    )

    # 분류된 모든 차량을 일치율 순으로 미리보기
    all_classified_flat = []
    for r in results:
        res = r["result"]
        if res and res.get("all_classified"):
            for cls in res["all_classified"]:
                all_classified_flat.append({
                    "cctv_id": r["cctv"]["id"],
                    "cctv_name": r["cctv"]["name"],
                    "track_id": cls["track_id"],
                    "match": cls["match"],
                    "pred": cls["pred"],
                })
    all_classified_flat.sort(key=lambda x: x["match"]["overall"], reverse=True)

    if all_classified_flat:
        st.markdown("### 🔎 분류된 차량 (일치율 순)")
        st.caption("임계값을 더 낮추면 이 차량들이 후보로 표시됩니다.")
        for i, item in enumerate(all_classified_flat[:20], 1):
            with st.container(border=True):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(
                        f"**#{i}** CCTV #{item['cctv_id']} ({item['cctv_name']}) "
                        f"— Track {item['track_id']}"
                    )
                    st.markdown(
                        f"예측: `{item['pred']['model']}` · `{item['pred']['color']}` · "
                        f"`{item['pred']['brand']}` · `{item['pred']['year']}`"
                    )
                with c2:
                    st.metric(
                        "종합 일치율",
                        f"{item['match']['overall']*100:.1f}%",
                        item["match"]["grade"],
                    )

    # 디버그 정보
    with st.expander("🔧 전체 결과 + 디버그 정보 보기"):
        for r in results:
            res = r["result"]
            cctv_id = r["cctv"]["id"]
            cctv_name = r["cctv"]["name"]

            st.markdown(f"#### CCTV #{cctv_id} — {cctv_name}")

            if res is None:
                st.write("❌ 처리 결과 없음")
                continue

            n_classified = len(res.get("all_classified", []))
            if n_classified > 0:
                st.write(f"✅ 분류된 차량 수: **{n_classified}대**")
                if res.get("match"):
                    m = res["match"]
                    st.write(
                        f"   최고 일치율: **{m['overall']*100:.1f}%** ({m['grade']})  "
                        f"→ 예측: `{res['predicted']}`"
                    )
            else:
                st.write("❌ 분류된 차량 없음")

            if res.get("debug"):
                d = res["debug"]
                st.json(d)

                # 자동 진단
                if d.get("error"):
                    st.error(f"🚨 {d['error']}")
                elif d["frames_with_detection"] == 0:
                    st.warning(
                        "⚠️ YOLO가 단 한 프레임에서도 차량을 감지하지 못했습니다. "
                        "영상에 차량이 없거나 클래스 필터링 문제일 수 있습니다."
                    )
                elif d["tracks_seen"] == 0:
                    st.warning(
                        "⚠️ 추적된 차량이 없습니다. 차량이 너무 작거나(50px 미만) 추적 실패."
                    )
                elif d["tracks_classified"] == 0:
                    st.warning(
                        f"⚠️ {d['tracks_seen']}대의 차량이 추적됐지만 quality_threshold "
                        f"({d['quality_threshold']})를 넘지 못해 분류되지 않았습니다. "
                        f"이 영상에서 본 최대 점수: **{d['max_score_seen']:.0f}**. "
                        f"임계값을 이 값보다 낮춰야 합니다."
                    )

            st.markdown("---")
    st.stop()

# 후보가 있을 때 — 상위 결과 카드 출력
st.success(f"🚨 일치 차량을 **{len(candidates)}건** 발견했습니다.")

# 너무 많으면 상위 N개로 제한
MAX_DISPLAY = 10
display_candidates = candidates[:MAX_DISPLAY]
if len(candidates) > MAX_DISPLAY:
    st.info(f"💡 상위 {MAX_DISPLAY}건만 표시합니다 (전체 {len(candidates)}건).")

for rank, r in enumerate(display_candidates, 1):
    cctv = r["cctv"]
    res = r["result"]
    match = res["match"]
    pred = res["predicted"]

    ts = res["timestamp_sec"]
    base = datetime(2026, 5, 18, 14, 0, 0)
    when = base + timedelta(seconds=ts)

    with st.container(border=True):
        c1, c2 = st.columns([1.2, 1])

        with c1:
            # 순위 메달 이모지
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "🏅"
            st.markdown(f"### {medal} 후보 #{rank}")
            st.markdown(f"📍 **위치:** {cctv['name']} (CCTV #{cctv['id']})")
            st.markdown(f"⏰ **시간:** {when.strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown(f"🎯 **Track ID:** `{res['track_id']}`")
            st.markdown(f"📊 **최종 등급:** `{match['grade']}`")
            st.progress(match["overall"], text=f"종합 일치율 {match['overall']*100:.1f}%")

            with st.expander("⬇️ 자세히 보기 — 요소별 세부 일치율"):
                v = st.session_state.vehicle_info
                items = [
                    ("차종/모델", v.get("model", "?"), pred["model"], match["per_field"]["model"]),
                    ("색상",      v["color"],          pred["color"], match["per_field"]["color"]),
                    ("제조사",    v["brand"],          pred["brand"], match["per_field"]["brand"]),
                    ("연식",      v["year"],           pred["year"],  match["per_field"]["year"]),
                ]
                for label, target_val, pred_val, prob in items:
                    cc1, cc2, cc3 = st.columns([1.2, 1.8, 1])
                    cc1.markdown(f"**{label}**")
                    cc2.markdown(f"입력 `{target_val}`  ·  예측 `{pred_val}`")
                    cc3.metric(label="확률", value=f"{prob*100:.0f}%", label_visibility="collapsed")

                # 어느 라벨로 매칭됐는지 (resolve 결과)
                if "resolved" in match:
                    st.caption(f"🔎 매칭된 실제 라벨: `{match['resolved']}`")

        with c2:
            st.markdown("**탐지 화면:**")
            frame_rgb = cv2.cvtColor(res["frame"], cv2.COLOR_BGR2RGB)
            # st.image(frame_rgb, use_container_width=True, caption=f"Track ID: {res['track_id']}")
            st.image(frame_rgb, use_column_width=True, caption=f"Track ID: {res['track_id']}")

# 하단 액션
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 새로운 사건 시작하기", use_container_width=True):
        for k in ["vehicle_info", "selected_cctvs", "search_done", "results"]:
            st.session_state[k] = None if k != "selected_cctvs" else []
        st.rerun()
with col2:
    with st.expander("🔧 디버그 정보 보기"):
        for r in results:
            res = r["result"]
            if res and res.get("debug"):
                st.markdown(f"**CCTV #{r['cctv']['id']}** — {r['cctv']['name']}")
                st.json(res["debug"])