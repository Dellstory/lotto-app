import streamlit as st
import random
from collections import Counter
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# =============================================================
# [헬퍼 함수] 통계 필터 및 밸런스 검증
# =============================================================
def calculate_stats(numbers):
    """6개 번호의 총합, 고저 비율, 홀짝 비율 및 황금 밸런스 여부를 반환"""
    total_sum = sum(numbers)
    low_count = sum(1 for x in numbers if x <= 22)   # 저번호(1~22)
    high_count = 6 - low_count                       # 고번호(23~45)
    odd_count = sum(1 for x in numbers if x % 2 != 0) # 홀수
    even_count = 6 - odd_count                       # 짝수
    
    # 황금 구간 조건: 총합 100~170 AND 고저 비율 2:4 ~ 4:2
    is_balanced = (100 <= total_sum <= 170) and (2 <= low_count <= 4)
    
    return {
        "sum": total_sum,
        "low_high": f"{low_count}:{high_count}",
        "odd_even": f"{odd_count}:{even_count}",
        "is_balanced": is_balanced
    }

def generate_balanced_random_game():
    """총합 100~170 및 고저 균형(2:4~4:2)을 만족하는 랜덤 1게임 생성"""
    while True:
        game = sorted(random.sample(range(1, 46), 6))
        stats = calculate_stats(game)
        if stats["is_balanced"]:
            return game

# =============================================================
# [핵심 로직] N개 고정수 + 미출현 번호 기반 연쇄 소거 세트 생성
# =============================================================
def generate_chain_sojeo_2games(base_games, n_value):
    """
    1. 메인 게임: 시작 3게임의 빈도 1위~N위 고정수 + 시작 3게임 미출현 번호에서 나머지 채움
    2. 1차 소거 게임: 메인 게임에 사용된 번호 제외 후 생성
    """
    selected_set = []
    used_numbers_in_set = set()
    
    all_base_nums = [num for g in base_games for num in g]
    base_nums_set = set(all_base_nums)
    
    # 시작 3게임에 출현하지 않은 번호 풀 (미출현 번호)
    unappeared_base_pool = list(set(range(1, 46)) - base_nums_set)
    
    # 1. 메인 게임 고정수 추출
    fixed_nums = set()
    if n_value > 0 and len(all_base_nums) >= n_value:
        counts = Counter(all_base_nums)
        most_common = [num for num, _ in counts.most_common(n_value)]
        fixed_nums = set(most_common)
    
    needed = 6 - len(fixed_nums)
    
    # 메인 게임 생성 (나머지 칸은 시작 게임 미출현 번호에서 무작위 선택)
    attempts = 0
    while True:
        attempts += 1
        # 미출현 번호 풀이 충분하고 시도 횟수가 500회 이하인 경우 미출현 번호에서만 선택
        if len(unappeared_base_pool) >= needed and attempts <= 500:
            candidate_pool = unappeared_base_pool
        else:
            # 보충 필요 시 고정수를 제외한 전체 번호에서 선택
            candidate_pool = list(set(range(1, 46)) - fixed_nums)
            
        main_game = sorted(list(fixed_nums) + random.sample(candidate_pool, needed))
        if calculate_stats(main_game)["is_balanced"]:
            selected_set.append(main_game)
            used_numbers_in_set.update(main_game)
            break
            
    # 2. 1차 소거 게임 생성 (메인 게임에 사용된 번호 제외)
    while True:
        available_pool = list(set(range(1, 46)) - used_numbers_in_set)
        if len(available_pool) < 6:
            available_pool = list(set(range(1, 46)))
        sojeo1_game = sorted(random.sample(available_pool, 6))
        if calculate_stats(sojeo1_game)["is_balanced"]:
            selected_set.append(sojeo1_game)
            break

    return selected_set

# =============================================================
# [보너스 로직] 미출현 번호 기반 10번째 게임 생성
# =============================================================
def generate_unused_bonus_game(previous_9_games):
    """이전 9개 게임에 등장하지 않은 번호 우선 활용하여 황금구간 1게임 생성"""
    used_nums = set(num for game in previous_9_games for num in game)
    unused_nums = list(set(range(1, 46)) - used_nums)
    
    while True:
        if len(unused_nums) >= 6:
            candidate = sorted(random.sample(unused_nums, 6))
        else:
            needed = 6 - len(unused_nums)
            pool_rest = list(set(range(1, 46)) - set(unused_nums))
            candidate = sorted(unused_nums + random.sample(pool_rest, needed))
            
        if calculate_stats(candidate)["is_balanced"]:
            return candidate, sorted(unused_nums)

# =============================================================
# Streamlit UI 구현 및 구글 시트 연동
# =============================================================
st.set_page_config(page_title="로또 황금밸런스 분석기 (총 10게임)", layout="wide")

