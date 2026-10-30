import json
import db_manager
from database import get_connection
from crawler.utils import get_now

def save_theater(theater_data):
    """
    存電影院資料，並返回該影城id
    """
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            sql_insert = """
                    insert ignore into theaters(brand, name, latitude, longitude,address)
                    values(%s, %s, %s, %s, %s)
                """
            cursor.execute(sql_insert,(
                theater_data.get("brand"),
                theater_data.get("name"),
                theater_data.get("latitude"),
                theater_data.get("longitude"),
                theater_data.get("address")
            ))
            connection.commit()
            print(f"[{get_now()}] {theater_data.get('name')} 儲存成功")

            sql_get_id = "SELECT theater_id FROM theaters WHERE name = %s;"
            cursor.execute(sql_get_id, (theater_data.get("name"),))
            result = cursor.fetchone()

            if result:
                return result["theater_id"]
            else:
                return None
            
    except Exception as e:
        print(f"[{get_now()}] 儲存 {theater_data.get('name')} 失敗 {e}")
        connection.rollback()
        return None
    finally:
        connection.close()

def main():
    try:
        with open('crawler_system/theaters.json', 'r', encoding='utf-8') as f:
            theaters = json.load(f)

        for theater in theaters:
            theater_id = save_theater(theater)
        
        print("電影影城資料儲存完成")
    except Exception as e:
        print(f"錯誤 {e}")

if __name__ == "__main__":
    main()