from models import movie_model

def get_movies_list(page:int = 1, keyword: str = ""):
    raw_movies = movie_model.get_all_movies(page, keyword)
    return raw_movies

def get_movie_detail(movie_id: int):
    movie_detail = movie_model.get_movie_detail_data(movie_id)
    return movie_detail

def get_movie_showtimes(movie_id: int):
    movie_showtimes = movie_model.get_movie_showtimes_data(movie_id)
    return movie_showtimes
def get_recommend_showtime(movie_id, user_lat, user_lng, rec_type):
    movie_recommend = movie_model.get_recommend_showtime_data(movie_id, user_lat, user_lng, rec_type)
    return movie_recommend