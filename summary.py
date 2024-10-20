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
    st.header("Steam 주요 지표 요약")
    st.markdown("###### _- Steam 플랫폼의 주요 정보를 요약하여 모아놓은 페이지 입니다._")

    st.markdown("<br><br>", unsafe_allow_html=True)  # 줄바꿈

    st.markdown("#### **▶ Steam 플랫폼 현황 요약**")

    users_now, peak_24h, all_time_peak, df_original = fetch_data()

    if df_original is None:
        st.error("데이터를 가져오지 못했습니다.")
        return

    # 수평으로 유저 정보 표시
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="현재 유저 수", value=f"{users_now}")
    with col2:
        st.metric(label="24시간 최대 유저 수", value=f"{peak_24h}")
    with col3:
        st.metric(label="모든 기간 최대 유저 수", value=f"{all_time_peak}")

    # 텍스트 크기를 작게 설정하기 위해 스타일 적용
    st.markdown(
        """
        <style>
        .css-1r6slb0.e16nr0p30 {
            font-size: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 데이터 역순으로 변환
    df_reversed = df_original.iloc[::-1].reset_index(drop=True)

    st.markdown("<br>", unsafe_allow_html=True)  # 줄바꿈

    # 차트 표시
    st.markdown("#### **- 월별 유저 통계**")

    def filter_data_by_period(df, period):
        if period == "최근 1년":
            return df.tail(12)
        elif period == "지난 3년":
            return df.tail(36)
        elif period == "지난 5년":
            return df.tail(60)
        elif period == "지난 10년":
            return df.tail(120)
        else:
            return df

    # 레이아웃 설정: 슬라이더와 통계 정보를 한 행에 배치
    col1, _, col2 = st.columns([1, 0.1, 1])

    with col1:
        period_options = ["최근 1년", "지난 3년", "지난 5년", "지난 10년", "모든 기간"]
        selected_period = st.select_slider("차트의 기간을 선택", options=period_options, value="지난 10년")

    # 슬라이더 값에 따라 데이터 필터링
    df_filtered = filter_data_by_period(df_reversed, selected_period)

    # 통계 정보 계산
    total_percentage_change = df_filtered['Percentage Change'].sum()

    in_game_peak_valid = df_filtered['In-Game Peak'].dropna()
    if not in_game_peak_valid.empty and len(in_game_peak_valid) > 1:
        in_game_peak_start = in_game_peak_valid.iloc[0]
        in_game_peak_end = in_game_peak_valid.iloc[-1]
        in_game_peak_change_percentage = ((in_game_peak_end - in_game_peak_start) / in_game_peak_start) * 100 if in_game_peak_start != 0 else np.nan
    else:
        in_game_peak_change_percentage = np.nan

    # 수평으로 통계 정보를 표시
    with col2:
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric(
                label=f"일일 스팀 동시 접속자 수 {selected_period}",
                value=f"{total_percentage_change:.2f}%",
                delta="성장" if total_percentage_change > 0 else "하락"
            )
        with metric_col2:
            if not np.isnan(in_game_peak_change_percentage):
                st.metric(
                    label=f"일일 스팀 인게임 동시 접속자 수 {selected_period}",
                    value=f"{in_game_peak_change_percentage:.2f}%",
                    delta="성장" if in_game_peak_change_percentage > 0 else "하락"
                )
            else:
                st.write("In-Game Peak Change 데이터 부족")

    players_line = alt.Chart(df_filtered).mark_line(point=True).encode(
        x=alt.X('Period', sort=None, title='기간'),
        y=alt.Y('Players', title='동시 접속자'),
        color=alt.value('blue'),  # 라인 색상을 파란색으로 지정
        tooltip=['Period', 'Players']  # 툴팁 추가
    )

    # In-Game Peak 라인과 포인트
    peak_line = alt.Chart(df_filtered).mark_line(point=True).encode(
        x=alt.X('Period', sort=None, title='기간'),
        y=alt.Y('In-Game Peak', title='인게임 피크'),
        color=alt.value('purple'),  # 라인 색상을 보라색으로 지정
        tooltip=['Period', 'In-Game Peak']  # 툴팁 추가
    )

    peak_points = alt.Chart(df_filtered).mark_point().encode(
        x=alt.X('Period', sort=None, title='기간'),
        y=alt.Y('In-Game Peak'),
        color=alt.value('purple'),
        tooltip=['Period', 'In-Game Peak']  # 툴팁 추가
    )

    # 데이터를 범례에 맞게 변환
    legend_data = df_filtered.melt(id_vars=['Period'], value_vars=['Players', 'In-Game Peak'], var_name='Type',
                                   value_name='Value')

    # 범례를 위한 색상 설정
    color_scale = alt.Scale(
        domain=['Players', 'In-Game Peak'],
        range=['blue', 'purple']  # Players는 파란색, In-Game Peak은 보라색
    )

    # 범례 레이블 변경
    legend_labels = {
        'Players': '동시 접속자',
        'In-Game Peak': '인게임 피크'
    }

    # 범례를 포함한 차트 생성
    legend_chart = alt.Chart(legend_data).mark_line(point=True).encode(
        x=alt.X('Period', sort=None, title='기간'),
        y=alt.Y('Value', title='유저 수'),
        color=alt.Color('Type:N', scale=color_scale, legend=alt.Legend(
            title="데이터",
            labelExpr="datum.label === 'Players' ? '동시 접속자' : '인게임 피크'"  # 범례 레이블 변경
        )),
        tooltip=['Period', 'Type', 'Value']
    ).properties(
        width=800,
        height=400
    )

    # 스트림릿을 사용해 차트를 출력
    st.altair_chart(legend_chart, use_container_width=True)

    # 월별 플레이어 통계 테이블 표시
    with st.expander("월별 유저 통계 테이블"):
        st.table(df_filtered)

    st.markdown("<br><br>", unsafe_allow_html=True)  # 줄바꿈

    # Display yearly game release data
    release_df = fetch_release_data()

    st.markdown("#### **- 연간 게임 출시 수**")
    if release_df is not None:
        # 원본 데이터를 사용하여 차트에 데이터 표시
        release_df['Year'] = release_df['Year'].apply(lambda x: f"{x}년")

        # Yearly release bar chart with text labels
        bar_chart = alt.Chart(release_df).mark_bar().encode(
            x=alt.X('Year:O', title='기간', sort=alt.SortField(field='Year', order='ascending')),
            y=alt.Y('Games Released:Q', title='출시 수', axis=alt.Axis(format=',d')),
        ).properties(
            width=800,
            height=400,
        )

        # 막대 위에 텍스트를 추가해 데이터 표시
        text = bar_chart.mark_text(
            align='center',
            baseline='bottom',
            dy=-5  # 텍스트를 막대 위에 표시하기 위해 y축으로 살짝 이동
        ).encode(
            text=alt.Text('Games Released:Q', format=',')  # 숫자에 천 단위 콤마 추가
        )

        # 차트와 텍스트를 레이어링
        chart_with_text = bar_chart + text

        # 차트를 스트림릿에 표시
        st.altair_chart(chart_with_text, use_container_width=True)

    else:
        st.error("Yearly game release data could not be loaded.")

    st.divider()  # 구분선 추가
    st.markdown("<br>", unsafe_allow_html=True)  # 줄바꿈


    # Fetch sales, followed, most played, and trending data
    sales_df = fetch_sales_data().head(15).drop(columns=['Numeric Price', 'Numeric Change'])
    followed_df = fetch_followed_games_data().head(15)
    most_played_df, trending_df = fetch_game_data()

    # Format Follows and 7d Gain columns in followed_df
    followed_df['팔로우 수'] = followed_df['팔로우 수'].apply(lambda x: f"{x:,}")
    followed_df['팔로우 7d 변동'] = followed_df['팔로우 7d 변동'].apply(lambda x: f"+ {x:,}")

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
    st.markdown("#### **▶ Steam 트랜드 지표 요약**")

    st.markdown("<br>", unsafe_allow_html=True)  # 줄바꿈

    col1, col2 = st.columns([0.9, 1.2])

    with col1:
        st.markdown("##### **- TOP 15 현재 유저 동접 순위**")
        most_played_html = most_played_df.to_html(escape=False, formatters={
            '이미지': lambda x: f'<img src="{x}" style="width:80px;"/>',
            '스토어 링크': lambda x: f'<a href="{x}" target="_blank">Store</a>'
        }, index=False, classes='mystyle')
        st.markdown(most_played_html, unsafe_allow_html=True)

    with col2:
        st.markdown("##### **- Top 15 게임 매출 순위**")
        sales_html = sales_df.to_html(escape=False, formatters={
            '이미지': lambda x: f'<img src="{x}" style="width:80px;"/>',
            '스토어 링크': lambda x: f'<a href="{x}" target="_blank">Store</a>'
        }, index=False, classes='mystyle')
        st.markdown(sales_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)  # 줄바꿈
    col3, col4 = st.columns([0.9, 1.2])

    with col3:
        st.markdown("##### **- Top 15 트랜딩 게임 순위**")
        trending_html = trending_df.to_html(escape=False, formatters={
            '이미지': lambda x: f'<img src="{x}" style="width:80px;"/>',
            '스토어 링크': lambda x: f'<a href="{x}" target="_blank">Store</a>'
        }, index=False, classes='mystyle')
        st.markdown(trending_html, unsafe_allow_html=True)

    with col4:
        st.markdown("##### **- Top 15 팔로우 게임 순위**")
        followed_html = followed_df.to_html(escape=False, formatters={
            '이미지': lambda x: f'<img src="{x}" style="width:80px;"/>',
            '스토어 링크': lambda x: f'<a href="{x}" target="_blank">Store</a>'
        }, index=False, classes='mystyle')
        st.markdown(followed_html, unsafe_allow_html=True)


if __name__ == "__main__":
    display_summary()
