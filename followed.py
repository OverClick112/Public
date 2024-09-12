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
from io import BytesIO


def is_chrome_running(port=9226):
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

            followers_elem = row.find('td', class_='text-center dt-type-numeric')
            followers = followers_elem.text.strip().replace(',', '') if followers_elem else ''

            trend_elem = row.find_all('td', class_='dt-type-numeric')[2]
            trend = trend_elem.text.strip().replace('+', '').replace(',', '') if trend_elem else '0'

            price_elem = row.find_all('td', class_='dt-type-numeric')[3]
            if price_elem:
                price_text = price_elem.text.strip().split('\n')[0] if price_elem.text.strip() else 'N/A'
                discount_elem = price_elem.find('span', class_='price-discount-minor')
                discount_text = discount_elem.text.strip() if discount_elem else ''
                final_price = f"{price_text} at {discount_text}" if discount_text else price_text
            else:
                final_price = 'N/A'

            release_date = row.find_all('td')[-1].text.strip()

            app_id = row['data-appid']

            image_elem = row.find('img')
            image_url = f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{app_id}/{image_elem['data-capsule']}" if image_elem and image_elem.has_attr(
                'data-capsule') else ''

            video_url_elem = row.find('td', class_='applogo').find('a')
            video_url = video_url_elem['href'] if video_url_elem and 'href' in video_url_elem.attrs else ''

            games_data.append([image_url, video_url, game_name, sub_info, followers, trend, final_price, release_date])

        df = pd.DataFrame(games_data,
                          columns=['Image URL', 'Video URL', 'Game Name', 'Sub Info', 'Followers', 'Trend', 'Price',
                                   'Release Date'])

        df.insert(0, 'Rank', range(1, len(df) + 1))
        df['Rank'] = df['Rank'].astype(str)

        return df

    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None


def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Followed Games')
    processed_data = output.getvalue()
    return processed_data


def display_followed():
    st.header("Most Followed Upcoming Steam Games")

    df = fetch_followed_games_data()

    if df is not None:
        st.subheader("Most Followed Games")

        df['Followers'] = df['Followers'].replace(',', '', regex=True).astype(int)

        df['Numeric Trend'] = pd.to_numeric(df['Trend'].str.replace(',', ''), errors='coerce').fillna(0)

        with st.sidebar:
            st.header("필터 옵션")

            rank_filter = st.slider("Rank", min_value=1, max_value=250, value=(1, 250))

            followers_filter = st.slider("Followers", min_value=int(df['Followers'].min()),
                                         max_value=int(df['Followers'].max()),
                                         value=(int(df['Followers'].min()), int(df['Followers'].max())))

            trend_filter_option = st.selectbox("Trend 정렬 옵션", ["필터 없음", "오름차순", "내림차순"], index=0)

            price_filter_option = st.selectbox("Price 필터", ["필터 없음", "가격", "Free", "N/A"], index=0)

            release_date_filter_option = st.selectbox("Release Date 필터",
                                                      ["필터 없음", "출시일 예정", "Coming soon", "To be announced"], index=0)

        filtered_df = df[(df['Rank'].astype(int) >= rank_filter[0]) & (df['Rank'].astype(int) <= rank_filter[1])]

        filtered_df = filtered_df[
            (df['Followers'].astype(int) >= followers_filter[0]) & (df['Followers'].astype(int) <= followers_filter[1])]

        if trend_filter_option == "오름차순":
            filtered_df = filtered_df.sort_values(by='Numeric Trend', ascending=True)
        elif trend_filter_option == "내림차순":
            filtered_df = filtered_df.sort_values(by='Numeric Trend', ascending=False)

        if price_filter_option == "가격":
            filtered_df = filtered_df[filtered_df['Price'].str.contains("₩")]
        elif price_filter_option == "Free":
            filtered_df = filtered_df[filtered_df['Price'] == "Free"]
        elif price_filter_option == "N/A":
            filtered_df = filtered_df[filtered_df['Price'] == "N/A"]

        if release_date_filter_option == "출시일 예정":
            filtered_df = filtered_df[filtered_df['Release Date'].str.contains(r'\d{2} \w+ \d{4}', regex=True)]
        elif release_date_filter_option == "Coming soon":
            filtered_df = filtered_df[filtered_df['Release Date'] == "Coming soon"]
        elif release_date_filter_option == "To be announced":
            filtered_df = filtered_df[filtered_df['Release Date'] == "To be announced"]

        filtered_df = filtered_df.drop(columns=['Numeric Trend'])

        filtered_df['Followers'] = filtered_df['Followers'].apply(lambda x: f"{x:,}")

        filtered_df['Trend'] = filtered_df['Trend'].apply(lambda x: f"+{x}" if not x.startswith('-') else x)

        def format_price(price):
            if "₩" in price:
                price_parts = price.split(' at ')
                price_number = int(price_parts[0].replace('₩', '').replace(',', '').strip())
                formatted_price = f"₩ {price_number:,}"
                if len(price_parts) > 1:
                    formatted_price += f" at {price_parts[1]}"
                return formatted_price
            return price

        filtered_df['Price'] = filtered_df['Price'].apply(format_price)

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

        html = filtered_df.to_html(escape=False, formatters={
            'Image URL': lambda x: f'<img src="{x}" style="width:100px;"/>',
            'Video URL': lambda x: f'<a href="{x}" target="_blank">Video Link</a>'
        }, index=False, classes='mystyle')

        st.markdown(html, unsafe_allow_html=True)

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
