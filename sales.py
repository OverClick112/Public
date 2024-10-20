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


def is_chrome_running(port=9225):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'chrome.exe' and any(
                f'--remote-debugging-port={port}' in cmd for cmd in proc.info['cmdline']):
            return True
    return False


@st.cache_data(ttl=30)
def fetch_sales_data():
    if not is_chrome_running(port=9225):
        try:
            subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe '
                             r'--remote-debugging-port=9225 '
                             r'--user-data-dir="C:\chromeCookie4"')
        except Exception as e:
            st.error(f"Chrome 디버그 모드 실행 중 오류가 발생했습니다: {e}")
            return None

    option = Options()
    option.add_argument('--disable-blink-features=AutomationControlled')
    option.add_argument("--start-maximized")
    option.add_experimental_option("debuggerAddress", "127.0.0.1:9225")

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)
        url = "https://store.steampowered.com/charts/topselling/global"
        driver.get(url)

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, '_2-RN6nWOY56sNmcDHu069P')))

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        sales_data = []
        sales_rows = soup.find_all('tr', class_='_2-RN6nWOY56sNmcDHu069P')

        for row in sales_rows:
            rank = row.find_all('td')[1].text.strip() if row.find_all('td')[1] else ''
            game_name_elem = row.find_all('td')[2].find('div', class_='_1n_4-zvf0n4aqGEksbgW9N')
            game_name = game_name_elem.text.strip() if game_name_elem else ''

            image_elem = row.find('img', class_='_2dODJrHKWs6F9v9QpgzihO')
            image_url = image_elem['src'] if image_elem else ''

            store_link_elem = row.find('a', class_='_2C5PJOUH6RqyuBNEwaCE9X')
            store_link = store_link_elem['href'] if store_link_elem else ''

            price_container = row.find_all('td')[3]
            sales_status = []
            for status_class in ['cnkoFkzVCby40gJ0jGGS4', '_2_KY_e11FV0ftXR2_7TMmP',
                                 '_3j4dI1yA7cRfCvK8h406OB _1Fru-E7WQMr8G_aR2sMg5F']:
                status_elem = price_container.find('div', class_=status_class)
                if status_elem:
                    sales_status.append(status_elem.text.strip())

            sales_status = ' / '.join(sales_status) if sales_status else '—'

            prices = price_container.find_all('div', class_='_3j4dI1yA7cRfCvK8h406OB')
            price = ''
            if prices:
                for p in prices:
                    if '₩' in p.text:
                        current_price = re.sub(r'[^\d]', '', p.text)
                        if price == '' or (current_price and int(current_price) < int(price)):
                            price = p.text.strip()
                    elif 'Free To Play' in p.text:
                        price = 'Free'

            change_elem = row.find_all('td')[4].find('div', class_='_2OA1JW-4H-f01kM7myTUuu')
            change = change_elem.text.strip() if change_elem else ''
            peak_position_elem = row.find_all('td')[5].find('div', class_='_2OA1JW-4H-f01kM7myTUuu')
            peak_position = f"{peak_position_elem.text.strip()}주" if peak_position_elem else '0주'

            sales_data.append([rank, image_url, store_link, game_name, sales_status, price, change, peak_position])

        df = pd.DataFrame(sales_data,
                          columns=['순위', '이미지', '스토어 링크', '타이틀', '세일 정보', '가격', '순위 변동', 'in 100위 유지'])

        df.replace('N/A', '', inplace=True)
        df['Numeric Price'] = pd.to_numeric(df['가격'].str.replace('₩', '').str.replace(',', ''),
                                            errors='coerce').fillna(0)
        df['Numeric Change'] = df['순위 변동'].apply(
            lambda x: float(x.replace('▲', '').replace('▼', '-').replace(' ', '').replace('New', '0')) if x else 0)

        return df

    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None


def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Top Sellers')
    processed_data = output.getvalue()
    return processed_data


def display_sales():
    st.header("SteamDB 판매량 차트")

    df = fetch_sales_data()

    if df is not None:
        st.subheader("Top Sellers Chart")

        with st.sidebar:
            st.header("필터 옵션")
            rank_filter = st.slider("순위", min_value=1, max_value=100, value=(1, 100))
            price_filter = st.slider("가격 (₩)", min_value=int(df['Numeric Price'].min()),
                                     max_value=int(df['Numeric Price'].max()),
                                     value=(int(df['Numeric Price'].min()), int(df['Numeric Price'].max())))

            change_filter_option = st.selectbox("순위 변동 정렬 옵션", options=["필터 없음", "오름차순", "내림차순", "New만 표기"], index=0)

            min_peak = int(df['in 100위 유지'].str.replace('주', '').astype(int).min())
            max_peak = int(df['in 100위 유지'].str.replace('주', '').astype(int).max())
            peak_position_filter = st.slider("in 100위 유지", min_value=min_peak, max_value=max_peak,
                                             value=(min_peak, max_peak))

        filtered_df = df[
            (df['순위'].astype(int) >= rank_filter[0]) & (df['순위'].astype(int) <= rank_filter[1]) &
            (df['Numeric Price'] >= price_filter[0]) & (df['Numeric Price'] <= price_filter[1]) &
            (df['in 100위 유지'].str.replace('주', '').astype(int) >= peak_position_filter[0]) &
            (df['in 100위 유지'].str.replace('주', '').astype(int) <= peak_position_filter[1])
        ]

        if change_filter_option == "오름차순":
            filtered_df = filtered_df[filtered_df['순위 변동'] != 'New'].sort_values(by='Numeric Change', ascending=True)
        elif change_filter_option == "내림차순":
            filtered_df = filtered_df[filtered_df['순위 변동'] != 'New'].sort_values(by='Numeric Change', ascending=False)
        elif change_filter_option == "New만 표기":
            filtered_df = filtered_df[filtered_df['순위 변동'] == 'New']

        filtered_df = filtered_df.drop(columns=['Numeric Price', 'Numeric Change'])

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
            border: 3px solid #000;
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

        excel_data = convert_df_to_excel(filtered_df)
        st.download_button(
            label="엑셀로 다운로드",
            data=excel_data,
            file_name='Top_Sellers.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    else:
        st.error("판매량 데이터를 가져오지 못했습니다.")


if __name__ == "__main__":
    display_sales()
