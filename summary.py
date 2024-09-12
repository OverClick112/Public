import streamlit as st
import subprocess
import psutil  # 프로세스 검사를 위한 모듈
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import altair as alt
import numpy as np
from summary2 import display_game_data

def is_chrome_running(port=9222):
    """
    주어진 포트에서 Chrome이 디버그 모드로 실행 중인지 확인합니다.
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'chrome.exe' and any(f'--remote-debugging-port={port}' in cmd for cmd in proc.info['cmdline']):
            return True
    return False

@st.cache_data(ttl=30)
def fetch_data():
    # Chrome 브라우저가 이미 실행 중인지 확인
    if not is_chrome_running():
        try:
            chrome_browser = subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe '
                                              r'--remote-debugging-port=9222 '
                                              r'--user-data-dir="C:\chromeCookie"')
        except Exception as e:
            st.error(f"Chrome 디버그 모드 실행 중 오류가 발생했습니다: {e}")
            return None, None, None, None

    option = Options()
    option.add_argument('--disable-blink-features=AutomationControlled')
    option.add_argument("--start-maximized")
    option.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)

    url = "https://steamdb.info/app/753/charts/#max"
    driver.get(url)

    try:
        wait = WebDriverWait(driver, 10)
        users_now = wait.until(
            EC.presence_of_element_located((By.XPATH, '//ul[@class="app-chart-numbers-big"]/li[2]/strong'))).text

        peak_24h = driver.find_element(By.XPATH, '//ul[@class="app-chart-numbers-big"]/li[3]/strong').text
        all_time_peak = driver.find_element(By.XPATH, '//ul[@class="app-chart-numbers-big"]/li[4]/strong').text

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        table_body = soup.find('tbody', class_='tabular-nums')
        rows = table_body.find_all('tr')

        breakdown_data = []
        for row in rows:
            columns = row.find_all('td')
            period = columns[0].text.strip()
            players = columns[1].text.strip()
            change = columns[2].text.strip()
            percentage_change = columns[3].text.strip()
            in_game_peak = columns[6].text.strip()
            breakdown_data.append([period, players, change, percentage_change, in_game_peak])

        df_original = pd.DataFrame(breakdown_data,
                                   columns=['Period', 'Players', 'Change', 'Percentage Change', 'In-Game Peak'])

        df_original['Period'] = df_original['Period'].replace('Last 30 days', '최종 30일')

        df_original['Period'] = df_original['Period'].replace({
            'January': '1월', 'February': '2월', 'March': '3월', 'April': '4월',
            'May': '5월', 'June': '6월', 'July': '7월', 'August': '8월',
            'September': '9월', 'October': '10월', 'November': '11월', 'December': '12월'
        }, regex=True)

        df_original['Period'] = df_original['Period'].apply(
            lambda x: f"{x.split()[1]}년 {x.split()[0]}" if x != '최종 30일' else x)

        df_original['Players'] = df_original['Players'].str.replace(',', '').astype(int)
        df_original['Percentage Change'] = df_original['Percentage Change'].replace('-', np.nan)
        df_original['Percentage Change'] = df_original['Percentage Change'].str.replace('%', '').astype(float)
        df_original['In-Game Peak'] = df_original['In-Game Peak'].replace('-', np.nan).str.replace(',', '').astype(float)

        return users_now, peak_24h, all_time_peak, df_original

    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None, None, None, None


def display_summary():
    st.header("SteamDB 요약 정보")

    users_now, peak_24h, all_time_peak, df_original = fetch_data()

    if df_original is None:
        st.error("데이터를 가져오지 못했습니다.")
        return

    st.write(f"**Users right now:** {users_now}")
    st.write(f"**24-hour peak:** {peak_24h}")
    st.write(f"**All-time peak:** {all_time_peak}")

    with st.expander("Monthly Players Breakdown Table"):
        st.table(df_original)

    df_reversed = df_original.iloc[::-1].reset_index(drop=True)

    st.subheader("Choose Time Period for Breakdown Chart")
    period_options = ["Last Year", "Last 3 Years", "Last 5 Years", "Last 10 Years", "All Data"]
    selected_period = st.select_slider("Select a period", options=period_options, value="All Data")

    def filter_data_by_period(df, period):
        if period == "Last Year":
            return df.tail(12)
        elif period == "Last 3 Years":
            return df.tail(36)
        elif period == "Last 5 Years":
            return df.tail(60)
        elif period == "Last 10 Years":
            return df.tail(120)
        else:
            return df

    df_filtered = filter_data_by_period(df_reversed, selected_period)

    total_percentage_change = df_filtered['Percentage Change'].sum()

    in_game_peak_valid = df_filtered['In-Game Peak'].dropna()
    if not in_game_peak_valid.empty and len(in_game_peak_valid) > 1:
        in_game_peak_start = in_game_peak_valid.iloc[0]
        in_game_peak_end = in_game_peak_valid.iloc[-1]
        in_game_peak_change_percentage = ((in_game_peak_end - in_game_peak_start) / in_game_peak_start) * 100 if in_game_peak_start != 0 else np.nan
    else:
        in_game_peak_change_percentage = np.nan

    percentage_change_label = "성장" if total_percentage_change > 0 else "하락" if total_percentage_change < 0 else ""
    in_game_peak_label = "성장" if in_game_peak_change_percentage > 0 else "하락" if in_game_peak_change_percentage < 0 else ""

    st.write(f"**Total Percentage Change for {selected_period}:** {total_percentage_change:.2f}% {percentage_change_label}")
    if not np.isnan(in_game_peak_change_percentage):
        st.write(f"**In-Game Peak Change for {selected_period}:** {in_game_peak_change_percentage:.2f}% {in_game_peak_label}")
    else:
        st.write(f"**In-Game Peak Change for {selected_period}:** 데이터 부족")

    st.subheader("Monthly Players Breakdown Chart")

    players_line = alt.Chart(df_filtered).mark_line(point=True, color='blue').encode(
        x=alt.X('Period', sort=None, title='Period'),
        y=alt.Y('Players', title='Players')
    )

    peak_line = alt.Chart(df_filtered).mark_line(point=True, color='red').encode(
        x=alt.X('Period', sort=None, title='Period'),
        y=alt.Y('In-Game Peak', title='In-Game Peak')
    )

    chart = alt.layer(players_line, peak_line).resolve_scale(
        y='shared'
    ).properties(
        width=800,
        height=400,
        title='Monthly Players Breakdown'
    )

    st.altair_chart(chart, use_container_width=True)

    display_game_data()

if __name__ == "__main__":
    display_summary()
