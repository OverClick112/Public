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

# 필터 목록 (전체 옵션)
FILTERS = {
    "모두 보기": 0,
    "Profile Features Limited": 1003823,
    "Indie": 492,
    "Singleplayer": 4182,
    "Action": 19,
    "Casual": 597,
    "Adventure": 21,
    "Simulation": 599,
    "2D": 3871,
    "RPG": 122,
    "Strategy": 9,
    "3D": 4191,
    "Atmospheric": 4166,
    "Colorful": 4305,
    "Fantasy": 1684,
    "Puzzle": 1664,
    "Story Rich": 1742,
    "Exploration": 3834,
    "Pixel Graphics": 3964,
    "Cute": 4726,
    "First-Person": 3839,
    "Multiplayer": 3859,
    "Free to Play": 113,
    "Action-Adventure": 4106,
    "Arcade": 1773,
    "Early Access": 493,
    "Demo Available": 21491,
    "Relaxing": 1654,
    "Funny": 4136,
    "Anime": 4085,
    "Shooter": 1774,
    "Sci-fi": 3942,
    "Combat": 3993,
    "Horror": 1667,
    "Family Friendly": 5350,
    "Third Person": 1697,
    "Stylized": 4252,
    "Retro": 4004,
    "Platformer": 1625,
    "Female Protagonist": 7208,
    "Sexual Content": 12095,
    "Controller": 7481,
    "Top-Down": 4791,
    "Nudity": 6650,
    "Realistic": 4175,
    "Visual Novel": 3799,
    "Violent": 4667,
    "Open World": 1695,
    "Choices Matter": 6426,
    "Survival": 1662,
    "2D Platformer": 5379,
    "PvP": 1775,
    "Soundtrack": 7948,
    "Cartoony": 4195,
    "Linear": 7250,
    "PvE": 6730,
    "Mystery": 5716,
    "Dark": 4342,
    "Comedy": 1719,
    "Multiple Endings": 6971,
    "Co-op": 1685,
    "Physics": 3968,
    "FPS": 1663,
    "Gore": 4345,
    "Sports": 701,
    "Character Customization": 4747,
    "Psychological Horror": 1721,
    "Old School": 3916,
    "Adult Content": 65443,
    "Sandbox": 3810,
    "Medieval": 4172,
    "Minimalist": 4094,
    "Action RPG": 4231,
    "Difficult": 4026,
    "Hand-drawn": 6815,
    "Rogue-like": 1716,
    "Point & Click": 1698,
    "Magic": 4057,
    "Online Co-Op": 3843,
    "Rogue-lite": 3959,
    "Racing": 699,
    "Space": 1755,
    "Building": 1643,
    "Tactical": 1708,
    "Management": 12472,
    "Shoot 'Em Up": 4255,
    "3D Platformer": 5395,
    "VR": 21978,
    "Side Scroller": 3798,
    "Drama": 5984,
    "Immersive Sim": 9204,
    "Futuristic": 4295,
    "Massively Multiplayer": 128,
    "Logic": 6129,
    "Choose Your Own Adventure": 4486,
    "Cartoon": 4562,
    "Action Roguelike": 42804,
    "Romance": 4947,
    "Crafting": 1702,
    "Procedural Generation": 5125,
    "Puzzle-Platformer": 5537,
    "Turn-Based Strategy": 1741,
    "Interactive Fiction": 11014,
    "Tabletop": 17389,
    "Dark Fantasy": 4604,
    "Turn-Based Combat": 4325,
    "Turn-Based Tactics": 14139,
    "Emotional": 5608,
    "Survival Horror": 3978,
    "Hidden Object": 1738,
    "Hack and Slash": 1646,
    "Bullet Hell": 4885,
    "Resource Management": 8945,
    "1980s": 7743,
    "Mature": 5611,
    "Great Soundtrack": 1756,
    "Nature": 30358,
    "Education": 1036,
    "Local Multiplayer": 7368,
    "JRPG": 4434,
    "Dating Sim": 9551,
    "Party-Based RPG": 10695,
    "Dungeon Crawler": 1720,
    "Base Building": 7332,
    "1990's": 6691,
    "Walking Simulator": 5900,
    "Surreal": 1710,
    "Post-apocalyptic": 3835,
    "Turn-Based": 1677,
    "Design & Illustration": 84,
    "War": 1678,
    "Score Attack": 5154,
    "Zombies": 1659,
    "Historical": 3987,
    "Hentai": 9130,
    "NSFW": 24904,
    "Top-Down Shooter": 4637,
    "Text-Based": 31275,
    "Cinematic": 4145,
    "Card Game": 1666,
    "Replay Value": 4711,
    "Life Sim": 10235,
    "Stealth": 1687,
    "Isometric": 5851,
    "2.5D": 4975,
    "Clicker": 379975,
    "Narration": 5094,
    "Local Co-Op": 3841,
    "Third-Person Shooter": 3814,
    "Investigation": 8369,
    "Military": 4168,
    "LGBTQ+": 44868,
    "Conversation": 15172,
    "Cyberpunk": 4115,
    "Utilities": 87,
    "Strategy RPG": 17305,
    "Precision Platformer": 3877,
    "Abstract": 4400,
    "RTS": 1676,
    "Detective": 5613,
    "Lore-Rich": 3854,
    "Board Game": 1770,
    "Robots": 5752,
    "Aliens": 1673,
    "Software": 8013,
    "Economy": 4695,
    "Real Time Tactics": 3813,
    "Dark Humor": 5923,
    "Thriller": 4064,
    "Demons": 9541,
    "Time Management": 16689,
    "Arena Shooter": 5547,
    "Driving": 1644,
    "Nonlinear": 6869,
    "Psychological": 5186,
    "Tower Defense": 1645,
    "Collectathon": 5652,
    "Perma Death": 1759,
    "Supernatural": 10808,
    "Web Publishing": 1038,
    "Team-Based": 5711,
    "City Builder": 4328,
    "Tutorial": 12057,
    "Tactical RPG": 21725,
    "Deckbuilding": 32322,
    "Comic Book": 1751,
    "Modern": 5673,
    "Fast-Paced": 1734,
    "Psychedelic": 1714,
    "Idler": 615955,
    "Short": 4234,
    "Wargame": 4684,
    "Flight": 15045,
    "Dystopian": 5030,
    "Beat 'em up": 4158,
    "Metroidvania": 1628,
    "Artificial Intelligence": 7926,
    "Memes": 10397,
    "Runner": 8666,
    "Inventory Management": 6276,
    "Loot": 4236,
    "4 Player Local": 4840,
    "Souls-like": 29482,
    "Music": 1621,
    "Card Battler": 791774,
    "Alternate History": 4598,
    "Level Editor": 8122,
    "Parkour": 4036,
    "Cats": 17894,
    "Automobile Sim": 1100687,
    "2D Fighter": 4736,
    "Grid-Based Movement": 7569,
    "Mythology": 16094,
    "CRPG": 4474,
    "Crime": 6378,
    "Destruction": 5363,
    "Game Development": 13906,
    "Creature Collector": 916648,
    "RPGMaker": 5577,
    "Rhythm": 1752,
    "Twin Stick Shooter": 4758,
    "Competitive": 3878,
    "Fighting": 1743,
    "Moddable": 1669,
    "Experimental": 13782,
    "Movie": 4700,
    "Philosophical": 15277,
    "3D Fighter": 6506,
    "Dark Comedy": 19995,
    "Farming Sim": 87918,
    "Capitalism": 4845,
    "Animation & Modeling": 872,
    "Automation": 255534,
    "Grand Strategy": 4364,
    "Lovecraftian": 7432,
    "Space Sim": 16598,
    "Match 3": 1665,
    "Class-Based": 4155,
    "Swordplay": 4608,
    "Classic": 1693,
    "Science": 5794,
    "Noir": 6052,
    "Colony Sim": 220585,
    "Vehicular Combat": 11104,
    "eSports": 5055,
    "Gun Customization": 5765,
    "Split Screen": 10816,
    "Word Game": 24003,
    "MMORPG": 1754,
    "Battle Royale": 176981,
    "Mystery Dungeon": 198631,
    "Dragons": 4046,
    "America": 13190,
    "Cooking": 3920,
    "World War II": 4150,
    "Auto Battler": 1084988,
    "3D Vision": 29363,
    "Cozy": 97376,
    "6DOF": 4835,
    "Hero Shooter": 620519,
    "Parody": 4878,
    "Spectacle fighter": 4777,
    "Looter Shooter": 353880,
    "Agriculture": 22602,
    "Trading": 4202,
    "Bullet Time": 5796,
    "Solitaire": 13070,
    "Combat Racing": 4102,
    "Conspiracy": 5372,
    "Voxel": 1732,
    "Martial Arts": 6915,
    "Gothic": 3952,
    "Beautiful": 5411,
    "Mechs": 4821,
    "Open World Survival Craft": 1100689,
    "Time Manipulation": 6625,
    "Audio Production": 1027,
    "Action RTS": 1723,
    "Satire": 1651,
    "Underground": 21006,
    "Video Production": 784,
    "Pirates": 1681,
    "God Game": 5300,
    "Quick-Time Events": 4559,
    "Steampunk": 1777,
    "Wholesome": 552282,
    "Character Action Game": 3955,
    "Co-op Campaign": 4508,
    "Dog": 1638,
    "Sokoban": 1730,
    "Time Travel": 10679,
    "Mining": 5981,
    "Tanks": 13276,
    "FMV": 18594,
    "Dynamic Narration": 9592,
    "Trading Card Game": 9271,
    "Hex Grid": 1717,
    "Ninja": 1688,
    "Political": 4853,
    "Transportation": 10383,
    "Vampire": 4018,
    "Blood": 5228,
    "Roguelike Deckbuilder": 1091588,
    "Underwater": 9157,
    "Otome": 31579,
    "Hunting": 9564,
    "Mouse only": 11123,
    "4X": 1670,
    "Software Training": 1445,
    "Fishing": 15564,
    "Narrative": 7702,
    "Trains": 1616,
    "Immersive": 3934,
    "Dinosaurs": 5160,
    "Party Game": 7178,
    "MOBA": 1718,
    "Hacking": 5502,
    "Western": 1647,
    "Political Sim": 26921,
    "Asynchronous Multiplayer": 17770,
    "Faith": 180368,
    "Programming": 5432,
    "Superhero": 1671,
    "Episodic": 4242,
    "Politics": 4754,
    "Typing": 1674,
    "Gambling": 16250,
    "Assassin": 4376,
    "Real-Time": 4161,
    "Party": 7108,
    "Naval": 6910,
    "Diplomacy": 6310,
    "Minigames": 8093,
    "Dungeons & Dragons": 14153,
    "Traditional Roguelike": 454187,
    "Escape Room": 769306,
    "Boomer Shooter": 1023537,
    "Heist": 1680,
    "Photo Editing": 809,
    "Trivia": 10437,
    "Cold War": 5179,
    "Snow": 9803,
    "Archery": 13382,
    "Remake": 5708,
    "Naval Combat": 4994,
    "Addictive": 4190,
    "Real-Time with Pause": 7107,
    "Sailing": 13577,
    "On-Rails Shooter": 56690,
    "Time Attack": 5390,
    "Football (Soccer)": 1254546,
    "Music-Based Procedural Generation": 8253,
    "Foreign": 51306,
    "Offroad": 7622,
    "Horses": 6041,
    "Illuminati": 7478,
    "Transhumanism": 4137,
    "Spelling": 71389,
    "Sniper": 7423,
    "360 Video": 776177,
    "Werewolves": 17015,
    "Mars": 6702,
    "Nostalgia": 14720,
    "Boxing": 12190,
    "Touch-Friendly": 25085,
    "Villain Protagonist": 11333,
    "Sequel": 5230,
    "Jet": 92092,
    "Cult Classic": 7782,
    "Chess": 4184,
    "Farming": 4520,
    "Motorbike": 198913,
    "Outbreak Sim": 1100686,
    "GameMaker": 1649,
    "Roguevania": 922563,
    "Golf": 7038,
    "Experience": 9994,
    "Bikes": 123332,
    "World War I": 5382,
    "Medical Sim": 1100688,
    "Rome": 6948,
    "Spaceships": 4291,
    "Submarine": 19780,
    "Electronic Music": 61357,
    "Unforgiving": 1733,
    "Kickstarter": 5153,
    "Social Deduction": 745697,
    "Basketball": 1746,
    "LEGO": 1736,
    "Mod": 5348,
    "Documentary": 15339,
    "Ambient": 29855,
    "Dwarf": 7918,
    "Asymmetric VR": 856791,
    "Gaming": 150626,
    "Pinball": 6621,
    "Skateboarding": 1753,
    "Mini Golf": 22955,
    "Wrestling": 47827,
    "Job Simulator": 35079,
    "Silent Protagonist": 15954,
    "Football (American)": 1254552,
    "Epic": 3965,
    "Instrumental Music": 189941,
    "TrackIR": 8075,
    "Crowdfunded": 7113,
    "Tennis": 5914,
    "Jump Scare": 42089,
    "Pool": 17927,
    "Games Workshop": 5310,
    "Skating": 96359,
    "Baseball": 5727,
    "Cycling": 19568,
    "Boss Rush": 11095,
    "Intentionally Awkward Controls": 14906,
    "Tile-Matching": 176733,
    "Vikings": 11634,
    "Rock Music": 337964,
    "Motocross": 15868,
    "Warhammer 40K": 12286,
    "Based On A Novel": 3796,
    "Extraction Shooter": 1199779,
    "Lemmings": 17337,
    "Hockey": 324176,
    "8-bit Music": 117648,
    "Bowling": 7328,
    "Mahjong": 33572,
    "Skiing": 7309,
    "Snowboarding": 28444,
    "Well-Written": 8461,
    "BMX": 252854,
    "Shop Keeper": 91114,
    "Electronic": 143739,
    "ATV": 129761,
    "Birds": 6214,
    "Voice Control": 27758,
    "Musou": 323922,
    "Hardware": 603297,
    "Dice": 7556,
    "Benchmark": 5407,
    "Feature Film": 233824,
    "Fox": 30927,
    "Elf": 102530,
    "Coding": 42329,
    "Cricket": 158638,
    "Steam Machine": 348922,
    "Hobby Sim": 1220528,
    "Rugby": 49213,
    "Volleyball": 847164,
    "Snooker": 363767,
    "Reboot": 5941
}

