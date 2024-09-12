import streamlit as st
import subprocess
import psutil  # 프로세스 검사를 위한 모듈
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import pandas as pd


def is_chrome_running(port=9223):
    """
    주어진 포트에서 Chrome이 디버그 모드로 실행 중인지 확인합니다.
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'chrome.exe' and any(
                f'--remote-debugging-port={port}' in cmd for cmd in proc.info['cmdline']):
            return True
    return False


@st.cache_data(ttl=30)
def fetch_game_data():
    # Chrome 브라우저가 이미 실행 중인지 확인
    if not is_chrome_running():
        try:
            chrome_browser = subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe '
                                              r'--remote-debugging-port=9223 '  # 다른 포트 사용
                                              r'--user-data-dir="C:\chromeCookie2"')  # 별도 프로파일
        except Exception as e:
            st.error(f"Chrome 디버그 모드 실행 중 오류가 발생했습니다: {e}")
            return None

    # Selenium 설정
    option = Options()
    option.add_argument('--disable-blink-features=AutomationControlled')
    option.add_argument("--start-maximized")
    option.add_experimental_option("debuggerAddress", "127.0.0.1:9223")  # 다른 포트 사용

    try:
        # ChromeDriver 설정 및 웹사이트로 이동
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)
        url = "https://steamdb.info/"
        driver.get(url)

        # 데이터가 로드될 때까지 대기
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
                game_name = row.select_one('a.css-truncate').text.strip()

                # 'td.text-center.tabular-nums' 클래스를 가진 모든 td 태그를 찾음
                player_data_cells = row.select('td.text-center.tabular-nums')

                if len(player_data_cells) >= 2:
                    current_players = player_data_cells[0].text.strip()
                    peak_players = player_data_cells[1].text.strip()
                else:
                    current_players = "N/A"
                    peak_players = "N/A"

                most_played_data.append([game_name, current_players, peak_players])
            except Exception as e:
                # 각 행에서 오류 발생 시 메시지 출력 및 무시
                st.write(f"Error processing row: {e}")
                continue

        # DataFrame 생성
        most_played_df = pd.DataFrame(most_played_data, columns=['Game', 'Current Players', 'Peak Players'])

        # 인덱스를 1부터 시작하도록 설정
        most_played_df.index = range(1, len(most_played_df) + 1)

        return most_played_df

    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None


def display_game_data():
    st.header("SteamDB Most Played Games 데이터")

    most_played_df = fetch_game_data()

    if most_played_df is not None:
        st.subheader("Most Played Games")
        st.table(most_played_df)
    else:
        st.error("게임 데이터를 가져오지 못했습니다.")


if __name__ == "__main__":
    display_game_data()