st.title("🎲 로또 황금밸런스 & 연쇄소거 분석기")
st.caption("시작 3게임 → N=1,2,3 세트(6게임) + 미출현 번호 보너스(1게임) = 총 10게임 자동 추출 & 구글 시트 기록")

# 구글 시트 커넥션 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    conn = None

st.sidebar.header("⚙️ 게임 방식 선택")
input_mode = st.sidebar.radio("시작 3게임 설정 방식", ["직접 입력하기", "랜덤 자동 생성"])

user_entered_games = []

if input_mode == "직접 입력하기":
    st.subheader("📝 시작 게임 직접 입력 (1~3개 선택 가능)")
    st.info("💡 1개나 2개만 입력하셔도 됩니다! 입력하지 않은 빈 칸은 황금 밸런스 자동 게임으로 채워집니다.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        g1_str = st.text_input("게임 1 번호", value="", placeholder="예: 3 12 18 27 34 41")
    with col2:
        g2_str = st.text_input("게임 2 번호 (선택)", value="", placeholder="예: 5 14 22 30 37 44")
    with col3:
        g3_str = st.text_input("게임 3 번호 (선택)", value="", placeholder="예: 1 8 19 25 33 40")
        
    def parse_input(input_str):
        if not input_str.strip():
            return []
        cleaned = input_str.replace(",", " ")
        tokens = cleaned.split()
        nums = []
        for t in tokens:
            if t.isdigit():
                num = int(t)
                if 1 <= num <= 45 and num not in nums:
                    nums.append(num)
        return sorted(nums)

    g1 = parse_input(g1_str)
    g2 = parse_input(g2_str)
    g3 = parse_input(g3_str)

    for g in [g1, g2, g3]:
        if len(g) == 6:
            user_entered_games.append(g)

    if g1_str or g2_str or g3_str:
        if len(user_entered_games) > 0:
            st.success(f"✅ {len(user_entered_games)}개 게임 입력 확인 완료! (부족한 {3 - len(user_entered_games)}개는 자동 보충됩니다)")
        else:
            st.warning("⚠️ 각 입력 칸마다 1~45 사이의 서로 다른 숫자 6개를 정확히 입력해 주세요.")

else:
    st.subheader("🎲 황금 밸런스 자동 뽑기 3게임")
    st.write("버튼을 누르면 총합 100~170 사이의 자동 검증된 3게임이 생성됩니다.")

st.divider()

if st.button("🚀 총 10게임 세트 생성하기", type="primary"):
    base_games = []
    
    if input_mode == "랜덤 자동 생성":
        base_games = [generate_balanced_random_game() for _ in range(3)]
    else:
        if len(user_entered_games) > 0:
            base_games = list(user_entered_games)
            while len(base_games) < 3:
                base_games.append(generate_balanced_random_game())
        else:
            st.error("❌ 입력된 번호가 없습니다. 최소 1개 게임 이상 번호 6개를 제대로 입력해 주세요.")

    if len(base_games) == 3:
        # N=1, N=2, N=3 연쇄 소거 세트 생성 (각 2게임씩 총 6게임)
        set_n1 = generate_chain_sojeo_2games(base_games, n_value=1)
        set_n2 = generate_chain_sojeo_2games(base_games, n_value=2)
        set_n3 = generate_chain_sojeo_2games(base_games, n_value=3)

        # 이전 9개 게임 수집 후 10번째 미출현 보너스 게임 생성
        previous_9 = base_games + set_n1 + set_n2 + set_n3
        bonus_game, unused_numbers = generate_unused_bonus_game(previous_9)

        # -------------------------------------------------------------
        # 결과 화면 출력
        # -------------------------------------------------------------
        labels = ["메인 게임", "1차 소거 게임"]

        # 1. 시작 3게임
        st.subheader("1️⃣ 시작 게임 (기반 3게임)")
        for i, game in enumerate(base_games, 1):
            stats = calculate_stats(game)
            badge = "🟢 황금구간" if stats["is_balanced"] else "🟡 일반구간"
            
            if input_mode == "직접 입력하기" and i <= len(user_entered_games):
                tag = " (수동입력)"
            elif input_mode == "직접 입력하기":
                tag = " (자동보충)"
            else:
                tag = ""
                
            st.markdown(f"**게임 {i}{tag}:** `{game}` | **[합계: {stats['sum']}]** ({badge}) | 저고 `{stats['low_high']}` | 홀짝 `{stats['odd_even']}`")

        st.divider()

        # 2. N=1 세트
        st.subheader("2️⃣ N=1 세트 (2게임)")
        for label, game in zip(labels, set_n1):
            stats = calculate_stats(game)
            st.markdown(f"**{label} (N=1):** `{game}` | 🟢 **[합계: {stats['sum']}]** | 저고 `{stats['low_high']}` | 홀짝 `{stats['odd_even']}`")

        st.divider()

        # 3. N=2 세트
        st.subheader("3️⃣ N=2 세트 (2게임)")
        for label, game in zip(labels, set_n2):
            stats = calculate_stats(game)
            st.markdown(f"**{label} (N=2):** `{game}` | 🟢 **[합계: {stats['sum']}]** | 저고 `{stats['low_high']}` | 홀짝 `{stats['odd_even']}`")

        st.divider()

        # 4. N=3 세트
        st.subheader("4️⃣ N=3 세트 (2게임)")
        for label, game in zip(labels, set_n3):
            stats = calculate_stats(game)
            st.markdown(f"**{label} (N=3):** `{game}` | 🟢 **[합계: {stats['sum']}]** | 저고 `{stats['low_high']}` | 홀짝 `{stats['odd_even']}`")

        st.divider()

        # 5. 10번째 보너스 게임
        st.subheader("5️⃣ 미출현 번호 보너스 게임 (10번째 게임)")
        b_stats = calculate_stats(bonus_game)
        st.markdown(f"🎯 **보너스 게임:** `{bonus_game}` | 🟢 **[합계: {b_stats['sum']}]** | 저고 `{b_stats['low_high']}` | 홀짝 `{b_stats['odd_even']}`")
        st.caption(f"💡 이전 9개 게임 미출현 번호({len(unused_numbers)}개): {unused_numbers}")

        # -------------------------------------------------------------
        # 구글 시트 자동 저장 로직 (총 10개 행)
        # -------------------------------------------------------------
        if conn:
            try:
                existing_data = conn.read(ttl=0)
                
                all_records = []
                now_str = pd.Timestamp.now(tz="Asia/Seoul").strftime("%Y-%m-%d %H:%M:%S")
                
                # 1) 시작 3게임
                for i, g in enumerate(base_games, 1):
                    s = calculate_stats(g)
                    all_records.append({
                        "생성시간": now_str, "구분": f"시작게임 {i}",
                        "N1": g[0], "N2": g[1], "N3": g[2], "N4": g[3], "N5": g[4], "N6": g[5],
                        "총합": s["sum"], "저고": s["low_high"], "홀짝": s["odd_even"]
                    })
                # 2) N=1 세트 (2게임)
                for label, g in zip(labels, set_n1):
                    s = calculate_stats(g)
                    all_records.append({
                        "생성시간": now_str, "구분": f"N=1 {label}",
                        "N1": g[0], "N2": g[1], "N3": g[2], "N4": g[3], "N5": g[4], "N6": g[5],
                        "총합": s["sum"], "저고": s["low_high"], "홀짝": s["odd_even"]
                    })
                # 3) N=2 세트 (2게임)
                for label, g in zip(labels, set_n2):
                    s = calculate_stats(g)
                    all_records.append({
                        "생성시간": now_str, "구분": f"N=2 {label}",
                        "N1": g[0], "N2": g[1], "N3": g[2], "N4": g[3], "N5": g[4], "N6": g[5],
                        "총합": s["sum"], "저고": s["low_high"], "홀짝": s["odd_even"]
                    })
                # 4) N=3 세트 (2게임)
                for label, g in zip(labels, set_n3):
                    s = calculate_stats(g)
                    all_records.append({
                        "생성시간": now_str, "구분": f"N=3 {label}",
                        "N1": g[0], "N2": g[1], "N3": g[2], "N4": g[3], "N5": g[4], "N6": g[5],
                        "총합": s["sum"], "저고": s["low_high"], "홀짝": s["odd_even"]
                    })
                # 5) 10번째 보너스 게임 (1게임)
                s_b = calculate_stats(bonus_game)
                all_records.append({
                    "생성시간": now_str, "구분": "미출현 보너스",
                    "N1": bonus_game[0], "N2": bonus_game[1], "N3": bonus_game[2], 
                    "N4": bonus_game[3], "N5": bonus_game[4], "N6": bonus_game[5],
                    "총합": s_b["sum"], "저고": s_b["low_high"], "홀짝": s_b["odd_even"]
                })
                
                new_df = pd.DataFrame(all_records)
                
                if not existing_data.empty:
                    updated_df = pd.concat([existing_data, new_df], ignore_index=True)
                else:
                    updated_df = new_df
                    
                conn.update(data=updated_df)
                st.success("✅ 총 10개 게임 생성이 완료되었으며, 구글 시트에 성공적으로 저장되었습니다!")
            except Exception as save_error:
                st.warning(f"⚠️ 게임은 생성되었으나 구글 시트 저장 중 오류가 발생했습니다: {save_error}")
        else:
            st.success("✅ 총 10개 게임 생성이 완료되었습니다.")
