import streamlit as st
from summary import display_summary
from users import display_users
from sales import display_sales
from followed import display_followed
from title_search import display_title_search

# 페이지 제목과 설명 설정
st.set_page_config(page_title="SteamDB 정보", page_icon="🎮", layout="wide")

# 페이지 설명
st.title("SteamDB 데이터베이스")
st.write("이 웹페이지는 SteamDB와 Steam에서 데이터를 크롤링하여 다양한 정보를 제공합니다.")

# 사이드바 페이지 메뉴 설정
with st.sidebar:
    st.sidebar.title("Steam 데이터 메뉴")
    # Steam 데이터 메뉴 (기본적으로 모든 메뉴가 노출됨)
    steam_menu_option = st.radio(
        "",
        ["요약 정보", "유저 통계", "판매량 차트", "가장 많이 팔로우된 게임", "게임 타이틀 검색"]
    )

# 각 메뉴에 따른 페이지 이동
if steam_menu_option == "요약 정보":
    display_summary()
elif steam_menu_option == "유저 통계":
    display_users()
elif steam_menu_option == "판매량 차트":
    display_sales()
elif steam_menu_option == "가장 많이 팔로우된 게임":
    display_followed()
elif steam_menu_option == "게임 타이틀 검색":
    display_title_search()
