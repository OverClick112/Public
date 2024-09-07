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


def is_chrome_running(port=9226):
    """
    주어진 포트에서 Chrome이 디버그 모드로 실행 중인지 확인합니다. 목표 데이터가 캡챠 기능이 있는 사이트이기에 우회하기 위해 넣은 기능들
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'chrome.exe' and any(
                f'--remote-debugging-port={port}' in cmd for cmd in proc.info['cmdline']):
            return True
    return False


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
            sub_info = row.find('i', class_='subinfo').text.strip()
            followers = row.find('td', class_='text-center dt-type-numeric').text.strip()
            trend = row.find_all('td', class_='dt-type-numeric')[1].text.strip()
            price = row.find_all('td', class_='dt-type-numeric')[2].text.strip()
            release_date = row.find_all('td')[-1].text.strip()
            image_url = row.find('td', class_='applogo').find('img')['src'] # url을 정상적으로 가져오지 못하고 있는 문제의 코드
            video_url = row.find('td', class_='applogo').find('a')['href']

            games_data.append([image_url, video_url, game_name, sub_info, followers, trend, price, release_date])

        df = pd.DataFrame(games_data,
                          columns=['Image URL', 'Video URL', 'Game Name', 'Sub Info', 'Followers', 'Trend', 'Price',
                                   'Release Date'])

        df.insert(0, 'Rank', range(1, len(df) + 1))
        df['Rank'] = df['Rank'].astype(str)

        return df

    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None


def display_followed():
    st.header("Most Followed Upcoming Steam Games")

    df = fetch_followed_games_data()

    if df is not None:
        st.subheader("Most Followed Games")

        # 데이터프레임을 HTML로 변환하여 이미지와 동영상 링크 추가
        html = df.to_html(escape=False, formatters={
            'Image URL': lambda x: f'<img src="{x}" style="width:100px;"/>',
            'Video URL': lambda x: f'<a href="{x}" target="_blank">Video Link</a>'
        }, index=False)

        # HTML 출력
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.error("가장 많이 팔로우된 게임 데이터를 가져오지 못했습니다.")


if __name__ == "__main__":
    display_followed()