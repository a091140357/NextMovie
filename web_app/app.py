from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import routers_movies

app = FastAPI(title="NextMovie API")

@app.get("/")
async def serve_home():
    return FileResponse("static/home.html")

@app.get("/movie")
async def read_movie_page():
    return FileResponse("static/movie.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(routers_movies.router)