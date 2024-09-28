import streamlit as st
from googlesearch import search
import requests
from bs4 import BeautifulSoup


def get_title_and_date_from_url(url):
    """URL에서 페이지의 제목과 게시 날짜를 추출하는 함수."""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("title").get_text().strip()

        # 인벤 기사 게시 날짜 추출
        if "inven.co.kr" in url:
            date_elem = soup.find("dd")
            date = date_elem.get_text().strip() if date_elem else None
            title_elem = soup.find("div", class_="articleTitle")
            title = title_elem.get_text().strip() if title_elem else title

            if not date:
                date_elem = soup.select_one(".topinfo .date dd")
                date = date_elem.get_text().strip() if date_elem else None

            if not date:
                date_elem = soup.select_one(".review-date-reco .date > span")
                date = date_elem.get_text().strip() if date_elem else None

            if not date:
                date = "날짜 없음"

        elif "thisisgame.com" in url:
            date_elem = soup.find("span", class_="time")
            if not date_elem:
                date_elem = soup.find("span", class_="reporter-data")
            if not date_elem:
                date_elem = soup.select_one(".m-news-view-title-text h2 span")
            if not date_elem:
                date_elem = soup.select_one(".content-title-namebt .reporter-data")
            date = date_elem.get_text().strip() if date_elem else "날짜 없음"
            title_elem = soup.find("h1", class_="title") or soup.find("h1", class_="title-text")
            title = title_elem.get_text().strip() if title_elem else title

        elif "ruliweb.com" in url:
            date_elem = soup.find("span", class_="regdate")
            date = date_elem.get_text().strip() if date_elem else "날짜 없음"
            title_elem = soup.find("meta", property="og:title")
            title = title_elem["content"].strip() if title_elem else title

        elif "gamemeca.com" in url:
            date_elem = soup.find("span", class_="date")
            date = date_elem.get_text().strip() if date_elem else "날짜 없음"
            title_elem = soup.find("h1", class_="title")
            title = title_elem.get_text().strip() if title_elem else title

        else:
            date = "날짜 없음"

        return title, date
    except Exception as e:
        return "제목을 찾을 수 없습니다.", "날짜 없음"


def get_dc_gallery_main_url(dc_gallery_result):
    """DC갤러리 임의의 게시글 URL에서 갤러리 메인 URL로 변환하는 함수."""
    try:
        if "gall.dcinside.com" in dc_gallery_result:
            gallery_id = dc_gallery_result.split("?id=")[-1].split("&")[0]
            main_url = f"https://gall.dcinside.com/mgallery/board/lists/?id={gallery_id}"
            return main_url
    except Exception as e:
        return None  # 유효하지 않은 경우 None 반환


def get_arcalive_main_url(arcalive_result, keyword):
    """아카라이브 임의의 게시글 URL에서 메인 URL로 변환하는 함수."""
    try:
        if "arca.live" in arcalive_result:
            response = requests.get(arcalive_result)
            soup = BeautifulSoup(response.text, "html.parser")
            title_elem = soup.find("meta", property="og:title")
            if title_elem and keyword.lower() in title_elem["content"].lower():
                board_id = arcalive_result.split("/")[4]
                main_url = f"https://arca.live/b/{board_id}"
                return main_url
    except Exception as e:
        return None  # 유효하지 않은 경우 None 반환


