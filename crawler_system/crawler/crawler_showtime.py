import requests
from datetime import datetime, timezone, timedelta
from crawler.utils import get_now

def get_showtime_data():

    api_url = "https://capi.showtimes.com.tw/4/app/bootstrap"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            print(f"[[{get_now()}]] 正在抓取秀泰資料")
            data  = response.json()

            data_cinema = data["payload"]["corporations"]
            cinema_dict = {}

            for cinema in data_cinema: #電影院對照表
                cinema_dict[str(cinema["id"])] = cinema["name"]

            events_dict = {}

            schedules_eventsForCorporations_list = data["payload"]["eventsForCorporations"]
            schedules_eventsForCorporations_keys = schedules_eventsForCorporations_list.keys()

            shuangbei_keywords = ["台北", "大巨蛋", "樹林", "土城", "板橋", "中和", "林口", "新店", "松仁"]


            for item in schedules_eventsForCorporations_keys:
                venues_list = schedules_eventsForCorporations_list[item]["venues"]
                events_list = schedules_eventsForCorporations_list[item]["events"]
                theater_name = cinema_dict[item]

                if not any(keyword in theater_name for keyword in shuangbei_keywords):
                    continue

                venues_dict = {}
                for venue_data in venues_list: #影廳對照表
                    venues_dict[venue_data["id"]] = venue_data["room"]

                for event in events_list:
                    program = event["programId"]
                    version = event["meta"]["format"]

                    startedAt= event["startedAt"].replace("z", "+00:00")
                    utc_time = datetime.fromisoformat(startedAt)
                    tw_timezone = timezone(timedelta(hours=8))
                    tw_time = utc_time.astimezone(tw_timezone)
                    time = tw_time.strftime("%Y-%m-%d %H:%M:%S")

                    venue = venues_dict[event["venueId"]]

                    if str(program) not in events_dict:
                        events_dict[str(program)] = []

                    events_dict[str(program)].append({
                        "cinema_brand":"秀泰",
                        "theater_name":theater_name,
                        "version":version,
                        "show_datetime":time,
                        "venue":venue
                                            })

            data_programs = data["payload"]["programs"]
            movie_list = []
            print(f"[{get_now()}] 正在整理秀泰 {len(data_programs)} 筆資料")

            for program in data_programs:
                raw_story = program.get("description","")
                clean_story = raw_story.replace("\r\n","").replace("\n", "").replace("<br><br>", "").replace("<br>", "").replace("\r","")

                movie_schedules = events_dict.get(str(program["id"]), [])
                
                raw_directors = (program.get("meta") or {}).get("directors") or []
                raw_casts = (program.get("meta") or {}).get("authors") or []
                raw_genres = program.get("genres") or []

                movie_list_data = {
                    "movie_id":str(program["id"]),
                    "title_ch":program.get("name",""),
                    "title_en":program.get("nameAlternative",""),
                    "poster_url":(program.get("coverImagePortrait") or {}).get("url",""),
                    "video_url":(program.get("previewVideo") or {}).get("url",""),
                    "director":",".join(raw_directors),
                    "cast":",".join(raw_casts),
                    "genre":",".join(raw_genres),
                    "duration_minutes":(program.get("duration",0))//60,
                    "story":clean_story,
                    "release_date": "",
                    "schedules":movie_schedules
                }

                movie_list.append(movie_list_data)
                print(f"[{get_now()}] {program.get('name','')} 資料爬取成功")

        print(f"[{get_now()}] 秀泰爬蟲抓取成功")
        return movie_list
    
    except Exception as e:
        print(f"秀泰 API 連線失敗: {e}")
    return []
            
        # file_time = datetime.now().strftime("%m%d_%H%M")
        # filename = f"showtime_movies_{file_time}.json"
        
        # with open(filename, "w", encoding="utf-8") as f:
        #     json.dump(movie_list, f, ensure_ascii=False, indent=2)
        

    #     print(f"秀泰爬蟲成功，爬到{len(movie_list)}筆資料")

    # else:
    #     print(response.status_code)