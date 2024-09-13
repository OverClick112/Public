import streamlit as st
from googlesearch import search
import requests
from bs4 import BeautifulSoup

def get_title_from_url(url):
    """URL에서 페이지의 제목을 추출하는 함수."""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("title").get_text()
        return title.strip()
    except Exception as e:
        return "제목을 찾을 수 없습니다."

def get_dc_gallery_main_url(dc_gallery_result):
    """
    DC갤러리 임의의 게시글 URL에서 갤러리 메인 URL로 변환하는 함수.
    """
    try:
        # 게시글 URL에서 갤러리 메인 링크를 추출하여 변환
        if "gall.dcinside.com" in dc_gallery_result:
            gallery_id = dc_gallery_result.split("?id=")[-1].split("&")[0]
            main_url = f"https://gall.dcinside.com/mgallery/board/lists/?id={gallery_id}"
            return main_url
    except Exception as e:
        return "No relevant result found"

def generate_search_results(title):
    """
    입력된 게임 타이틀을 바탕으로 구글에서 스팀DB, 나무위키, DC갤러리, 웹진 링크를 검색하여 반환.
    """
    # 구글 검색을 통한 SteamDB appID 링크 생성
    query_steamdb = f"{title} site:steamdb.info/app"

    # 구글 검색을 통한 나무위키 링크 생성
    query_namu = f"{title} site:namu.wiki"

    # 구글 검색을 통한 DC갤러리 임의의 게시글 링크 생성
    query_dc = f"{title} site:gall.dcinside.com"

    # 구글 검색을 통한 인벤 정규 리뷰 (최대 5개 검색)
    query_inven_review = f"{title} site:inven.co.kr/webzine/news/?news="

    # 구글 검색을 통한 디스이즈게임 정규 리뷰 (최대 5개 검색)
    query_thisisgame_review = f"{title} site:thisisgame.com/webzine/game/nboard/16/"

    # 구글 검색을 통한 루리웹 정규 리뷰 (최대 5개 검색)
    query_ruliweb_review = f"{title} site:bbs.ruliweb.com/news/read/"

    # SteamDB 링크 추출
    try:
        steam_db_result = next(search(query_steamdb, num_results=1))
        steam_db_url = steam_db_result
    except StopIteration:
        steam_db_url = "No relevant result found"

    # 나무위키 링크 추출
    try:
        namu_wiki_result = next(search(query_namu, num_results=1))
    except StopIteration:
        namu_wiki_result = "No relevant result found"

    # DC갤러리 링크 추출
    try:
        dc_gallery_result = next(search(query_dc, num_results=1))
        dc_gallery_url = get_dc_gallery_main_url(dc_gallery_result)  # 게시글을 메인 갤러리 링크로 변환
    except StopIteration:
        dc_gallery_url = "No relevant result found"

    # 인벤 리뷰 검색 결과 (최대 5개)
    inven_reviews = []
    try:
        for result in search(query_inven_review, num_results=5):
            title = get_title_from_url(result)
            inven_reviews.append({"url": result, "title": title})
    except StopIteration:
        inven_reviews.append({"url": "No relevant result found", "title": "No relevant result found"})

    # 디스이즈게임 리뷰 검색 결과 (최대 5개)
    thisisgame_reviews = []
    try:
        for result in search(query_thisisgame_review, num_results=5):
            title = get_title_from_url(result)
            thisisgame_reviews.append({"url": result, "title": title})
    except StopIteration:
        thisisgame_reviews.append({"url": "No relevant result found", "title": "No relevant result found"})

    # 루리웹 리뷰 검색 결과 (최대 5개)
    ruliweb_reviews = []
    try:
        for result in search(query_ruliweb_review, num_results=5):
            title = get_title_from_url(result)
            ruliweb_reviews.append({"url": result, "title": title})
    except StopIteration:
        ruliweb_reviews.append({"url": "No relevant result found", "title": "No relevant result found"})

    # 검색 결과 리스트 반환
    results = [
        f"1번째 결과 = 스팀 DB : [스팀DB 링크]({steam_db_url})",
        f"2번째 결과 = 나무위키 : [나무위키 링크]({namu_wiki_result})",
        f"3번째 결과 = DC갤러리 : [DC갤러리 링크]({dc_gallery_url})",
        "게임 웹진 리뷰:"
    ]

    if len(inven_reviews) == 0 and len(thisisgame_reviews) == 0 and len(ruliweb_reviews) == 0:
        results.append("유효한 검색 결과가 없습니다. 혹은 게임 타이틀을 정확하게 입력 해주세요.")
    else:
        # 인벤 리뷰 결과
        results.append(f"**인벤 리뷰:**")
        for idx, review in enumerate(inven_reviews[:5], 1):
            results.append(f"{idx}번째 리뷰: 인벤 기사: [{review['title']}]({review['url']})")

        # 디스이즈게임 리뷰 결과
        results.append(f"**디스이즈게임 리뷰:**")
        for idx, review in enumerate(thisisgame_reviews[:5], 1):
            results.append(f"{idx}번째 리뷰: 디스이즈게임 기사: [{review['title']}]({review['url']})")

        # 루리웹 리뷰 결과
        results.append(f"**루리웹 리뷰:**")
        for idx, review in enumerate(ruliweb_reviews[:5], 1):
            results.append(f"{idx}번째 리뷰: 루리웹 기사: [{review['title']}]({review['url']})")

    return results

def display_title_search():
    st.header("SteamDB 유저 통계 및 타이틀 검색")

    # 타이틀 검색창
    title = st.text_input("검색할 게임 타이틀을 입력하세요:", value="Black Myth: Wukong")

    if title:
        # 타이틀 검색 결과 생성
        results = generate_search_results(title)

        # 결과를 화면에 표시
        st.subheader(f"'{title}' 검색 결과:")
        for result in results:
            st.markdown(result, unsafe_allow_html=True)

# main.py에서 호출될 때 이 함수를 실행
if __name__ == "__main__":
    display_title_search()
