import re
import time
import random
from urllib.parse import urljoin
from curl_cffi import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from crawler.utils import get_now

def get_movie_matches(movie_id):
    # 根據輸入的電影編號去爬資料
    movie_introduce_url = "https://www.vscinemas.com.tw/film/detail.aspx?id=" + movie_id
    response = requests.get(movie_introduce_url, impersonate="chrome110")

    if response.status_code != 200:
        return {}

    soup = BeautifulSoup(response.text, "html.parser")

    # 中英文片名
    title_area = soup.find(class_="titleArea")
    title_ch = ""
    title_en = ""
    if title_area:
        h1_tag = title_area.find("h1")
        h2_tag = title_area.find("h2")
        title_ch = h1_tag.text.strip() if h1_tag else ""
        title_en = h2_tag.text.strip() if h2_tag else ""

    # 電影宣傳圖片
    poster_url = ""
    movie_main = soup.find(class_="movieMain")
    if movie_main and movie_main.find("img"):
        img_src = movie_main.find("img").get("src", "")
        poster_url = urljoin(movie_introduce_url, img_src)

    # 影片連結
    video_url = ""
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "")
        if "youtube.com" in src or "youtu.be" in src:
            video_url = src
            break

    # 劇情簡介、導演、演員、類型、片長
    story_div = soup.find(class_="bbsArticle")
    story = story_div.text.strip() if story_div else ""

    director = ""
    cast = ""
    genre = ""
    duration_minutes = 0
    
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) >= 2:
            label = tds[0].text.strip()
            value = " ".join(tds[1].text.split())
            if "導演" in label:
                director = value
            elif "演員" in label:
                cast = value
            elif "類型" in label:
                genre = value
            elif "片長" in label:
                h_match = re.search(r"(\d+)\s*時", value)
                m_match = re.search(r"(\d+)\s*分", value)
                h = int(h_match.group(1)) if h_match else 0
                m = int(m_match.group(1)) if m_match else 0
                duration_minutes = h * 60 + m
    
    movie_matches = []
    versionList_ul = soup.find(class_="versionList")

    if versionList_ul:
        versionList = versionList_ul.find_all("li", recursive=False)

        for versionList_li in versionList:
            version_first = versionList_li.find(class_="versionFirst")
            if not version_first:
                continue
            version_name = version_first.text.strip()
            
            sub_ul = versionList_li.find("ul")
            if not sub_ul:
                continue
            theather_list = sub_ul.find_all("li")

            shuangbei_keywords = ["台北", "大巨蛋", "樹林", "土城", "板橋", "中和", "林口", "新店", "松仁"]

            for theather_list_li in theather_list:
                theather_name = theather_list_li.text.strip()
                
                if not any(keyword in theather_name for keyword in shuangbei_keywords):
                    continue

                time_id = theather_list_li.find("a").get("href").replace("#", "")
                schedule_box = soup.find(id=time_id)
                
                if schedule_box:
                    for day_div in schedule_box.find_all(class_="movieDay"):
                        h4_tag = day_div.find("h4")
                        if not h4_tag:
                            continue
                        raw_date = h4_tag.text.strip()
                        nums = re.findall(r"\d+", raw_date)
                        
                        if len(nums) >= 3:
                            date_str = f"{nums[0]}-{int(nums[1]):02d}-{int(nums[2]):02d}"
                        else:
                            date_str = raw_date.replace("/", "-")

                        book_list = day_div.find(class_="bookList")
                        if book_list:
                            for time_li in book_list.find_all("li"):
                                t_text = time_li.text.strip()
                                if t_text:
                                    is_next_day = "(隔日)" in t_text
                                    clean_time = t_text.replace("(隔日)", "")

                                    base_datetime_str = f"{date_str} {clean_time}:00"

                                    try:
                                        dt_obj = datetime.strptime(base_datetime_str, "%Y-%m-%d %H:%M:%S")
                                        if is_next_day:
                                            dt_obj += timedelta(days=1)

                                        show_datetime = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                                    
                                    except ValueError:
                                        show_datetime = base_datetime_str

                                    movie_matches.append({
                                        "cinema_brand": "威秀",
                                        "theater_name": theather_name,
                                        "version": version_name,
                                        "show_datetime": show_datetime
                                    })
        
    return {
        "movie_id": movie_id,
        "title_ch": title_ch,
        "title_en": title_en,
        "poster_url": poster_url,
        "video_url": video_url,
        "director": director,
        "cast": cast,
        "genre": genre,
        "duration_minutes": duration_minutes,
        "story": story,
        "schedules": movie_matches
    }

def get_vieshow_data():

    base_list_url = "https://www.vscinemas.com.tw/film/index.aspx"

    response = requests.get(base_list_url, impersonate="chrome110")
    total_pages = 1

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        pagebar = soup.find(class_="pagebar")
        if pagebar:
            page_nums = [int(a.text.strip()) for a in pagebar.find_all("a") if a.text.strip().isdigit()]
            if page_nums:
                total_pages = max(page_nums)
    print(f"總共有 {total_pages} 頁")

    all_movies = []
            
    for page in range(1, total_pages + 1):
        page_url = f"{base_list_url}?p={page}"
        print(f"\n========== 正在爬第 {page} 頁 ==========")

        res = requests.get(page_url, impersonate="chrome110")
        if res.status_code != 200:
            print(f"第 {page} 頁失敗：{res.status_code}")
            continue

        page_soup = BeautifulSoup(res.text, "html.parser")
        movie_ul = page_soup.find(class_="movieList")
        if not movie_ul:
            continue

        movie_list = movie_ul.find_all("li")

        for idx, item in enumerate(movie_list, start=1):
            a_tag = item.find("figure").find("a")
            if not a_tag or "id=" not in a_tag.get("href", ""):
                continue

            movie_id = a_tag.get("href").split("id=")[1]

            movie_title = item.find(class_="infoArea").find("a").text.strip()
            print(f"[{get_now()}] [第 {page} 頁 - {idx}/{len(movie_list)}] 正在爬：{movie_title} (ID: {movie_id})...")

            time_tag = item.find(class_="infoArea").find("time")
            release_date = time_tag.text.strip().replace("-", "/") if time_tag else ""

            movie_data = get_movie_matches(movie_id)

            if movie_data:
                movie_data["release_date"] = release_date
                all_movies.append(movie_data)
            
            time.sleep(random.uniform(2.0, 3.0))

    print(f"[{get_now()}] 威秀爬蟲抓取成功")
    return all_movies

    # file_time = datetime.now().strftime("%m%d_%H%M")
    # filename = f"vieshow_movies_{file_time}.json"

    # with open(filename, "w", encoding="utf-8") as f:
    #     json.dump(all_movies, f, ensure_ascii=False, indent=2)

    # print(f"爬成功：{filename}")