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
import time


def is_chrome_running(port=9224):
    """
    주어진 포트에서 Chrome이 디버그 모드로 실행 중인지 확인합니다.
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'chrome.exe' and any(
                f'--remote-debugging-port={port}' in cmd for cmd in proc.info['cmdline']):
            return True
    return False


@st.cache_data(ttl=30)
def fetch_users_data():
    # Chrome 브라우저가 이미 실행 중인지 확인
    if not is_chrome_running(port=9224):
        try:
            chrome_browser = subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe '
                                              r'--remote-debugging-port=9224 '
                                              r'--user-data-dir="C:\chromeCookie3"')  # 별도 사용자 데이터 디렉토리
        except Exception as e:
            st.error(f"Chrome 디버그 모드 실행 중 오류가 발생했습니다: {e}")
            return None

    option = Options()
    option.add_argument('--disable-blink-features=AutomationControlled')
    option.add_argument("--start-maximized")
    option.add_experimental_option("debuggerAddress", "127.0.0.1:9224")  # 다른 포트 사용

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)
        url = "https://steamdb.info/charts/"
        driver.get(url)

        # 데이터가 로드될 때까지 대기
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app')))

        games_data = []

        def extract_page_data():
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            games_rows = soup.find_all('tr', class_='app')

            page_data = []  # 페이지별 데이터
            for row in games_rows:
                rank = row.find('td').text.strip()
                game_name = row.find_all('td')[2].find('a').text.strip()
                current_players = row.find_all('td')[3]['data-sort']
                peak_today = row.find_all('td')[4]['data-sort']
                peak_all_time = row.find_all('td')[5]['data-sort']
                page_data.append([rank, game_name, current_players, peak_today, peak_all_time])

            return page_data

        # 첫 번째 페이지 데이터 가져오기
        games_data.extend(extract_page_data())

        # 페이지 넘김 버튼 클릭 및 데이터 추가 추출
        for i in range(2, 4):  # 2번과 3번 페이지
            try:
                # 페이지 로드 시간 확보
                time.sleep(2)

                # 다음 페이지 버튼 대기 및 클릭
                next_button = wait.until(EC.element_to_be_clickable((By.XPATH, f'//button[@data-dt-idx="{i - 1}"]')))
                driver.execute_script("arguments[0].click();", next_button)

                # 페이지가 완전히 로드될 때까지 대기
                wait.until(EC.staleness_of(next_button))  # 이전 버튼이 더 이상 존재하지 않음을 확인하여 페이지 전환이 완료되었는지 확인
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app')))  # 새로운 데이터가 로드되었는지 확인

                # 새로운 페이지 데이터 가져오기
                page_data = extract_page_data()
                games_data.extend(page_data)  # 기존 데이터에 추가

            except Exception as e:
                st.error(f"페이지 {i} 버튼 클릭 중 오류가 발생했습니다: {e}")
                break

        # DataFrame 생성
        df = pd.DataFrame(games_data, columns=['순위', '타이틀', '현재 동접', '일일 최고 동접', '역대 최고 동접'])

        return df

    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None


def display_users():
    st.header("SteamDB 유저 통계")

    df = fetch_users_data()

    if df is not None:
        st.subheader("Most Played Games")
        st.dataframe(df, use_container_width=True, height=3580, hide_index=True)  # 인덱스를 숨김
    else:
        st.error("유저 데이터를 가져오지 못했습니다.")


if __name__ == "__main__":
    display_users()
