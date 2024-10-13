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

def is_chrome_running(port=9223):
    """
    주어진 포트에서 Chrome이 디버그 모드로 실행 중인지 확인합니다.
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'chrome.exe' and any(
                f'--remote-debugging-port={port}' in cmd for cmd in proc.info['cmdline']):
            return True
    return False

def format_game_name_for_url(game_name):
    formatted_name = re.sub(r'[^\w\s]', '', game_name)
    formatted_name = formatted_name.replace(' ', '_')
    return formatted_name

@st.cache_data(ttl=30)
def fetch_game_data():
    # Chrome 브라우저가 이미 실행 중인지 확인
    if not is_chrome_running(port=9223):
        try:
            subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe '
                             r'--remote-debugging-port=9223 '
                             r'--user-data-dir="C:\chromeCookie2"')
        except Exception as e:
            st.error(f"Chrome 디버그 모드 실행 중 오류가 발생했습니다: {e}")
            return None, None

    # Selenium 설정
    option = Options()
    option.add_argument('--disable-blink-features=AutomationControlled')
    option.add_argument("--start-maximized")
    option.add_experimental_option("debuggerAddress", "127.0.0.1:9223")

    try:
        # ChromeDriver 설정 및 웹사이트로 이동
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)
        url = "https://steamdb.info/"
        driver.get(url)

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody')))  # 'Most Played Games' 테이블 로드 대기

        # 페이지 소스를 가져와서 BeautifulSoup으로 파싱
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # 'Most Played Games' 데이터 추출 (상위 15개만 가져오기)
        most_played_rows = soup.select('tbody tr.app')[:15]  # 첫 15개의 tr 태그만 선택
        most_played_data = []

        for row in most_played_rows:
            try:
                # 게임 이름
                game_name = row.select_one('a.css-truncate').text.strip()

                # 현재 플레이어 수 및 최대 플레이어 수
                player_data_cells = row.select('td.text-center.tabular-nums')
                current_players = player_data_cells[0].text.strip() if len(player_data_cells) >= 2 else "N/A"
                peak_players = player_data_cells[1].text.strip() if len(player_data_cells) >= 2 else "N/A"

                # 이미지 URL 및 앱 링크
                app_id = row['data-appid']
                image_elem = row.find('img')
                image_url = f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{app_id}/{image_elem['data-capsule']}" if image_elem and image_elem.has_attr('data-capsule') else ''
                formatted_game_name = format_game_name_for_url(game_name)
                detail_url = f"https://store.steampowered.com/app/{app_id}/{formatted_game_name}/?curator_clanid=4777282"

                # "Source SDK Base 2007"이 포함된 경우 예외 처리
                if "Source SDK Base 2007" in game_name:
                    image_url = "https://steamdb.info/static/img/capsules/218.jpg"

                most_played_data.append([image_url, detail_url, game_name, current_players, peak_players])
            except Exception as e:
                # 각 행에서 오류 발생 시 메시지 출력 및 무시
                st.write(f"Error processing row: {e}")
                continue

        # DataFrame 생성
        most_played_df = pd.DataFrame(most_played_data, columns=['Image URL', 'Detail URL', 'Game', 'Current Players', 'Peak Players'])
        most_played_df.insert(0, 'Rank', range(1, len(most_played_df) + 1))  # Rank 열 추가

        # 'Trending Games' 데이터 추출 (상위 15개만 가져오기)
        trending_table = soup.find_all('table', {'class': 'table-products table-hover'})[1]  # 두 번째 테이블
        trending_rows = trending_table.select('tbody tr.app')[:15]
        trending_data = []

        for row in trending_rows:
            try:
                # 게임 이름
                game_name = row.select_one('a.css-truncate').text.strip()

                # 플레이어 수 (현재 플레이어 수)
                player_now = row.select_one('td.text-center.tabular-nums').text.strip() if row.select_one('td.text-center.tabular-nums') else "N/A"

                # 이미지 URL 및 앱 링크
                app_id = row['data-appid']
                image_elem = row.find('img')
                image_url = f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{app_id}/{image_elem['data-capsule']}" if image_elem and image_elem.has_attr('data-capsule') else ''
                formatted_game_name = format_game_name_for_url(game_name)
                detail_url = f"https://store.steampowered.com/app/{app_id}/{formatted_game_name}/?curator_clanid=4777282"

                trending_data.append([image_url, detail_url, game_name, player_now])
            except Exception as e:
                # 각 행에서 오류 발생 시 메시지 출력 및 무시
                st.write(f"Error processing row: {e}")
                continue

        # DataFrame 생성
        trending_df = pd.DataFrame(trending_data, columns=['Image URL', 'Detail URL', 'Game', 'Players Now'])
        trending_df.insert(0, 'Rank', range(1, len(trending_df) + 1))  # Rank 열 추가

        return most_played_df, trending_df

    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None, None


def display_game_data():
    st.header("SteamDB Most Played Games & Trending Games 데이터")

    most_played_df, trending_df = fetch_game_data()

    if most_played_df is not None:
        st.subheader("Most Played Games")

        # HTML 스타일 적용 및 이미지 및 상세 링크 추가
        html = most_played_df.to_html(escape=False, formatters={
            'Image URL': lambda x: f'<img src="{x}" style="width:100px;"/>',
            'Detail URL': lambda x: f'<a href="{x}" target="_blank">Detail Link</a>'
        }, index=False)

        st.markdown("""
        <style>
        table {
            font-size: 14px;
            font-family: Arial;
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            text-align: center;
            padding: 8px;
            border: 1px solid #000;
        }
        th {
            background-color: #DCDCDC;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(html, unsafe_allow_html=True)

    else:
        st.error("Most Played Games 데이터를 가져오지 못했습니다.")

    if trending_df is not None:
        st.subheader("Trending Games")

        # HTML 스타일 적용 및 이미지 및 상세 링크 추가
        html = trending_df.to_html(escape=False, formatters={
            'Image URL': lambda x: f'<img src="{x}" style="width:100px;"/>',
            'Detail URL': lambda x: f'<a href="{x}" target="_blank">Detail Link</a>'
        }, index=False)

        st.markdown(html, unsafe_allow_html=True)

    else:
        st.error("Trending Games 데이터를 가져오지 못했습니다.")


if __name__ == "__main__":
    display_game_data()
