from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from controllers import movie_controller

router = APIRouter(prefix="/api/movies", tags=["Movies"])

@router.get("/all_movie")
def get_all_movie(page: int = 1, keyword: str = ""):
    movie_datas = movie_controller.get_movies_list(page, keyword)

    if movie_datas is None:
        return JSONResponse(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            content = {
                "ok":False,
                "message":"伺服器錯誤"
            }
        )
    
    return{
        "ok":True,
        "data":movie_datas
    }

@router.get("/{movie_id}")
def get_movie_detail(movie_id: int):
    movie_detail = movie_controller.get_movie_detail(movie_id)
    if not movie_detail["data"]:
        return JSONResponse(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            content = {
                "ok":False,
                "message":"伺服器錯誤"
            }
        )
    
    return{
        "ok":True,
        "data":movie_detail["data"]
    }

@router.get("/{movie_id}/showtimes")
def get_movie_showtimes(movie_id: int):
    movie_showtimes = movie_controller.get_movie_showtimes(movie_id)
    if movie_showtimes is None:
        return JSONResponse(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            content = {
                "ok":False,
                "message":"伺服器錯誤"
            }
        )
    
    return{
        "ok":True,
        "data":movie_showtimes
    }

@router.get("/{movie_id}/recommend")
def get_recommend_showtime_data(
        movie_id: int, 
        type:str, 
        lat:float, 
        lng:float
    ):
    movie_recommend = movie_controller.get_recommend_showtime(movie_id, lat, lng, type)
    if movie_recommend is None:
        return JSONResponse(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            content = {
                "ok":False,
                "message":"伺服器錯誤"
            }
        )
    
    return{
        "ok":True,
        "data":movie_recommend
    }
