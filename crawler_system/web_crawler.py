import db_manager
import crawler.crawler_showtime as crawler_showtime
import crawler.crawler_vieshow as crawler_vieshow
import crawler.crawler_ambassador as crawler_ambassador
import time
from crawler.utils import get_now

theater_id_cache = {}
def process_movie_data(movie_data_list):
    for movie in movie_data_list:
        movie_id = db_manager.save_movie(movie)
        if not movie_id:
            continue

        batch_data = []

        for schedule in movie.get("schedules", []):
            theater_name = schedule.get("theater_name")

            if theater_name not in theater_id_cache:
                theater_id_cache[theater_name] = db_manager.get_theater_id_by_name(theater_name)

            theater_id = theater_id_cache[theater_name]

            if theater_id:
                batch_data.append((
                    movie_id,
                    theater_id,
                    schedule.get("version", ""),
                    schedule.get("show_datetime", ""),
                    schedule.get("venue", "")
                ))
            else:
                print(f"[{get_now()}] 找不到影城「{theater_name}」場次")

        if batch_data:
            db_manager.save_showtimes_batch(batch_data)

def lambda_handler(event, context):
    start_time = time.time()

    task = event.get("task", "all")

    if task == "vieshow":
        print(f"{get_now()} 正在爬取威秀資料...")
        vieshow_movie = crawler_vieshow.get_vieshow_data()
        process_movie_data(vieshow_movie)
        db_manager.sync_movie_posters()
        print(f"{get_now} 爬取威秀資料成功")

    elif task == "showtime":
        print(f"{get_now()} 正在爬取秀泰資料...")
        showtime_movie = crawler_showtime.get_showtime_data()
        process_movie_data(showtime_movie)
        db_manager.sync_movie_posters()
        print(f"{get_now()} 爬取秀泰資料成功")
        
    elif task == "ambassador":
        print(f"{get_now()} 正在爬取國賓資料...")
        ambassador_movie = crawler_ambassador.get_ambassador_data()
        process_movie_data(ambassador_movie)
        db_manager.sync_movie_posters()
        print(f"{get_now()} 爬取國賓資料成功")
        
    elif task == "maintenance":
        print(f"{get_now()} 執行資料庫維護 (清理過期場次與更新海報)...")
        db_manager.clean_expired_showtimes()
        db_manager.sync_movie_posters()
        print(f"{get_now()} 海報與過期資料更新完畢")

    elif task == "all":
        print(f"{get_now()} 正在清理過期的場次資料...")
        db_manager.clean_expired_showtimes()
        print(f"{get_now()} 過期資料更新完畢")

        print(f"{get_now()} 正在爬取威秀資料...")
        vieshow_movie = crawler_vieshow.get_vieshow_data()
        process_movie_data(vieshow_movie)
        print(f"{get_now()} 爬取威秀資料成功")

        print(f"{get_now()} 正在爬取秀泰資料...")
        showtime_movie = crawler_showtime.get_showtime_data()
        process_movie_data(showtime_movie)
        print(f"{get_now()} 爬取秀泰資料成功")

        print(f"{get_now()} 正在爬取國賓資料...")
        ambassador_movie = crawler_ambassador.get_ambassador_data()
        process_movie_data(ambassador_movie)
        print(f"{get_now()} 爬取國賓資料成功")

        print(f"{get_now()} 正在處理圖片...")
        db_manager.sync_movie_posters()
        print(f"{get_now()} 海報更新完畢")
    else:
        print(f"{get_now()} 未知的任務: {task}")
        return {"statusCode": 400, "body": "未知的任務"}

    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes, seconds = divmod(elapsed_time, 60)

    result_message = f"{get_now()} 任務 [{task}] 總共花費 {int(minutes)}分 {seconds:.2f}秒 執行完成"
    print(result_message)
    
    return {
        "statusCode": 200,
        "body": result_message
    }


if __name__ == "__main__":
    lambda_handler({"task": "all"}, None)
