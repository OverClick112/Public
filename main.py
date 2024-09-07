import streamlit as st
from summary import display_summary
from users import display_users
from sales import display_sales
from followed import display_followed
from title_search import display_title_search

# 페이지 제목과 설명
st.set_page_config(page_title="SteamDB 정보", page_icon="🎮", layout="wide")
st.title("SteamDB 데이터베이스")
st.write("이 웹페이지는 SteamDB와 Steam에서 데이터를 크롤링하여 다양한 정보를 제공합니다.")

# 사이드바 구성
st.sidebar.title("메뉴")
option = st.sidebar.selectbox(
    "원하는 정보를 선택하세요",
    ("요약 정보", "유저 통계", "판매량 차트", "가장 많이 팔로우된 게임", "게임 타이틀 검색")
)

# 선택한 옵션에 따라 해당 데이터 보여주기
if option == "요약 정보":
    display_summary()
elif option == "유저 통계":
    display_users()
elif option == "판매량 차트":
    display_sales()
elif option == "가장 많이 팔로우된 게임":
    display_followed()
elif option == "게임 타이틀 검색":
    display_title_search()
