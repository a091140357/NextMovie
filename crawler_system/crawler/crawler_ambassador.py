from curl_cffi import requests
from bs4 import BeautifulSoup
import time
import random
from crawler.utils import get_now

def get_movie_data(movie_url):
    base_url = "https://www.ambassador.com.tw/"
    movie_data_url = base_url + movie_url

    response = requests.get(movie_data_url, impersonate="chrome110")
    soup = BeautifulSoup(response.text, "html.parser")

    movie_introduce = soup.find(class_ = "cell small-12 medium-12 large-12 movie-info-box")

    title_ch = ""
    title_en = ""
    poster_url = ""
    story = ""
    cast = ""
    genre = ""
    release_date = ""
    video_url = ""

    if movie_introduce:
        #中英文片名
        title_ch = movie_introduce.find("h2").text
        title_en = movie_introduce.find("h6").text

        #片長
        spans = movie_introduce.find(class_ = "rating-box").find_all("span")
        duration_raw_data = ""
        duration_minutes = 0

        for span in spans:
            text = span.text
            if "時" in text and "分" in text:
                duration_raw_data = text
                break

        if duration_raw_data:
            hour = int(duration_raw_data.split("時")[0])
            min = int(duration_raw_data.split("時")[1].split("分")[0])
            duration_minutes = hour * 60 + min
        

        movie_introduce_p_label_list = movie_introduce.find_all("p")
        if movie_introduce_p_label_list:
            #劇情介紹
            story = movie_introduce_p_label_list[0].text

            #演員
            cast = movie_introduce_p_label_list[1].text.split("主要演員：")[1]

            #類型
            genre = movie_introduce_p_label_list[2].text.split("影片類型：")[1]

            #上映日期
            release_date = movie_introduce_p_label_list[3].text.split("上映日期：")[1]

    #圖片
    img_div = soup.find(class_ = "cell small-3 medium-2 large-2 movie-pic-box")
    if img_div:
        poster_url = img_div.find("img").get("src")

    #影片
    video_div = soup.find(class_ = "responsive-embed widescreen")
    if video_div:
        video_url = video_div.find("iframe").get("src").split("?")[0]

    #時刻表
    theater_name_list = ["國賓大戲院", "台北長春國賓影城", "新莊晶冠國賓影城", "林口昕境國賓影城", "淡水禮萊國賓影城"]
    
    matches_label_list = soup.find(class_ = "menu scrollbar")
    schedules = []
    if matches_label_list:
        schedules_dict = {}
        matches_ul_list = matches_label_list.find_all("li")
        for item in matches_ul_list:
            schedules_time_raw = item.find("a").text
            
            schedules_time = schedules_time_raw.split(",")[1].replace("/", "-")
            schedules_url = item.find("a").get("href")
            schedules_dict[schedules_time] = schedules_url

        for schedule_item in schedules_dict.keys():
            schedule_url = base_url + schedules_dict[schedule_item]
            print(f"正在爬取 {schedule_url}")
            response = requests.get(schedule_url, impersonate="chrome110")
            soup = BeautifulSoup(response.text, "html.parser")

            theater_list_div = soup.find(class_ = "theater-list")
            if theater_list_div:
                theaters_box = theater_list_div.find_all(class_ = "theater-box")
                for theater_schedule in theaters_box:
                    theater_name = theater_schedule.find("h3").find("a").text
                    if not theater_name in theater_name_list:
                        continue

                    version_tags = theater_schedule.find_all(class_="tag-seat")
                    for version_tag in version_tags:
                        version_raw = version_tag.text

                        if "(" in version_raw and ")" in version_raw:
                            version = version_raw.split("(")[1].split(")")[0]
                        else:
                            version = version_raw.strip()

                        ul_item = version_tag.find_next_sibling("ul", class_="no-bullet seat-list")
                        if ul_item:
                            time_list = ul_item.find_all("li")

                            for time_item in time_list:
                                if time_item.find("h6"):
                                    time = time_item.find("h6").text.strip()

                                    venue_raw = time_item.find("p").text
                                    venue = venue_raw.split(" ")[0]
                                    schedules.append({
                                        "cinema_brand": "國賓",
                                        "theater_name": f"{theater_name}",
                                        "version": f"{version}",
                                        "show_datetime": f"{schedule_item.replace(' ', '')} {time}",
                                        "venue": f"{venue}"
                                    })

    return{
        "movie_id": "",
        "title_ch":title_ch,
        "title_en":title_en,
        "poster_url":poster_url,
        "video_url":video_url,
        "director":"",
        "cast":cast,
        "genre":genre,
        "duration_minutes":duration_minutes,
        "story":story,
        "schedules":schedules,
        "release_date": release_date
        }


def get_ambassador_data():
    movie_introduce_url = "https://www.ambassador.com.tw/home/MovieList?Type=1"
    response = requests.get(movie_introduce_url, impersonate="chrome110")

    if response.status_code != 200:
        print(f"[{get_now()}] 國賓電影院資料爬取失敗")
        print(f"[{get_now()}] {response.status_code}")
        return {}


    soup = BeautifulSoup(response.text, "html.parser")
    print(f"[{get_now()}] 正在爬取國賓電影院資料")

    movie_data_list = soup.find_all(class_ = "cell")
    movie_url_list = []
    print(f"[{get_now()}] 抓到的國賓電影資料總共有 {len(movie_data_list)} 筆")
    for movie_data in movie_data_list:
        movie_a_label = movie_data.find("a", class_ = "poster")
        if movie_a_label:
            movie_url = movie_a_label.get("href")
            movie_url_list.append(movie_url)
    

    all_movie = []

    data_num = 1
    for movie_data in movie_url_list:
        print(f"[{get_now()}] 正在爬取第 {data_num} 筆資料")

        result = get_movie_data(movie_data)
        if result:
            all_movie.append(result)
        
        data_num += 1
        time.sleep(random.uniform(1.5, 3.0))
    
    print(f"[{get_now()}] 國賓爬蟲抓取成功")
    return all_movie

    # file_time = datetime.now().strftime("%m%d_%H%M")
    # filename = f"ambassdor_movies_{file_time}.json"

    # with open(filename, "w", encoding="utf-8") as f:
    #     json.dump(all_movie, f, ensure_ascii=False, indent=2)