def get_inven_main_url(inven_result):
    """인벤 임의의 게시글 URL에서 메인 URL로 변환하는 함수."""
    try:
        # 1. 서브도메인 형태의 인벤 메인 페이지 변환 (예: https://er.inven.co.kr/)
        if ".inven.co.kr" in inven_result:
            subdomain = inven_result.split("//")[1].split(".")[0]
            # 일반 서브도메인 (www, party 제외)
            if subdomain != "www" and subdomain != "party":
                return f"https://{subdomain}.inven.co.kr/"

        # 2. 파티 서브도메인 형태의 메인 페이지 변환 (예: https://party.inven.co.kr/descendant)
        if "party.inven.co.kr" in inven_result:
            board_id = inven_result.split("//party.inven.co.kr/")[1].split("/")[0]
            return f"https://party.inven.co.kr/{board_id}"

        # 3. 일반 게시판 형태의 메인 페이지 변환 (예: https://www.inven.co.kr/board/1234)
        if "www.inven.co.kr/board/" in inven_result and "/party/" not in inven_result:
            board_id = inven_result.split("/board/")[1].split("/")[0]
            return f"https://www.inven.co.kr/board/{board_id}"

        # 4. 파티 게시판 형태의 메인 페이지 변환 (예: https://www.inven.co.kr/board/party/6192)
        if "www.inven.co.kr/board/party/" in inven_result:
            board_id = inven_result.split("/party/")[1].split("/")[0]
            return f"https://www.inven.co.kr/board/party/{board_id}"

    except Exception as e:
        return None  # 유효하지 않은 경우 None 반환


def get_ruliweb_main_url(ruliweb_result):
    """루리웹 임의의 게시글 URL에서 메인 URL로 변환하는 함수."""
    try:
        if "ruliweb.com" in ruliweb_result:
            game_id = ruliweb_result.split("/")[4]
            main_url = f"https://bbs.ruliweb.com/game/{game_id}"
            return main_url
    except Exception as e:
        return None  # 유효하지 않은 경우 None 반환


def get_steam_store_url(steam_result):
    """스팀 스토어 URL에서 메인 URL로 변환하는 함수."""
    try:
        if "store.steampowered.com" in steam_result:
            app_id = steam_result.split("/")[4]
            main_url = f"https://store.steampowered.com/app/{app_id}/?l=korean"  # 한글화된 스토어 페이지로 연결
            return main_url
    except Exception as e:
        return None  # 유효하지 않은 경우 None 반환


def get_steam_store_preview(url):
    """스팀 스토어에서 게임 정보를 미리보기로 가져오는 함수."""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # 게임 제목
        game_title = soup.find("div", {"id": "appHubAppName"}).get_text().strip()

        # 헤더 이미지 URL
        header_image_elem = soup.find("img", {"class": "game_header_image_full"})
        header_image_url = header_image_elem["src"] if header_image_elem else ""

        # 게임 설명
        description_elem = soup.find("div", class_="game_description_snippet")
        game_description = description_elem.get_text().strip() if description_elem else "설명 없음"

        # 개발자 정보
        developer_elem = soup.select_one(".dev_row .summary a")
        developer = developer_elem.get_text().strip() if developer_elem else "개발자 없음"

        # 배급사 정보
        publisher_elem = soup.select(".dev_row .summary a")[1] if len(soup.select(".dev_row .summary a")) > 1 else None
        publisher = publisher_elem.get_text().strip() if publisher_elem else "배급사 없음"

        # 출시일
        release_date_elem = soup.find("div", class_="release_date")
        release_date = release_date_elem.find("div", class_="date").get_text().strip() if release_date_elem else "출시일 없음"

        # 평가 정보 간략화
        def get_review_summary(review_elem):
            """평가 정보를 텍스트로 간략화하여 반환하는 함수."""
            if review_elem:
                review_summary = review_elem.find("span", class_="game_review_summary").get_text().strip()
                review_count_elem = review_elem.find("span", class_="responsive_hidden")
                review_count = review_count_elem.get_text().strip() if review_count_elem else ""
                review_desc_elem = review_elem.find("span", class_="responsive_reviewdesc")
                review_desc = review_desc_elem.get_text().strip() if review_desc_elem else ""
                return f"{review_summary} {review_count} - {review_desc}"
            return "평가 없음"

        recent_reviews_elem = soup.select_one("#userReviews .user_reviews_summary_row:nth-child(1)")
        recent_reviews = get_review_summary(recent_reviews_elem)

        all_reviews_elem = soup.select_one("#userReviews .user_reviews_summary_row:nth-child(2)")
        all_reviews = get_review_summary(all_reviews_elem)

        # 인기 태그 정보
        tags_elem = soup.select(".popular_tags a.app_tag")
        tags = [tag.get_text().strip() for tag in tags_elem]

        preview_info = {
            "title": game_title,
            "image_url": header_image_url,
            "description": game_description,
            "developer": developer,
            "publisher": publisher,
            "release_date": release_date,
            "recent_reviews": recent_reviews,
            "all_reviews": all_reviews,
            "tags": tags
        }

        return preview_info

    except Exception as e:
        return None


