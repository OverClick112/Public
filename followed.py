import streamlit as st
import subprocess
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import pandas as pd
import re
from io import BytesIO

def is_chrome_running(port=9226):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'chrome.exe' and any(
                f'--remote-debugging-port={port}' in cmd for cmd in proc.info['cmdline']):
            return True
    return False

def translate_release_date(date_str):
    if date_str == "TBA":
        return "추후 공지"
    elif date_str.lower() == "soon":
        return "출시 임박"
    elif re.match(r'^[A-Za-z]{3} \d{4}$', date_str):
        month_translation = {
            "Jan": "1월", "Feb": "2월", "Mar": "3월", "Apr": "4월",
            "May": "5월", "Jun": "6월", "Jul": "7월", "Aug": "8월",
            "Sep": "9월", "Oct": "10월", "Nov": "11월", "Dec": "12월"
        }
        month, year = date_str.split()
        return f"{year}년 {month_translation.get(month, month)}"
    elif re.match(r'^Q[1-4] \d{4}$', date_str):
        quarter_translation = {
            "Q1": "1분기", "Q2": "2분기", "Q3": "3분기", "Q4": "4분기"
        }
        quarter, year = date_str.split()
        return f"{year}년 {quarter_translation.get(quarter, quarter)}"
    elif re.match(r'^\d{4}$', date_str):
        return f"{date_str}년 중 출시"
    return date_str

def update_release_date(df):
    df['출시 일정'] = df['출시 일정'].apply(lambda x: translate_release_date(x))
    return df

@st.cache_data(ttl=30)
def fetch_followed_games_data():
    if not is_chrome_running(port=9226):
        try:
            subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe '
                             r'--remote-debugging-port=9226 '
                             r'--user-data-dir="C:\chromeCookie5"')
        except Exception as e:
            st.error(f"Chrome 디버그 모드 실행 중 오류가 발생했습니다: {e}")
            return None

    option = Options()
    option.add_argument('--disable-blink-features=AutomationControlled')
    option.add_argument("--start-maximized")
    option.add_experimental_option("debuggerAddress", "127.0.0.1:9226")

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)
        url = "https://steamdb.info/upcoming/mostfollowed/"
        driver.get(url)

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app')))

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        games_data = []
        games_rows = soup.find_all('tr', class_='app')

        for row in games_rows:
            game_name = row.find('a', class_='b').text.strip()

            try:
                price_elem = row.find_all('td', class_='dt-type-numeric')[2]
                price = price_elem.text.strip() if price_elem.text.strip() else '—'
            except IndexError:
                price = '—'

            try:
                release_date_elem = row.find_all('td', class_='dt-type-numeric')[4]
                release_date = release_date_elem.text.strip() if release_date_elem else 'N/A'
            except IndexError:
                release_date = 'N/A'

            try:
                follows_elem = row.find_all('td', class_='dt-type-numeric')[5]
                follows = follows_elem.text.strip().replace(',', '') if follows_elem else 'N/A'
            except IndexError:
                follows = 'N/A'

            try:
                gain_elem = row.find_all('td', class_='green dt-type-numeric')[0]
                gain = gain_elem.text.strip().replace(',', '') if gain_elem else '+0'
            except IndexError:
                gain = '+0'

            app_id = row['data-appid']
            image_url = f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{app_id}/capsule_231x87.jpg"
            formatted_game_name = game_name.replace(' ', '_')
            video_url = f"https://store.steampowered.com/app/{app_id}/{formatted_game_name}/?curator_clanid=4777282"

            if game_name == 'Deadlock':
                image_url = "https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/1422450/cb84593a7056ddc04337c77295b33ce8d95b485e/capsule_231x87.jpg"

            games_data.append([image_url, video_url, game_name, price, release_date, follows, gain])

        df = pd.DataFrame(games_data,
                          columns=['이미지', '스토어 링크', '타이틀', '가격', '출시 일정', '팔로우 수', '팔로우 7d 변동'])

        df.insert(0, '순위', range(1, len(df) + 1))

        df['팔로우 수'] = pd.to_numeric(df['팔로우 수'].replace('N/A', None), errors='coerce')
        df['팔로우 7d 변동'] = pd.to_numeric(df['팔로우 7d 변동'].replace('+', '').replace(',', ''), errors='coerce')

        df = update_release_date(df)

        return df

    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None

def custom_sort_key(date_str, reverse=False):
    if isinstance(date_str, str):
        if '월' in date_str:
            year = int(re.search(r'(\d{4})', date_str).group())
            month = int(re.search(r'(\d{1,2})월', date_str).group(1))
            return (year, month) if not reverse else (year, -month)
        elif '분기' in date_str:
            year = int(re.search(r'(\d{4})', date_str).group())
            quarter = int(re.search(r'(\d)분기', date_str).group(1))
            return (year, quarter * 3) if not reverse else (year, 12 - quarter * 3)
        elif '중 출시' in date_str:
            year = int(re.search(r'(\d{4})', date_str).group())
            return (year, 13) if not reverse else (year, -1)
        elif date_str in ['TBA', 'Soon', '추후 공지', '출시 임박']:
            return (9999, 12) if not reverse else (0, 0)
    return (9999, 12) if not reverse else (0, 0)

