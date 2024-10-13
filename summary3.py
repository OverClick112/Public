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
import altair as alt

def is_chrome_running(port=9227):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'chrome.exe' and any(f'--remote-debugging-port={port}' in cmd for cmd in proc.info['cmdline']):
            return True
    return False

@st.cache_data(ttl=30)
def fetch_release_data():
    if not is_chrome_running(port=9227):
        try:
            subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe '
                             r'--remote-debugging-port=9227 '
                             r'--user-data-dir="C:\chromeCookie6"')
        except Exception as e:
            print(f"Chrome 디버그 모드 실행 중 오류가 발생했습니다: {e}")  # 디버그 용도로만 사용
            return None

    option = Options()
    option.add_argument('--disable-blink-features=AutomationControlled')
    option.add_argument("--start-maximized")
    option.add_experimental_option("debuggerAddress", "127.0.0.1:9227")

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)
        url = "https://steamdb.info/stats/releases/"
        driver.get(url)

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul')))

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        release_data = []
        rows = soup.select('ul li')

        for row in rows:
            try:
                year_elem = row.find('b')
                count_elem = row.find_all('b')

                if year_elem and len(count_elem) >= 2:
                    year_text = year_elem.text.strip()
                    count_text = count_elem[1].text.strip()

                    games_released = int(year_text.replace('년', ''))
                    year = int(count_text.replace('개의', '').replace(',', ''))
                    release_data.append([games_released, year])
            except (ValueError, IndexError, AttributeError) as e:
                print(f"Error processing row: {e}")  # 디버그 용도로만 사용
                continue

        if not release_data:
            print("No release data found.")  # 디버그 용도로만 사용
            return None

        df = pd.DataFrame(release_data, columns=['Games Released', 'Year'])
        return df

    except Exception as e:
        print(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")  # 디버그 용도로만 사용
        return None

def display_release_chart():
    st.header("Steam Yearly Game Releases")

    df = fetch_release_data()
    if df is not None:
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X('Year:O', title='Year'),
            y=alt.Y('Games Released:Q', title='Games Released')
        ).properties(
            width=800,
            height=400,
            title="Yearly Steam Game Releases"
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.error("게임 출시 데이터를 가져오지 못했습니다.")  # 사용자에게만 노출

if __name__ == "__main__":
    display_release_chart()