def get_metacritic_info(url):
    """메타크리틱에서 게임 평가 정보를 미리보기로 가져오는 함수."""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, "html.parser")

        metascore_elem = soup.select_one(".c-productScoreInfo_scoreNumber .c-siteReviewScore span")
        metascore = metascore_elem.get_text().strip() if metascore_elem else "N/A"

        metascore_sentiment_elem = soup.select_one(".c-productScoreInfo_text .c-productScoreInfo_scoreSentiment")
        metascore_sentiment = metascore_sentiment_elem.get_text().strip() if metascore_sentiment_elem else "N/A"

        metascore_reviews_elem = soup.select_one(".c-productScoreInfo_reviewsTotal span")
        metascore_reviews = metascore_reviews_elem.get_text().strip() if metascore_reviews_elem else "N/A"

        userscore_elem = soup.select_one(".c-productScoreInfo_scoreNumber .c-siteReviewScore_user span")
        userscore = userscore_elem.get_text().strip() if userscore_elem else "N/A"

        userscore_sentiment_elem = soup.select(".c-productScoreInfo_text .c-productScoreInfo_scoreSentiment")[1]
        userscore_sentiment = userscore_sentiment_elem.get_text().strip() if userscore_sentiment_elem else "N/A"

        userscore_reviews_elem = soup.select(".c-productScoreInfo_reviewsTotal span")[1]
        userscore_reviews = userscore_reviews_elem.get_text().strip() if userscore_reviews_elem else "N/A"

        def get_score_distribution():
            distribution_data = soup.select(".c-GlobalScoreGraph .c-GlobalScoreGraph_indicator")
            if distribution_data:
                positive = distribution_data[0].get("style").split("(")[1].split("%")[0]
                neutral = distribution_data[1].get("style").split("(")[1].split("%")[0]
                negative = distribution_data[2].get("style").split("(")[1].split("%")[0]
                return positive, neutral, negative
            return "0", "0", "0"

        critic_positive, critic_neutral, critic_negative = get_score_distribution()

        userscore_graph_elem = soup.select(".c-GlobalScoreGraph")[1] if len(soup.select(".c-GlobalScoreGraph")) > 1 else None
        if userscore_graph_elem:
            user_positive = userscore_graph_elem.select(".c-GlobalScoreGraph_indicator--positive")[0].get("style").split("(")[1].split("%")[0]
            user_neutral = userscore_graph_elem.select(".c-GlobalScoreGraph_indicator--neutral")[0].get("style").split("(")[1].split("%")[0]
            user_negative = userscore_graph_elem.select(".c-GlobalScoreGraph_indicator--negative")[0].get("style").split("(")[1].split("%")[0]
        else:
            user_positive, user_neutral, user_negative = "0", "0", "0"

        metacritic_info = {
            "metascore": metascore,
            "metascore_sentiment": metascore_sentiment,
            "metascore_reviews": metascore_reviews,
            "userscore": userscore,
            "userscore_sentiment": userscore_sentiment,
            "userscore_reviews": userscore_reviews,
            "critic_positive": f"{float(critic_positive):.2f}",
            "critic_neutral": f"{float(critic_neutral):.2f}",
            "critic_negative": f"{float(critic_negative):.2f}",
            "user_positive": f"{float(user_positive):.2f}",
            "user_neutral": f"{float(user_neutral):.2f}",
            "user_negative": f"{float(user_negative):.2f}"
        }

        return metacritic_info

    except Exception as e:
        print(f"Error fetching metacritic info: {e}")
        return None


def filter_by_keyword(reviews, keyword):
    """검색어와 관련 없는 리뷰를 필터링."""
    return [review for review in reviews if keyword.lower() in review['title'].lower()]


