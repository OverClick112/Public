import streamlit as st
from summary import display_summary
from users import display_users
from sales import display_sales
from followed import display_followed
from title_search import display_title_search
from summary3 import display_release_stats  # 새로 추가할 페이지를 위한 임포트

# 페이지 제목과 설명 설정
st.set_page_config(page_title="LYJ_PP", page_icon="🎮", layout="wide")

# 사이드바 페이지 메뉴 설정
with st.sidebar:
    st.sidebar.title("Steam 데이터 메뉴")

    # 모든 메뉴를 하나의 radio로 묶고, 부제목을 시각적으로 삽입
    menu_option = st.radio(
        "Steam 데이터 메뉴2",
        [
            "요약 정보",
            "유저 통계",
            "판매량 차트",
            "가장 많이 팔로우된 게임",
            "출시 게임 통계",
            "게임 타이틀 검색"
        ]
    )

# 각 메뉴에 따른 페이지 이동
if menu_option == "요약 정보":
    display_summary()
elif menu_option == "유저 통계":
    display_users()
elif menu_option == "판매량 차트":
    display_sales()
elif menu_option == "가장 많이 팔로우된 게임":
    display_followed()
elif menu_option == "출시 게임 통계":
    display_release_stats()
elif menu_option == "게임 타이틀 검색":
    display_title_search()