def is_chrome_running(port=9227):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'chrome.exe' and any(
                f'--remote-debugging-port={port}' in cmd for cmd in proc.info['cmdline']):
            return True
    return False

@st.cache_data(ttl=30)
def fetch_release_data(tag_id=None):
    if not is_chrome_running(port=9227):
        try:
            subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe '
                             r'--remote-debugging-port=9227 '
                             r'--user-data-dir="C:\chromeCookie6"')
        except Exception as e:
            print(f"Chrome 디버그 모드 실행 중 오류가 발생했습니다: {e}")
            return None

    option = Options()
    option.add_argument('--disable-blink-features=AutomationControlled')
    option.add_argument("--start-maximized")
    option.add_experimental_option("debuggerAddress", "127.0.0.1:9227")

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)

        if tag_id and tag_id != 0:
            url = f"https://steamdb.info/stats/releases/?tagid={tag_id}"
        else:
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
                print(f"Error processing row: {e}")
                continue

        if not release_data:
            print("No release data found.")
            return None

        df = pd.DataFrame(release_data, columns=['Games Released', 'Year'])
        return df

    except Exception as e:
        print(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None

def display_release_stats(tag_id=None):
    st.header("Steam 출시 게임 통계")

    # 사이드바 필터 기능 추가
    if tag_id is None:
        selected_filter = st.sidebar.selectbox("필터 선택", options=list(FILTERS.keys()), index=0, key="sidebar_filter")
        tag_id = FILTERS.get(selected_filter, 0)
    else:
        selected_filter = [key for key, value in FILTERS.items() if value == tag_id][0]
        st.sidebar.selectbox("필터 선택", options=list(FILTERS.keys()), index=list(FILTERS.keys()).index(selected_filter), key="sidebar_filter")

    all_data_df = fetch_release_data(0)
    filtered_data_df = fetch_release_data(tag_id)

    if all_data_df is not None and filtered_data_df is not None:
        comparison_df = pd.merge(all_data_df, filtered_data_df, on='Year', how='left', suffixes=('_all', '_filtered'))
        comparison_df['Games Released_filtered'] = comparison_df['Games Released_filtered'].fillna(0)
        comparison_df['Percentage'] = (comparison_df['Games Released_filtered'] / comparison_df['Games Released_all']) * 100

        # Games Released 컬럼에 쉼표 추가
        comparison_df['Games Released_filtered'] = comparison_df['Games Released_filtered'].apply(lambda x: f"{int(x):,}")
        comparison_df['Games Released_all'] = comparison_df['Games Released_all'].apply(lambda x: f"{int(x):,}")

        # Year 컬럼에 '년' 추가
        comparison_df['Year'] = comparison_df['Year'].apply(lambda x: f"{x}년")

        st.subheader("Yearly Game Release Data with Percentage")
        with st.expander("Yearly Game Release Data (Click to Expand)"):
            st.table(comparison_df[['Year', 'Games Released_filtered', 'Games Released_all', 'Percentage']])

        all_data_df['Year'] = all_data_df['Year'].apply(lambda x: f"{x}년")
        filtered_data_df['Year'] = filtered_data_df['Year'].apply(lambda x: f"{x}년")

        # Games Released 차트
        all_data_chart = alt.Chart(all_data_df).mark_bar(opacity=0.6, color='darkblue').encode(
            x=alt.X('Year:O', title='Year', sort=alt.SortField(field='Year', order='ascending')),
            y=alt.Y('Games Released:Q', axis=alt.Axis(title='Games Released', titleColor='darkblue'),
                    scale=alt.Scale(domain=[0, 20000])),
        )

        filtered_data_chart = alt.Chart(filtered_data_df).mark_bar(opacity=0.8, color='blue').encode(
            x=alt.X('Year:O'),
            y=alt.Y('Games Released:Q', axis=alt.Axis(title=None), scale=alt.Scale(domain=[0, 20000])),
        )

        # Percentage 값 텍스트 오버레이 추가 (크기 키우고 색상 변경)
        percentage_text = alt.Chart(comparison_df).mark_text(
            align='center',
            baseline='middle',
            dx=0,
            dy=-64,
            color='orange',  # 주황색으로 변경
            fontSize=14,  # 텍스트 크기 키움
            fontWeight='bold'  # 글씨를 굵게 변경
        ).encode(
            x=alt.X('Year:O'),
            y=alt.Y('Percentage:Q', scale=alt.Scale(domain=[0, 300])),  # Percentage 축을 기준으로 텍스트 위치 지정
            text=alt.Text('Percentage:Q', format='.0%')  # 소수점 없이 % 기호 추가
        ).transform_calculate(
            Percentage='datum.Percentage / 100'  # Percentage 값을 100으로 나누어 퍼센트로 변환
        )

        # 두 차트 통합
        combined_chart = alt.layer(
            all_data_chart,
            filtered_data_chart,
            percentage_text
        ).resolve_scale(
            y='shared'
        ).properties(
            width=800,
            height=400,
            title="Comparison of Total and Filtered Steam Game Releases with Percentage"
        )

        st.altair_chart(combined_chart, use_container_width=True)

    else:
        st.error("게임 출시 데이터를 가져오지 못했습니다.")

    # 필터 옵션을 보기 좋게 열(Column) 형태로 나누어 표시
    st.subheader("필터 옵션")

    columns = st.columns(5)  # 3열로 배치
    filter_keys = list(FILTERS.keys())
    for i, filter_name in enumerate(filter_keys):
        columns[i % 5].write(filter_name)  # 3열로 나누어 출력

if __name__ == "__main__":
    display_release_stats()