def generate_search_results(title, progress_bar):
    """입력된 게임 타이틀을 바탕으로 구글에서 스팀DB, 나무위키, DC갤러리, 웹진 링크를 검색하여 반환."""
    query_steamdb = f"{title} site:steamdb.info/app"
    query_namu = f"{title} site:namu.wiki"
    query_dc = f"{title} site:gall.dcinside.com"
    query_arcalive = f"{title} site:arca.live"
    query_inven = f"{title} site:inven.co.kr"
    query_ruliweb = f"{title} site:ruliweb.com/game"

    # 스팀 스토어 검색을 위한 쿼리
    query_steam_store = f"{title} site:store.steampowered.com/app/"

    # 메타크리틱 검색을 위한 쿼리
    query_metacritic = f"{title} site:metacritic.com/game/"

    # 디스이즈게임의 최신 기사를 위한 추가 쿼리
    query_thisisgame_review = f"{title} site:thisisgame.com/webzine/special/nboard/"
    query_inven_review = f"{title} site:inven.co.kr/webzine/news/?news="
    query_ruliweb_review = f"{title} site:bbs.ruliweb.com/news/read/"
    query_gamemeca_review = f"{title} site:gamemeca.com/view.php?gid="

    progress_bar.progress(10)  # 10% 진행

    # 구글 검색을 통한 각 웹사이트 결과 추출
    try:
        steam_db_result = next(search(query_steamdb, num_results=1))
        steam_db_url = steam_db_result
    except StopIteration:
        steam_db_url = None
    progress_bar.progress(15)  # 15% 진행

    try:
        namu_wiki_result = next(search(query_namu, num_results=1))
    except StopIteration:
        namu_wiki_result = None
    progress_bar.progress(20)  # 20% 진행

    try:
        dc_gallery_result = next(search(query_dc, num_results=1))
        dc_gallery_url = get_dc_gallery_main_url(dc_gallery_result)
    except StopIteration:
        dc_gallery_url = None
    progress_bar.progress(25)  # 25% 진행

    try:
        arcalive_result = next(search(query_arcalive, num_results=1))
        arcalive_url = get_arcalive_main_url(arcalive_result, title)
    except StopIteration:
        arcalive_url = None
    progress_bar.progress(30)  # 30% 진행

    try:
        inven_result = next(search(query_inven, num_results=1))
        inven_url = get_inven_main_url(inven_result)
    except StopIteration:
        inven_url = None
    progress_bar.progress(35)  # 35% 진행

    try:
        ruliweb_result = next(search(query_ruliweb, num_results=1))
        ruliweb_url = get_ruliweb_main_url(ruliweb_result)
    except StopIteration:
        ruliweb_url = None
    progress_bar.progress(40)  # 40% 진행

    # 스팀 스토어 검색 결과 추출
    try:
        steam_store_result = next(search(query_steam_store, num_results=1))
        steam_store_url = get_steam_store_url(steam_store_result)
        steam_store_preview = get_steam_store_preview(steam_store_url)  # 스팀 스토어 미리보기 정보 가져오기
    except StopIteration:
        steam_store_url = None
        steam_store_preview = None
    progress_bar.progress(45)  # 45% 진행

    # 메타크리틱 검색 결과 추출
    try:
        metacritic_result = next(search(query_metacritic, num_results=1))
        metacritic_info = get_metacritic_info(metacritic_result)  # 메타크리틱 정보 가져오기
    except StopIteration:
        metacritic_result = None
        metacritic_info = None
    progress_bar.progress(50)  # 50% 진행

    # 웹진 리뷰 검색 결과 추출 (최대 10개)
    def get_web_reviews(query, num_results=10):
        reviews = []
        for result in search(query, num_results=num_results):
            title, date = get_title_and_date_from_url(result)
            reviews.append({"url": result, "title": title, "date": date})
        return reviews

    # 디스이즈게임 리뷰 검색
    thisisgame_reviews = get_web_reviews(query_thisisgame_review, num_results=10)
    progress_bar.progress(55)  # 55% 진행

    inven_reviews = get_web_reviews(query_inven_review, num_results=10)
    progress_bar.progress(60)  # 60% 진행

    ruliweb_reviews = get_web_reviews(query_ruliweb_review, num_results=10)
    progress_bar.progress(70)  # 70% 진행

    gamemeca_reviews = get_web_reviews(query_gamemeca_review, num_results=10)
    progress_bar.progress(80)  # 80% 진행

    # 키워드와 일치하지 않는 리뷰 필터링 및 최대 10개까지만 유지
    inven_reviews = filter_by_keyword(inven_reviews, title)[:10]
    thisisgame_reviews = filter_by_keyword(thisisgame_reviews, title)[:10]
    ruliweb_reviews = filter_by_keyword(ruliweb_reviews, title)[:10]
    gamemeca_reviews = filter_by_keyword(gamemeca_reviews, title)[:10]

    # 날짜를 기준으로 리뷰 정렬 (최신 날짜 순)
    inven_reviews.sort(key=lambda x: x['date'], reverse=True)
    thisisgame_reviews.sort(key=lambda x: x['date'], reverse=True)
    ruliweb_reviews.sort(key=lambda x: x['date'], reverse=True)
    gamemeca_reviews.sort(key=lambda x: x['date'], reverse=True)

    # ######### 결과물 형식 조정 및 배치 #########

    st.subheader(f"'{title}' 검색 결과")
    st.divider()  # 구분선 추가

    st.markdown("### [ 스팀 스토어 / 메타크리틱 미리보기 ]")

    st.markdown("<br>", unsafe_allow_html=True)  # 줄바꿈

    col1, _, col2 = st.columns([1, 0.1, 1])

    with col1:
        # 스팀 스토어 미리보기 정보가 있는 경우 표시
        if steam_store_preview:
            st.image(steam_store_preview['image_url'], width=250)
            st.markdown(f"**설명:** {steam_store_preview['description']}")
            st.markdown(f"**개발자:** {steam_store_preview['developer']}")
            st.markdown(f"**배급사:** {steam_store_preview['publisher']}")
            st.markdown(f"**출시일:** {steam_store_preview['release_date']}")
            st.markdown(f"**최근 평가:** {steam_store_preview['recent_reviews']}")
            st.markdown(f"**전체 평가:** {steam_store_preview['all_reviews']}")
            if steam_store_preview['tags']:
                st.markdown("**이 제품의 인기 태그:** " + ", ".join(steam_store_preview['tags']))
        else:
            st.markdown("- 유효한 스팀 스토어 미리보기 정보가 없습니다.")

    with col2:
        # 메타크리틱 미리보기 정보가 있는 경우 표시
        if metacritic_info:
            st.markdown("#### Metacritic Score")
            st.markdown(f"**Metascore:** {metacritic_info['metascore']} ({metacritic_info['metascore_sentiment']}) - {metacritic_info['metascore_reviews']}")
            st.markdown(f"평론가 긍정적 평가: {metacritic_info['critic_positive']}%")
            st.markdown(f"평론가 중립적 평가: {metacritic_info['critic_neutral']}%")
            st.markdown(f"평론가 부정적 평가: {metacritic_info['critic_negative']}%")
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"**User Score:** {metacritic_info['userscore']} ({metacritic_info['userscore_sentiment']}) - {metacritic_info['userscore_reviews']}")
            st.markdown(f"유저 긍정적 평가: {metacritic_info['user_positive']}%")
            st.markdown(f"유저 중립적 평가: {metacritic_info['user_neutral']}%")
            st.markdown(f"유저 부정적 평가: {metacritic_info['user_negative']}%")
        else:
            st.markdown("- 유효한 메타크리틱 미리보기 정보가 없습니다.")

    st.divider()  # 구분선 추가

    st.markdown("<br>", unsafe_allow_html=True)  # 줄바꿈

    # 링크들을 모아서 보여주는 부분
    st.markdown("### [ 공식 / 평가 / 평론 / 기사 / 리뷰등의 링크 모음 ]")
    st.markdown("##### 스팀 스토어/평가/평론/지표")

    if steam_store_url:
        st.markdown(f"- [스팀 스토어]({steam_store_url})")
    else:
        st.markdown("- 유효한 스팀 스토어 검색 결과가 없습니다.")

    if steam_db_url:
        st.markdown(f"- [스팀 DB]({steam_db_url})")
    else:
        st.markdown("- 유효한 스팀 DB 검색 결과가 없습니다.")

    if metacritic_result:
        st.markdown(f"- [메타크리틱]({metacritic_result})")
    else:
        st.markdown("- 유효한 메타크리틱 검색 결과가 없습니다.")

    st.markdown("<br>", unsafe_allow_html=True)  # 줄바꿈

    # 국내 게임 웹진 주요 기사 섹션
    st.markdown("##### 국내 게임 주요 웹진 기사/리뷰")
    st.markdown("###### ▶ 인벤")
    for idx, review in enumerate(inven_reviews, 1):
        st.markdown(f"[{review['title']}]({review['url']}) (게시 날짜: {review['date']})")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("###### ▶ 디스이즈게임")
    for idx, review in enumerate(thisisgame_reviews, 1):
        st.markdown(f"[{review['title']}]({review['url']}) (게시 날짜: {review['date']})")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("###### ▶ 루리웹")
    for idx, review in enumerate(ruliweb_reviews, 1):
        st.markdown(f"[{review['title']}]({review['url']}) (게시 날짜: {review['date']})")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("###### ▶ 게임메카")
    for idx, review in enumerate(gamemeca_reviews, 1):
        st.markdown(f"[{review['title']}]({review['url']}) (게시 날짜: {review['date']})")

    st.divider()  # 구분선 추가

    # 위키 or 커뮤니티 섹션
    st.markdown("### [ 위키 / 커뮤니티 링크 모음 ]")
    if namu_wiki_result:
        st.markdown(f"- 나무위키 : [나무위키 링크]({namu_wiki_result})")
    else:
        st.markdown("- 유효한 나무위키 검색 결과가 없습니다.")

    if inven_url:
        st.markdown(f"- 인벤 : [인벤 링크]({inven_url})")
    else:
        st.markdown("- 유효한 인벤 검색 결과가 없습니다.")

    if arcalive_url:
        st.markdown(f"- 아카라이브 : [아카라이브 링크]({arcalive_url})")
    else:
        st.markdown("- 유효한 아카라이브 검색 결과가 없습니다.")

    if dc_gallery_url:
        st.markdown(f"- DC갤러리 : [DC갤러리 링크]({dc_gallery_url})")
    else:
        st.markdown("- 유효한 DC갤러리 검색 결과가 없습니다.")

    if ruliweb_url:
        st.markdown(f"- 루리웹 : [루리웹 링크]({ruliweb_url})")
    else:
        st.markdown("- 유효한 루리웹 검색 결과가 없습니다.")

    st.divider()  # 구분선 추가

    progress_bar.progress(100)  # 100% 완료


def display_title_search():
    st.header("SteamDB 유저 통계 및 타이틀 검색")

    title = st.text_input("검색할 게임 타이틀을 입력하세요:")

    if st.button("검색 시작") or st.session_state.get("enter_pressed"):
        if not title:
            st.warning("게임 타이틀을 정확하게 입력할수록 정확도가 상승합니다.")
            st.warning("유효한 검색 결과가 없을 시 결과를 미 반환 또는 유사도가 높은 다른 결과를 반환할 수도 있습니다.")
        else:
            progress_bar = st.progress(0)
            generate_search_results(title, progress_bar)
    else:
        st.warning("게임 타이틀을 정확하게 입력할수록 정확도가 상승합니다.")
        st.warning("유효한 검색 결과가 없을 시 결과를 미 반환 또는 유사도가 높은 다른 결과를 반환할 수도 있습니다.")


if __name__ == "__main__":
    if "enter_pressed" not in st.session_state:
        st.session_state.enter_pressed = False
    display_title_search()
