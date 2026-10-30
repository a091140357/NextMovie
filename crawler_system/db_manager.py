import os, boto3
import requests
from dotenv import load_dotenv
from crawler.utils import is_similar, get_now
from database import get_connection

load_dotenv()

def save_movie(movie_data):
    """
    儲存電影資料，並回傳資料庫中電影id
    """
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            release_date_raw = movie_data.get("release_date")
            
            if not release_date_raw or release_date_raw.strip() == "":
                release_date = None
            else:
                release_date = release_date_raw.replace("/", "-").strip()

            duration_raw = movie_data.get("duration_minutes")
            if not duration_raw or str(duration_raw).strip() == "" or duration_raw == 0:
                duration_minutes = None
            else:
                duration_minutes = duration_raw

            scraped_title = movie_data.get("title_ch")

            cursor.execute("select id, title_ch, title_en from movies;")
            db_movies = cursor.fetchall()

            title_en = movie_data.get("title_en", "") or ""
            matched_id = None

            for db_movie in db_movies:
                db_title = db_movie["title_ch"]
                db_title_en = db_movie["title_en"] or ""

                if title_en and db_title_en and title_en.strip().lower() == db_title_en.strip().lower():
                    matched_id = db_movie["id"]
                    break

                if is_similar(scraped_title, db_title, threshold=0.75):
                    matched_id = db_movie["id"]
                    break

            title_en = movie_data.get("title_en")
            if not title_en:
                title_en = ""
            
            if matched_id:
                print(f"[{get_now()}] {scraped_title} 找到同一部電影資料")
                sql_update = """
                update movies set
                    title_en = coalesce(nullif(%s, ""), title_en),
                    poster_url = coalesce(nullif(%s, ""), poster_url),
                    video_url = coalesce(nullif(%s, ""), video_url),
                    director = coalesce(nullif(%s, ""), director),
                    cast = coalesce(nullif(%s, ""), cast),
                    genre = coalesce(nullif(%s, ""), genre),
                    duration_minutes = coalesce(nullif(%s, ""), duration_minutes),
                    story = coalesce(nullif(%s, ""), story),
                    release_date = coalesce(nullif(%s, ""), release_date)
                where id = %s;
                """

                cursor.execute(sql_update, (
                    title_en,
                    movie_data.get("poster_url"),
                    movie_data.get("video_url"),
                    movie_data.get("director"),
                    movie_data.get("cast"),
                    movie_data.get("genre"),
                    duration_minutes,
                    movie_data.get("story"),
                    release_date,
                    matched_id
                ))
                connection.commit()
                print(f"[{get_now()}] {scraped_title} 電影資料更新")

                return matched_id
            else:
                sql_insert ='''
                        insert ignore into movies
                        (title_ch, title_en, poster_url, video_url, director, cast, genre, duration_minutes, story, release_date)
                        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        '''
                cursor.execute(sql_insert,(
                    movie_data.get("title_ch"),
                    movie_data.get("title_en"),
                    movie_data.get("poster_url"),
                    movie_data.get("video_url"),
                    movie_data.get("director"),
                    movie_data.get("cast"),
                    movie_data.get("genre"),
                    duration_minutes,
                    movie_data.get("story"),
                    release_date
                ))
                connection.commit()
                print(f"[{get_now()}] {scraped_title} 新增電影資料")

                sql_get_id = "select id from movies where title_ch = %s;"
                cursor.execute(sql_get_id,(movie_data.get("title_ch"),))
                result = cursor.fetchone()

                if result:
                    return result["id"]
                else:
                    return None
    except Exception as e:
        print(f"[{get_now()}] {movie_data.get('title_ch')}儲存時發生錯誤 {e}")
        connection.rollback()
        return None
    finally:
        connection.close()