def display_followed():
    st.header("Most Followed Upcoming Steam Games")

    df = fetch_followed_games_data()

    if df is not None:
        st.subheader("Most Followed Games")

        with st.sidebar:
            st.header("필터 옵션")
            rank_filter = st.slider("순위", min_value=int(df['순위'].min()), max_value=int(df['순위'].max()), value=(1, 100))
            price_filter_option = st.selectbox("가격 정렬", ["필터 없음", "가격 오름차순", "가격 내림차순", "Free"], index=0)
            release_date_filter_option = st.selectbox("출시 일정 필터", ["필터 없음", "출시일 확정 빠른 순서", "출시일 확정 느린 순서", "출시 임박", "추후 공지"], index=0)
            follows_filter = st.slider("팔로우 수", min_value=int(df['팔로우 수'].min()), max_value=int(df['팔로우 수'].max()), value=(int(df['팔로우 수'].min()), int(df['팔로우 수'].max())))
            gain_filter = st.slider("팔로우 7d 변동", min_value=int(df['팔로우 7d 변동'].min()), max_value=int(df['팔로우 7d 변동'].max()), value=(int(df['팔로우 7d 변동'].min()), int(df['팔로우 7d 변동'].max())))

        # 필터 적용
        filtered_df = df[(df['순위'].astype(int) >= rank_filter[0]) & (df['순위'].astype(int) <= rank_filter[1])]

        # 가격 필터 적용
        if price_filter_option == "가격 오름차순":
            filtered_df = filtered_df[filtered_df['가격'] != '—']
            filtered_df['Numeric Price'] = pd.to_numeric(filtered_df['가격'].str.replace('₩', '').str.replace(',', ''), errors='coerce')
            filtered_df = filtered_df.sort_values(by='Numeric Price', ascending=True).drop(columns=['Numeric Price'])
        elif price_filter_option == "가격 내림차순":
            filtered_df = filtered_df[filtered_df['가격'] != '—']
            filtered_df['Numeric Price'] = pd.to_numeric(filtered_df['가격'].str.replace('₩', '').str.replace(',', ''), errors='coerce')
            filtered_df = filtered_df.sort_values(by='Numeric Price', ascending=False).drop(columns=['Numeric Price'])
        elif price_filter_option == "Free":
            filtered_df = filtered_df[filtered_df['가격'] == "Free"]

        # 출시 일정 필터 적용
        if release_date_filter_option == "출시일 확정 빠른 순서":
            filtered_df = filtered_df[~filtered_df['출시 일정'].isin(['출시 임박', '추후 공지'])]
            filtered_df = filtered_df.sort_values(by='출시 일정',
                                                  key=lambda x: x.map(lambda y: custom_sort_key(y, reverse=False)),
                                                  ascending=True)
        elif release_date_filter_option == "출시일 확정 느린 순서":
            filtered_df = filtered_df[~filtered_df['출시 일정'].isin(['출시 임박', '추후 공지'])]
            filtered_df = filtered_df.sort_values(by='출시 일정',
                                                  key=lambda x: x.map(lambda y: custom_sort_key(y, reverse=True)),
                                                  ascending=False)
        elif release_date_filter_option == "출시 임박":
            filtered_df = filtered_df[filtered_df['출시 일정'] == "출시 임박"]
        elif release_date_filter_option == "추후 공지":
            filtered_df = filtered_df[filtered_df['출시 일정'] == "추후 공지"]

        # 팔로우 수, 7d 변동 필터 적용
        filtered_df = filtered_df[(filtered_df['팔로우 수'] >= follows_filter[0]) & (filtered_df['팔로우 수'] <= follows_filter[1])]
        filtered_df = filtered_df[(filtered_df['팔로우 7d 변동'] >= gain_filter[0]) & (filtered_df['팔로우 7d 변동'] <= gain_filter[1])]

        # 포맷팅: 팔로우 수와 7d 변동 데이터에 쉼표 추가
        filtered_df['팔로우 수'] = filtered_df['팔로우 수'].apply(lambda x: f"{x:,}")
        filtered_df['팔로우 7d 변동'] = filtered_df['팔로우 7d 변동'].apply(lambda x: f"+ {x:,}")

        # HTML 스타일과 함께 출력
        html = filtered_df.to_html(escape=False, formatters={
            '이미지': lambda x: f'<img src="{x}" style="width:100px;"/>',
            '스토어 링크': lambda x: f'<a href="{x}" target="_blank">Store</a>'
        }, index=False, classes='mystyle')

        st.markdown("""
        <style>
        .mystyle {
            font-size: 14px;
            font-family: 'Arial';
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            border: 2px solid #000;
        }
        .mystyle th {
            background-color: #DCDCDC;
            color: Black;
            text-align: center;
            padding: 10px;
            border: 2px solid #000;
        }
        .mystyle td {
            text-align: center;
            padding: 8px;
            border: 1px solid #000;
        }
        .mystyle td:nth-child(4) {
            text-align: left;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(html, unsafe_allow_html=True)

        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Followed Games')
            processed_data = output.getvalue()
            return processed_data

        excel_data = convert_df_to_excel(filtered_df)
        st.download_button(
            label="엑셀로 다운로드",
            data=excel_data,
            file_name='Followed_Games.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    else:
        st.error("가장 많이 팔로우된 게임 데이터를 가져오지 못했습니다.")

if __name__ == "__main__":
    display_followed()
