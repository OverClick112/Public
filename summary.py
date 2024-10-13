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
from summary2 import fetch_game_data
from summary3 import fetch_release_data
from sales import fetch_sales_data
from followed import fetch_followed_games_data

def is_chrome_running(port=9222):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'chrome.exe' and any(f'--remote-debugging-port={port}' in cmd for cmd in proc.info['cmdline']):
            return True
    return False

@st.cache_data(ttl=30)
def fetch_data():
    if not is_chrome_running(port=9222):
        try:
            subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe '
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
    selected_period = st.select_slider("Select a period", options=period_options, value="Last 10 Years")

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

    # Fetch sales, followed, most played, and trending data
    sales_df = fetch_sales_data().head(15).drop(columns=['Numeric Price', 'Numeric Change'])
    followed_df = fetch_followed_games_data().head(15)
    most_played_df, trending_df = fetch_game_data()

    # Format Follows and 7d Gain columns in followed_df
    followed_df['Follows'] = followed_df['Follows'].apply(lambda x: f"{x:,}")
    followed_df['7d Gain'] = followed_df['7d Gain'].apply(lambda x: f"+ {x:,}")

    # Fetch yearly game release data from summary3.py
    release_df = fetch_release_data()

    # Style for tables
    st.markdown("""
        <style>
        .mystyle {
            font-size: 12px;
            font-family: 'Arial';
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            border: 3px solid #000;
        }
        .mystyle th {
            background-color: #DCDCDC;
            color: Black;
            text-align: center;
            padding: 8px;
            border: 2px solid #000;
        }
        .mystyle td {
            text-align: center;
            padding: 6px;
            border: 1px solid #000;
        }
        </style>
        """, unsafe_allow_html=True)

    # Display game-related data in structured format
    st.subheader("Most Played Games & Top 15 Selling Games")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Most Played Games")
        most_played_html = most_played_df.to_html(escape=False, formatters={
            'Image URL': lambda x: f'<img src="{x}" style="width:80px;"/>',
            'Detail URL': lambda x: f'<a href="{x}" target="_blank">Detail Link</a>'
        }, index=False, classes='mystyle')
        st.markdown(most_played_html, unsafe_allow_html=True)

    with col2:
        st.subheader("Top 15 Selling Games")
        sales_html = sales_df.to_html(escape=False, formatters={
            'Image URL': lambda x: f'<img src="{x}" style="width:80px;"/>',
            'Store Link': lambda x: f'<a href="{x}" target="_blank">Store Link</a>'
        }, index=False, classes='mystyle')
        st.markdown(sales_html, unsafe_allow_html=True)

    st.subheader("Trending Games & Top 15 Followed Games")
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Trending Games")
        trending_html = trending_df.to_html(escape=False, formatters={
            'Image URL': lambda x: f'<img src="{x}" style="width:80px;"/>',
            'Detail URL': lambda x: f'<a href="{x}" target="_blank">Detail Link</a>'
        }, index=False, classes='mystyle')
        st.markdown(trending_html, unsafe_allow_html=True)

    with col4:
        st.subheader("Top 15 Followed Games")
        followed_html = followed_df.to_html(escape=False, formatters={
            'Image URL': lambda x: f'<img src="{x}" style="width:80px;"/>',
            'Video URL': lambda x: f'<a href="{x}" target="_blank">Video Link</a>'
        }, index=False, classes='mystyle')
        st.markdown(followed_html, unsafe_allow_html=True)

    # Display yearly game release data
    release_df = fetch_release_data()

    st.subheader("Yearly Game Release Data")
    if release_df is not None:
        # Format Games Released column with commas
        release_df_display = release_df.copy()
        release_df_display['Games Released'] = release_df_display['Games Released'].apply(lambda x: f"{x:,}")

        release_df_display['Year'] = release_df_display['Year'].apply(lambda x: f"{x}년")

        with st.expander("Yearly Game Release Data (Click to Expand)"):
            st.table(release_df_display)

        release_df['Year'] = release_df['Year'].apply(lambda x: f"{x}년")

        # Yearly release bar chart using the original DataFrame without formatting
        chart = alt.Chart(release_df).mark_bar().encode(
            x=alt.X('Year:O', title='Year', sort=alt.SortField(field='Year', order='ascending')),
            y=alt.Y('Games Released:Q', title='Games Released', axis=alt.Axis(format=',d')),
        ).properties(
            width=800,
            height=400,
            title="Yearly Steam Game Releases"
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.error("Yearly game release data could not be loaded.")

if __name__ == "__main__":
    display_summary()