def save_showtime(movie_id, theater_id, show_datetime, version, venue=""):
    """
    存電影場次資料
    """
    connection = get_connection()

    try:
        with connection.cursor(dictionary=True) as cursor:
            sql = """
                insert ignore into showtimes (movie_id, theater_id, version, show_datetime, venue)
                values (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql,(movie_id, theater_id, version, show_datetime, venue))
            connection.commit()
    except Exception as e:
        print(f"[{get_now()}] 儲存場次錯誤 {e}")
        connection.rollback()
    finally:
        connection.close()

def save_showtimes_batch(batch_data):
    """
    批次存入電影場次資料，大幅提升效能並避免連線塞爆
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                insert ignore into showtimes (movie_id, theater_id, version, show_datetime, venue)
                values (%s, %s, %s, %s, %s)
            """
            cursor.executemany(sql, batch_data)
            connection.commit()
            print(f"[{get_now()}] 成功批次新增 {len(batch_data)} 筆場次")
    except Exception as e:
        print(f"[{get_now()}] 批次儲存場次發生錯誤: {e}")
        connection.rollback()
    finally:
        connection.close()


def get_theater_id_by_name(theater_name):
    """
    查詢資料庫中的電影影城對應的id
    """
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            sql = "select theater_id from theaters where name = %s;"
            cursor.execute(sql, (theater_name,))
            result = cursor.fetchone()

            if result:
                return result["theater_id"]
            else:
                print(f"[{get_now()}] 找不到影城{theater_name}")
                return None
    except Exception as e:
        print(f"[{get_now()}] 查詢電影id失敗 {e}")
        return None
    finally:
        connection.close()

def save_image(image_bytes, file_name, use_s3=False):
    """
    儲存電影海報圖片 (支援本機或 AWS S3)
    """
    if use_s3: 
        try:
            S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
            # AWS_REGION = os.getenv('AWS_REGION')
            
            # s3_client = boto3.client(
            #     's3',
            #     aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            #     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            #     region_name=AWS_REGION
            # )
            
            s3_client = boto3.client('s3')

            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=file_name,
                Body=image_bytes,
                ContentType='image/jpeg'
            )

            return f"https://{S3_BUCKET_NAME}.s3.ap-northeast-1.amazonaws.com/{file_name}"
            
        except Exception as e:
            print(f"上傳圖片 {file_name} 至 S3 失敗: {e}")
            return None

    else:
        base_dir = os.path.join(os.getcwd(), "web_app", "static", "movies_imgs")
        os.makedirs(base_dir, exist_ok=True)

        file_path = os.path.join(base_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(image_bytes)
            
        return f"/static/movies_imgs/{file_name}"

def sync_movie_posters():
    connection = get_connection()
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/"
    }

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("select id, poster_url, title_ch from movies where poster_url like 'http%';")
            movies = cursor.fetchall()

            if not movies:
                print(f"[{get_now()}] 目前沒有需要下載的新海報。")
                return
            
            print(f"[{get_now()}] 正在更新 {len(movies)} 張電影海報")

            for movie in movies:
                movie_id = movie["id"]
                img_url = movie["poster_url"]
                title = movie["title_ch"]

                try:
                    response = requests.get(img_url, headers=headers, timeout=10)

                    if response.status_code == 200:
                        file_name = f"movie_{movie_id}.jpg"

                        new_path = save_image(response.content, file_name, use_s3=True)

                        update_sql = "update movies set poster_url = %s where id = %s;"
                        cursor.execute(update_sql, (new_path, movie_id))
                        connection.commit()

                        print(f"[{get_now()}] {title} 海報儲存成功")
                    else:
                        print(f"[{get_now()}] {title} 海報下載失敗 {response.status_code})")
                    
                except Exception as e:
                    print(f"[{get_now()}] {title} 海報下載發生異常: {e}")
    
    except Exception as e:
        print(f"[{get_now()}] 更新海報發生錯誤: {e}")
        connection.rollback()
    
    finally:
        connection.close()
        print(f"[{get_now()}] 海報更新完成")

def clean_expired_showtimes():
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("DELETE FROM showtimes WHERE show_datetime < NOW() - INTERVAL 1 DAY;")
            connection.commit()
    except Exception as e:
        print(f"[{get_now()}] 清理電影資料失敗 {e}")
        return None
    finally:
        connection.close()