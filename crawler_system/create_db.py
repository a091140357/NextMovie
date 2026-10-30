import pymysql, os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

connection = None

try:
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    with connection.cursor() as cursor:
        print(f"建立資料庫 {DB_NAME}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute(f"USE {DB_NAME};")

        tables_sql = [
            '''
            create table if not exists movies(
                id int auto_increment primary key,
                title_ch varchar(255) not null,
                title_en varchar(255),
                poster_url varchar(500),
                video_url varchar(500),
                director varchar(255),
                `cast` text,
                genre varchar(255),
                duration_minutes int,
                story text,
                release_date date,
                status int default 1,
                created_at datetime default current_timestamp,
                unique key uk_title (title_ch, title_en)
                );
            ''',
            '''
            create table if not exists theaters(
                theater_id int auto_increment primary key,
                brand varchar(50) not null,
                name varchar(255) not null,
                latitude decimal(10, 7),
                longitude decimal(10, 7),
                address varchar(100),
                unique key uk_theater_name (name)
                );
            ''',
            '''
            create table if not exists showtimes(
                id bigint auto_increment primary key,
                movie_id int not null,
                theater_id int not null,
                version varchar(100),
                venue varchar(100),
                show_datetime datetime not null,
                foreign key (movie_id) references movies(id) on delete cascade,
                foreign key (theater_id) references theaters(theater_id) on delete cascade,
                unique key uk_showtime(theater_id, movie_id, show_datetime, version, venue),
                index idx_show_datetime (show_datetime)
                );
            '''
        ]

        for sql in tables_sql:
            cursor.execute(sql)
        
        connection.commit()
        print("建立資料庫成功")

except pymysql.MySQLError as e:
    print(f"資料庫操作失敗  {e}")
    if connection:
        connection.rollback()

except Exception as e:
    print(f"資料庫建立失敗  {e}")
finally:
    if connection and connection.open:
        connection.close()
        print("資料庫已關閉")
    