import streamlit as st
import random
import pandas as pd
import os
from datetime import datetime

# 페이지 기본 설정 (모바일 화면에 최적화)
st.set_page_config(page_title="로또 번호 맞춤 조합기", page_icon="🎲", layout="centered")

st.title("🎲 로또 번호 맞춤 조합기")
st.write("구매한 게임 번호를 입력하고 맞춤 조합을 생성해보세요.")

# 1. 게임 입력 받기
st.subheader("1. 기존 구매 게임 입력")
st.caption("2게임만 입력 시 3번째 게임은 비워두시면 됩니다.")

game1_str = st.text_input("게임 1 (예: 3 12 18 25 33 41)", key="g1")
game2_str = st.text_input("게임 2", key="g2")
game3_str = st.text_input("게임 3", key="g3")

# 2. 조합 옵션 설정
st.subheader("2. 조합 옵션 설정")
col1, col2 = st.columns(2)
with col1:
    n_val = st.number_input("입력 번호 중 선택할 개수 (N)", min_value=0, max_value=6, value=2)
with col2:
    m_val = st.number_input("생성할 총 게임 수 (M)", min_value=1, max_value=20, value=5)

# 3. 생성 버튼 동작
if st.button("✨ 로또 번호 조합 생성하기", type="primary", use_container_width=True):
    # 입력 검증
    raw_inputs = [game1_str, game2_str, game3_str]
    input_games = []
    
    for idx, raw in enumerate(raw_inputs):
        if raw.strip():
            try:
                nums = list(map(int, raw.strip().split()))
                if len(nums) != 6 or not all(1 <= x <= 45 for x in nums) or len(set(nums)) != 6:
                    st.error(f"게임 {idx+1}: 1~45 사이의 중복 없는 숫자 6개를 입력해주세요.")
                    st.stop()
                input_games.append(sorted(nums))
            except ValueError:
                st.error(f"게임 {idx+1}: 올바른 숫자 형식으로 입력해주세요.")
                st.stop()

    if not input_games:
        st.warning("최소 1개 이상의 게임을 입력하셔야 합니다.")
        st.stop()

    # 번호 추출 로직
    all_user_nums = [num for game in input_games for num in game]
    unique_user_nums = sorted(list(set(all_user_nums)))
    unselected_nums = sorted(list(set(range(1, 46)) - set(unique_user_nums)))

    if n_val > len(unique_user_nums):
        st.error(f"N({n_val})은 입력된 고유 번호 개수({len(unique_user_nums)}개)보다 클 수 없습니다.")
        st.stop()

    # 결과 생성
    generated_games = []
    for _ in range(m_val):
        picked_user = random.sample(unique_user_nums, n_val) if n_val > 0 else []
        picked_unselected = random.sample(unselected_nums, 6 - n_val)
        generated_games.append(sorted(picked_user + picked_unselected))

    # 화면에 결과 출력
    st.subheader("🎯 생성 결과")
    st.info(f"입력 번호 활용: {len(unique_user_nums)}개 중 {n_val}개 / 미입력 번호 활용: {len(unselected_nums)}개 중 {6-n_val}개")
    
    for i, game in enumerate(generated_games, 1):
        st.success(f"**게임 {i:02d}:** {game}")

    # CSV 파일 누적 저장 (lotto.csv)
    filename = "lotto.csv"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 저장할 데이터 행 구성
    row_data = {"시각": now_str}
    for i, g in enumerate(input_games, 1):
        row_data[f"입력_게임{i}"] = " ".join(map(str, g))
    for i, g in enumerate(generated_games, 1):
        row_data[f"생성_게임{i}"] = " ".join(map(str, g))

    new_df = pd.DataFrame([row_data])

    if os.path.exists(filename):
        new_df.to_csv(filename, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        new_df.to_csv(filename, mode='w', header=True, index=False, encoding='utf-8-sig')

    st.toast("💾 결과가 lotto.csv 파일에 저장되었습니다!", icon="✅")