import streamlit as st

def display_title_search():
    st.header("SteamDB 유저 통계")

    # 여기에 Selenium 코드를 추가하여 데이터를 크롤링하고, 결과를 표시합니다.
    st.write("유저 통계 데이터를 여기에 표시합니다.")

    st.image("https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/1030300/capsule_231x87.jpg?t=1724799534")
    st.image("https://shared.akamai.steamstatic.com//store_item_assets/steam/apps/2358720/capsule_231x87.jpg?t=1724238313")

# main.py에서 호출될 때 이 함수를 실행
if __name__ == "__main__":
    display_title_search()
