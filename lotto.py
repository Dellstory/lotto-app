import streamlit as st
import random
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 자동 번역 충돌 방지 설정
st.markdown("<style>html { translate: no; }</style>", unsafe_allow_html=True)
st.set_page_config(page_title="로또 번호 맞춤 조합기", page_icon="🎲", layout="centered")

st.title("🎲 로또 번호 맞춤 조합기")

# Google Sheets 연결 초기화
conn = st.connection("gsheets", type=GSheetsConnection)

st.subheader("1. 기존 구매 게임 입력")
game1_str = st.text_input("게임 1 (예: 3 12 18 25 33 41)", key="g1")
game2_str = st.text_input("게임 2", key="g2")
game3_str = st.text_input("게임 3", key="g3")

col1, col2 = st.columns(2)
with col1:
    n_val = st.number_input("입력 번호 중 선택할 개수 (N)", min_value=0, max_value=6, value=2)
with col2:
    m_val = st.number_input("생성할 총 게임 수 (M)", min_value=1, max_value=20, value=5)

if st.button("✨ 로또 번호 조합 생성하기", type="primary", use_container_width=True):
    raw_inputs = [game1_str, game2_str, game3_str]
    input_games = []
    
    for idx, raw in enumerate(raw_inputs):
        if raw.strip():
            try:
                nums = list(map(int, raw.strip().split()))
                if len(nums) != 6 or not all(1 <= x <= 45 for x in nums) or len(set(nums)) != 6:
                    st.error(f"게임 {idx+1}: 올바른 6개 숫자를 입력해주세요.")
                    st.stop()
                input_games.append(sorted(nums))
            except ValueError:
                st.error("숫자 형식으로 입력해주세요.")
                st.stop()

    if not input_games:
        st.warning("최소 1개 이상의 게임을 입력하셔야 합니다.")
        st.stop()

    all_user_nums = [num for game in input_games for num in game]
    unique_user_nums = sorted(list(set(all_user_nums)))
    unselected_nums = sorted(list(set(range(1, 46)) - set(unique_user_nums)))

    generated_games = []
    for _ in range(m_val):
        picked_user = random.sample(unique_user_nums, n_val) if n_val > 0 else []
        picked_unselected = random.sample(unselected_nums, 6 - n_val)
        generated_games.append(sorted(picked_user + picked_unselected))

    st.subheader("🎯 생성 결과")
    for i, game in enumerate(generated_games, 1):
        st.success(f"**게임 {i:02d}:** {game}")

    # Google Sheets 데이터 저장 로직
    try:
        # 기존 데이터를 불러옴
        existing_data = conn.read(ttl=0)
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_rows = []
        
        for idx, gen_game in enumerate(generated_games, 1):
            row = {
                "시각": now_str,
                "입력_게임1": " ".join(map(str, input_games[0])) if len(input_games) > 0 else "",
                "입력_게임2": " ".join(map(str, input_games[1])) if len(input_games) > 1 else "",
                "입력_게임3": " ".join(map(str, input_games[2])) if len(input_games) > 2 else "",
                "생성_게임": f"게임 {idx:02d}",
                "상세내용": " ".join(map(str, gen_game))
            }
            new_rows.append(row)
            
        updated_df = pd.concat([pd.DataFrame(existing_data), pd.DataFrame(new_rows)], ignore_index=True)
        conn.update(data=updated_df)
        st.toast("🟢 구글 시트에 데이터가 저장되었습니다!", icon="✅")
    except Exception as e:
        st.error(f"구글 시트 저장 중 오류 발생: {e}")
