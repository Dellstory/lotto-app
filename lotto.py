import streamlit as st
import random
from collections import Counter

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
# [핵심 로직] N값 세트 & 연쇄 소거 세트 생성
# =============================================================
def generate_chain_sojeo_sets(base_games, n_value):
    """
    기반 3게임에서 고정수(N개)를 추출하고, 
    1차/2차 연쇄 소거 및 황금 밸런스(100~170)를 적용하여 3게임 세트 생성
    """
    selected_set = []
    used_numbers_in_set = set()
    
    # 기반 게임 전체 번호 풀
    all_base_nums = [num for g in base_games for num in g]
    
    # 1. 메인 게임 생성 (N개 고정수 추출)
    fixed_nums = set()
    if n_value > 0 and len(all_base_nums) >= n_value:
        counts = Counter(all_base_nums)
        most_common = [num for num, _ in counts.most_common(n_value)]
        fixed_nums = set(most_common)
    
    # 메인 게임 (황금 밸런스 만족할 때까지 생성)
    while True:
        candidate_pool = list(set(range(1, 46)) - fixed_nums)
        needed = 6 - len(fixed_nums)
        main_game = sorted(list(fixed_nums) + random.sample(candidate_pool, needed))
        if calculate_stats(main_game)["is_balanced"]:
            selected_set.append(main_game)
            used_numbers_in_set.update(main_game)
            break
            
    # 2. 1차 소거 게임 (메인 게임에 사용된 번호 제외)
    while True:
        available_pool = list(set(range(1, 46)) - used_numbers_in_set)
        if len(available_pool) < 6:
            available_pool = list(set(range(1, 46)))
        sojeo1_game = sorted(random.sample(available_pool, 6))
        if calculate_stats(sojeo1_game)["is_balanced"]:
            selected_set.append(sojeo1_game)
            used_numbers_in_set.update(sojeo1_game)
            break

    # 3. 2차 소거 게임 (1차+2차 소거에 사용된 번호 제외)
    while True:
        available_pool = list(set(range(1, 46)) - used_numbers_in_set)
        if len(available_pool) < 6:
            available_pool = list(set(range(1, 46)))
        sojeo2_game = sorted(random.sample(available_pool, 6))
        if calculate_stats(sojeo2_game)["is_balanced"]:
            selected_set.append(sojeo2_game)
            break

    return selected_set

# =============================================================
# Streamlit UI 구현
# =============================================================
st.set_page_config(page_title="로또 황금밸런스 & 연쇄소거 번호 생성기", layout="wide")

st.title("🎲 로또 황금밸런스 & 연쇄소거 분석기")
st.caption("시작 3게임 입력 → 황금 밸런스(총합 100~170) 및 N=2,3 연쇄 소거 세트(총 9게임) 자동 도출")

st.sidebar.header("⚙️ 게임 방식 선택")
input_mode = st.sidebar.radio("시작 3게임 설정 방식", ["직접 입력하기", "랜덤 자동 생성"])

base_games = []

if input_mode == "직접 입력하기":
    st.subheader("📝 시작 3게임 직접 입력")
    st.info("💡 모바일 입력 팁: 숫자를 **한 칸 띄어쓰기(공백)**로 구분해서 입력해 주세요. (예: 3 12 18 27 34 41)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        g1_str = st.text_input("게임 1 번호", value="", placeholder="예: 3 12 18 27 34 41")
    with col2:
        g2_str = st.text_input("게임 2 번호", value="", placeholder="예: 5 14 22 30 37 44")
    with col3:
        g3_str = st.text_input("게임 3 번호", value="", placeholder="예: 1 8 19 25 33 40")
        
    # 공백(스페이스) 및 쉼표 구분 모두 지원하는 문자열 파싱
    def parse_input(input_str):
        if not input_str.strip():
            return []
        # 쉼표가 들어간 경우 공백으로 대체 후 분할
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

    # 입력 안내 및 검증 메세지
    if g1_str or g2_str or g3_str:
        if len(g1) == 6 and len(g2) == 6 and len(g3) == 6:
            base_games = [g1, g2, g3]
            st.success("✅ 3개 게임의 입력이 정상적으로 확인되었습니다.")
        else:
            st.warning("⚠️ 각 입력 칸마다 1~45 사이의 서로 다른 숫자 6개를 띄어쓰기로 입력해 주세요.")

else:
    st.subheader("🎲 황금 밸런스 자동 뽑기 3게임")
    st.write("버튼을 누르면 총합 100~170 사이의 자동 검증된 3게임이 생성됩니다.")

st.divider()

if st.button("🚀 연쇄 소거 9게임 세트 생성하기", type="primary"):
    if input_mode == "랜덤 자동 생성":
        base_games = [generate_balanced_random_game() for _ in range(3)]
        
    if len(base_games) == 3:
        # N=2 및 N=3 연쇄 소거 세트 생성
        set_n2 = generate_chain_sojeo_sets(base_games, n_value=2)
        set_n3 = generate_chain_sojeo_sets(base_games, n_value=3)

        # 1. 시작 3게임 출력
        st.subheader("1️⃣ 시작 게임 (기반 3게임)")
        for i, game in enumerate(base_games, 1):
            stats = calculate_stats(game)
            badge = "🟢 황금구간" if stats["is_balanced"] else "🟡 일반구간"
            st.markdown(f"**게임 {i}:** `{game}` | **[합계: {stats['sum']}]** ({badge}) | 저고 `{stats['low_high']}` | 홀짝 `{stats['odd_even']}`")

        st.divider()

        # 2. N=2 세트 출력
        st.subheader("2️⃣ N=2 세트 (메인 + 1차 소거 + 2차 소거)")
        labels = ["메인 게임 (N=2)", "1차 소거 게임", "2차 소거 게임"]
        for label, game in zip(labels, set_n2):
            stats = calculate_stats(game)
            st.markdown(f"**{label}:** `{game}` | 🟢 **[합계: {stats['sum']}]** | 저고 `{stats['low_high']}` | 홀짝 `{stats['odd_even']}`")

        st.divider()

        # 3. N=3 세트 출력
        st.subheader("3️⃣ N=3 세트 (메인 + 1차 소거 + 2차 소거)")
        for label, game in zip(labels, set_n3):
            stats = calculate_stats(game)
            st.markdown(f"**{label}:** `{game}` | 🟢 **[합계: {stats['sum']}]** | 저고 `{stats['low_high']}` | 홀짝 `{stats['odd_even']}`")

        st.success("✅ 총 9개 게임 생성이 완료되었습니다!")
    else:
        st.error("❌ 시작 3게임 입력이 제대로 완성되지 않았습니다. 번호를 확인해 주세요.")
