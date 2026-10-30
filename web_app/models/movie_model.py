import mysql.connector
from models.database import get_connection
from datetime import datetime, timezone, timedelta

def get_all_movies(num:int = 1, keyword: str = ""):
    """
    取得所有電影資料，一次16筆
    """
    if num < 1:
        return []
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            data_num = 16
            offset_num = (num - 1) * 16 

            if keyword:
                search_term = f"%{keyword}%"
                sql = "select * from movies where title_ch like %s order by id asc limit %s offset %s;"
                cursor.execute(sql, (search_term, data_num, offset_num))
            else:
                sql = "select * from movies order by id asc limit %s offset %s;"
                cursor.execute(sql, (data_num, offset_num))

            result = cursor.fetchall()
            return result
            
    except mysql.connector.Error as e:
        print(f"資料庫錯誤 {e}")
        return []
    finally:
        if connection and connection.is_connected():
            connection.close()

def get_movie_detail_data(movie_id: int):
    """
    取得單一電影詳細資料
    """
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            sql = "select * from movies where id = %s;"
            cursor.execute(sql, (movie_id,))
            movie = cursor.fetchone()

            if movie:
                return {"data": movie}
            else:
                return {"error": "找不到該電影", "data": None}
    except Exception as e:
        return {"error": str(e), "data": None}
    finally:
        connection.close()

def get_movie_showtimes_data(movie_id: int):
    """
    取得單一電影的所有場次
    """
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            sql = """
                select 
                    t.brand,
                    t.name as theater_name,
                    s.version,
                    s.venue,
                    substring(cast(s.show_datetime as char), 1, 10) as show_date,
                    substring(cast(s.show_datetime as char), 12, 5) as show_time
                from showtimes s
                join theaters t on s.theater_id = t.theater_id
                /* 👇 這裡直接讓 MySQL 抓 UTC+8 的時間 */
                where s.movie_id = %s and s.show_datetime >= DATE_ADD(now(), INTERVAL 8 HOUR)
                order by t.name, s.show_datetime;
            """
            cursor.execute(sql, (movie_id,))
            return cursor.fetchall()
    except Exception as e:
        print(f"撈取場次錯誤: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()

def get_recommend_showtime_data(movie_id, user_lat, user_lng, rec_type):
    """
    用經緯度與推薦類型，找最適合的電影場次
    """
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            base_sql = """
                select 
                    t.name as theater_name,
                    s.version,
                    substring(cast(s.show_datetime as char), 1, 10) as show_date,
                    substring(cast(s.show_datetime as char), 12, 5) as show_time,
                    st_distance_sphere(point(t.longitude, t.latitude), point(%s, %s)) as distance
                from showtimes s
                join theaters t on s.theater_id = t.theater_id
                where s.movie_id = %s and s.show_datetime >= DATE_ADD(now(), INTERVAL 8 HOUR)
            """

            if rec_type == 'earliest':
                sql = base_sql + " order by s.show_datetime asc limit 1;"
                cursor.execute(sql, (user_lng, user_lat, movie_id))
                
            elif rec_type == 'nearest':
                sql = base_sql + " order by distance asc, s.show_datetime asc limit 1;"
                cursor.execute(sql, (user_lng, user_lat, movie_id))
                
            elif rec_type == 'optimal':
                sql = base_sql + """
                    and timestampdiff(minute, DATE_ADD(now(), INTERVAL 8 HOUR), s.show_datetime) >= (st_distance_sphere(point(t.longitude, t.latitude), point(%s, %s)) / 300) + 10
                    order by 
                        (timestampdiff(minute, DATE_ADD(now(), INTERVAL 8 HOUR), s.show_datetime) + (distance / 30)) asc 
                    limit 1;
                """
                cursor.execute(sql, (user_lng, user_lat, movie_id, user_lng, user_lat))
            
            else:
                return None

            return cursor.fetchone()

    except Exception as e:
        print(f"查詢推薦場次失敗: {e}")
        return None
    finally:
        if connection and connection.is_connected():
            connection.close()