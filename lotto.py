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

st.subheader("1. 기존 구매 게임 입력 (최대 5게임)")
st.caption("※ 최소 1게임 이상 입력. 입력하지 않은 칸은 자동으로 제외됩니다.")
game1_str = st.text_input("게임 1 (예: 3 12 18 25 33 41)", key="g1")
game2_str = st.text_input("게임 2", key="g2")
game3_str = st.text_input("게임 3", key="g3")
game4_str = st.text_input("게임 4 (선택)", key="g4")
game5_str = st.text_input("게임 5 (선택)", key="g5")

st.markdown("---")
st.subheader("2. 추가 커스텀 생성 옵션 (선택)")
col1, col2 = st.columns(2)
with col1:
    custom_n = st.number_input("추가 생성 N (선택할 고정 개수)", min_value=0, max_value=6, value=2)
with col2:
    custom_m = st.number_input("추가 생성 M (생성할 게임 수)", min_value=0, max_value=20, value=1)

if st.button("✨ 기본 4개 세트 + 추가 조합 생성하기", type="primary", use_container_width=True):
    # 입력 필드 5개를 모두 가져옵니다.
    raw_inputs = [game1_str, game2_str, game3_str, game4_str, game5_str]
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
                st.error(f"게임 {idx+1}: 숫자 형식으로 입력해주세요.")
                st.stop()

    if not input_games:
        st.warning("최소 1개 이상의 게임을 입력하셔야 합니다.")
        st.stop()

    all_user_nums = [num for game in input_games for num in game]
    unique_user_nums = sorted(list(set(all_user_nums)))
    unselected_nums = sorted(list(set(range(1, 46)) - set(unique_user_nums)))

    generated_rows = []  # 구글 시트에 저장할 데이터
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---------------------------------------------------------
    # [파트 1] 기본 세트 4게임 (N=0, 1, 2, 3 각 1개씩)
    # ---------------------------------------------------------
    st.subheader("🎯 [기본 세트] N=0, 1, 2, 3 분산 조합 (4게임)")
    
    for n in range(4):
        if n > len(unique_user_nums):
            st.warning(f"N={n} 세트: 입력된 유일 숫자가 {len(unique_user_nums)}개뿐이어서 생성할 수 없습니다.")
            continue

        picked_user = sorted(random.sample(unique_user_nums, n)) if n > 0 else []
        picked_unselected = sorted(random.sample(unselected_nums, 6 - n))
        final_game = sorted(picked_user + picked_unselected)
        
        user_num_str = " ".join(map(str, picked_user)) if picked_user else "없음"
        
        # 화면 출력
        st.success(f"**기본 {n+1} (N={n}):** {final_game}  *(선택된 번호: {user_num_str})*")
        
        # 저장용 로우 생성
        generated_rows.append({
            "시각": now_str,
            "입력_게임1": " ".join(map(str, input_games[0])) if len(input_games) > 0 else "",
            "입력_게임2": " ".join(map(str, input_games[1])) if len(input_games) > 1 else "",
            "입력_게임3": " ".join(map(str, input_games[2])) if len(input_games) > 2 else "",
            "입력_게임4": " ".join(map(str, input_games[3])) if len(input_games) > 3 else "",
            "입력_게임5": " ".join(map(str, input_games[4])) if len(input_games) > 4 else "",
            "생성_게임": f"기본 N={n}",
            "선택된_N개": user_num_str,
            "상세내용": " ".join(map(str, final_game))
        })

    # ---------------------------------------------------------
    # [파트 2] 추가 커스텀 생성 (N, M 설정 반영)
    # ---------------------------------------------------------
    if custom_m > 0:
        st.markdown("---")
        st.subheader(f"⚙️ [추가 생성] N={custom_n} 고정 조합 ({custom_m}게임)")
        
        if custom_n > len(unique_user_nums):
            st.error(f"입력된 유일 숫자가 {len(unique_user_nums)}개입니다. 추가 생성 N을 {len(unique_user_nums)} 이하로 설정해주세요.")
        else:
            fixed_user = sorted(random.sample(unique_user_nums, custom_n)) if custom_n > 0 else []
            fixed_user_str = " ".join(map(str, fixed_user)) if fixed_user else "없음"
            
            st.info(f"📌 **이번 추가 생성 고정 번호({custom_n}개):** {fixed_user_str}")
            
            for idx in range(1, custom_m + 1):
                picked_unselected = sorted(random.sample(unselected_nums, 6 - custom_n))
                final_game = sorted(fixed_user + picked_unselected)
                
                # 화면 출력
                st.success(f"**추가 게임 {idx:02d}:** {final_game}")
                
                # 저장용 로우 생성
                generated_rows.append({
                    "시각": now_str,
                    "입력_게임1": " ".join(map(str, input_games[0])) if len(input_games) > 0 else "",
                    "입력_게임2": " ".join(map(str, input_games[1])) if len(input_games) > 1 else "",
                    "입력_게임3": " ".join(map(str, input_games[2])) if len(input_games) > 2 else "",
                    "입력_게임4": " ".join(map(str, input_games[3])) if len(input_games) > 3 else "",
                    "입력_게임5": " ".join(map(str, input_games[4])) if len(input_games) > 4 else "",
                    "생성_게임": f"추가 {idx:02d} (N={custom_n})",
                    "선택된_N개": fixed_user_str,
                    "상세내용": " ".join(map(str, final_game))
                })

    # ---------------------------------------------------------
    # [파트 3] Google Sheets 데이터 저장
    # ---------------------------------------------------------
    try:
        existing_data = conn.read(ttl=0)
        updated_df = pd.concat([pd.DataFrame(existing_data), pd.DataFrame(generated_rows)], ignore_index=True)
        conn.update(data=updated_df)
        st.toast("🟢 모든 생성 데이터가 구글 시트에 성공적으로 저장되었습니다!", icon="✅")
    except Exception as e:
        st.error(f"구글 시트 저장 중 오류 발생: {e}")
