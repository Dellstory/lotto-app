import streamlit as st
import random

# ================= ============================================
# [헬퍼 함수] 통계 필터 및 밸런스 검증
# ================= ============================================
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

# ================= ============================================
# [핵심 로직] N값 세트 & 연쇄 소거 세트 생성
# ================= ============================================
def generate_chain_sojeo_sets(base_games, n_value):
    """
    기존 베이스 게임들로부터 고정수(N개)를 확보하고, 
    남은 번호에서 1차/2차 연쇄 소거를 적용하여 균형 잡힌 3게임 세트를 생성
    """
    selected_set = []
    used_numbers_in_set = set()
    
    # 1. 메인 게임 생성 (N개 고정수 추출)
    # 기존 게임들에서 자주 겹치는 번호 또는 무작위 추출로 N개 고정수 확보
    all_base_nums = [num for g in base_games for num in g]
    # 고정수 추출
    fixed_nums = set()
    if n_value > 0 and len(all_base_nums) >= n_value:
        # 빈도수 기준 상위 N개 추출
        from collections import Counter
        counts = Counter(all_base_nums)
        most_common = [num for num, _ in counts.most_common(n_value)]
        fixed_nums = set(most_common)
    
    # 메인 게임 완성 (황금 밸런스 만족할 때까지 생성)
    while True:
        candidate_pool = list(set(range(1, 46)) - fixed_nums)
        needed = 6 - len(fixed_nums)
        main_game = sorted(list(fixed_nums) + random.sample(candidate_pool, needed))
        if calculate_stats(main_game)["is_balanced"]:
            selected_set.append(main_game)
            used_numbers_in_set.update(main_game)
            break
            
    # 2. 1차 소거 게임 (메인 게임에 사용된 번호 제외 후 생성)
    while True:
        available_pool = list(set(range(1, 46)) - used_numbers_in_set)
        if len(available_pool) < 6:
            available_pool = list(set(range(1, 46))) # 풀이 부족할 경우 전체로 리셋
        sojeo1_game = sorted(random.sample(available_pool, 6))
        if calculate_stats(sojeo1_game)["is_balanced"]:
            selected_set.append(sojeo1_game)
            used_numbers_in_set.update(sojeo1_game)
            break

    # 3. 2차 소거 게임 (1차+2차에 사용된 번호 제외 후 생성)
    while True:
        available_pool = list(set(range(1, 46)) - used_numbers_in_set)
        if len(available_pool) < 6:
            available_pool = list(set(range(1, 46))) # 풀이 부족할 경우 전체로 리셋
        sojeo2_game = sorted(random.sample(available_pool, 6))
        if calculate_stats(sojeo2_game)["is_balanced"]:
            selected_set.append(sojeo2_game)
            break

    return selected_set

# ================= ============================================
# Streamlit UI 구현
# ================= ============================================
st.set_page_config(page_title="로또 황금밸런스 & 연쇄소거 번호 생성기", layout="wide")

st.title("🎲 로또 황금밸런스 & 연쇄소거 생성기")
st.caption("총합 100~170 & 고저 균형 필터가 적용된 9,000원(9게임) 최적화 전략")

st.sidebar.header("⚙️ 전략 설정")
st.sidebar.markdown("""
* **랜덤 시작 게임:** 3게임 (3,000원)
* **N=2 소거 세트:** 3게임 (3,000원)
* **N=3 소거 세트:** 3게임 (3,000원)
---
**총 9게임 (9,000원)**
""")

if st.button("🚀 9게임 생성하기", type="primary"):
    # 1. 초기 황금 밸런스 랜덤 3게임 생성
    random_3_games = [generate_balanced_random_game() for _ in range(3)]
    
    # 2. N=2 및 N=3 연쇄 소거 세트 생성
    set_n2 = generate_chain_sojeo_sets(random_3_games, n_value=2)
    set_n3 = generate_chain_sojeo_sets(random_3_games, n_value=3)

    st.subheader("1️⃣ 시작 게임 (황금 밸런스 랜덤 3게임)")
    for i, game in enumerate(random_3_games, 1):
        stats = calculate_stats(game)
        st.markdown(f"**게임 {i}:** `{game}` | 🟢 **[합계: {stats['sum']}]** | 저고 `{stats['low_high']}` | 홀짝 `{stats['odd_even']}`")

    st.divider()

    st.subheader("2️⃣ N=2 세트 (메인 + 1차 소거 + 2차 소거)")
    labels = ["메인 게임 (N=2)", "1차 소거 게임", "2차 소거 게임"]
    for label, game in zip(labels, set_n2):
        stats = calculate_stats(game)
        st.markdown(f"**{label}:** `{game}` | 🟢 **[합계: {stats['sum']}]** | 저고 `{stats['low_high']}` | 홀짝 `{stats['odd_even']}`")

    st.divider()

    st.subheader("3️⃣ N=3 세트 (메인 + 1차 소거 + 2차 소거)")
    for label, game in zip(labels, set_n3):
        stats = calculate_stats(game)
        st.markdown(f"**{label}:** `{game}` | 🟢 **[합계: {stats['sum']}]** | 저고 `{stats['low_high']}` | 홀짝 `{stats['odd_even']}`")

    st.success("✅ 총 9개 게임이 모두 '황금 구간(총합 100~170 & 고저 균형)' 조건을 검증받아 성공적으로 생성되었습니다!")
