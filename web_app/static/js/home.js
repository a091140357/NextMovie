//向後端拿資料
async function getAllMovieData(page, keyword = ""){
    try{
        const response = await fetch(`/api/movies/all_movie?page=${page}&keyword=${encodeURIComponent(keyword)}`);
        if(!response.ok){
            throw new Error("抓取不到後端資料");
        }
        const result = await response.json();
        console.log(result.data);
        return result.data;
    }
    catch(error){
        console.log(`${error}`)
        return;
    }
};

//選染電影畫面
function renderingMovieData(data){
    const sensor = document.getElementById("loading-sensor");

    if (!data || data.length === 0) {
        hasMore = false;
        sensor.innerText = "已經沒有更多電影囉！";
        return;
    }

    const moviesData = document.querySelector(".moviesData");
    let htmlContent = "";

    for (let i = 0; i < data.length; i++) {
        let movie = data[i];

    htmlContent += `
        <a href="movie?id=${movie.id}" class="movie-link" style="text-decoration: none;">
            <div class="movie-card">
                <img src="${movie.poster_url}" alt="${movie.title_ch}">
                <div class="movie-title">${movie.title_ch}</div>
            </div>
        </a>
    `;
    }
    moviesData.insertAdjacentHTML('beforeend', htmlContent);

    if (data.length < 16) {
        hasMore = false;
        sensor.innerText = "已經沒有更多電影囉！";
    } else {
        sensor.innerText = "往下捲動載入更多...";
    }
}

//無限下拉滾動監聽
function setupObserver() {
    const sensor = document.getElementById("loading-sensor");

    const observer = new IntersectionObserver(async (entries) => {
        if (entries[0].isIntersecting && !isLoading && hasMore) {
            isLoading = true;
            currentPage++;
            
            const newMovies = await getAllMovieData(currentPage, currentKeyword);
            renderingMovieData(newMovies);
            isLoading = false;
        }
    }, {
        threshold: 0.1
    });
    observer.observe(sensor);
}

let currentPage = 1;
let isLoading = false;
let hasMore = true;

let currentKeyword = "";

//觸發新的搜尋
async function triggerSearch(keyword) {
    currentKeyword = keyword;
    currentPage = 1;
    hasMore = true;
    document.querySelector(".moviesData").innerHTML = "";
    document.getElementById("loading-sensor").innerText = "載入中...";

    isLoading = true;
    const searchResult = await getAllMovieData(currentPage, currentKeyword);
    renderingMovieData(searchResult);
    isLoading = false;
}

let searchTimeout = null;
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearchBtn');

//監聽搜尋框打字
searchInput.addEventListener('input', (e) => {
    const keyword = e.target.value.trim();
    
    if (keyword.length > 0) {
        clearSearchBtn.style.display = 'block';
    } else {
        clearSearchBtn.style.display = 'none';
    }

    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        triggerSearch(keyword);
    }, 500);
});

//監聽清除按鈕
clearSearchBtn.addEventListener('click', () => {
    searchInput.value = '';
    clearSearchBtn.style.display = 'none';
    searchInput.focus();
    triggerSearch('');
});

//監聽導覽列的電影查詢按鈕
document.getElementById('nav-search-btn').addEventListener('click', (e) => {
    e.preventDefault();

    const searchInput = document.getElementById('searchInput');

    searchInput.scrollIntoView({ behavior: 'smooth', block: 'center' });

    setTimeout(() => {
        searchInput.focus();
    }, 500);
});

//監聽導覽列Logo與首頁按鈕
const homeLinks = document.querySelectorAll('.logo a, .nav-links a[href="/"]');
homeLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        if (window.location.pathname === '/' || window.location.pathname.endsWith('home.html')) {
            e.preventDefault(); 
            
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
    });
});

//初始化
async function init(){
    isLoading = true;
    const initialMovies = await getAllMovieData(currentPage, currentKeyword);
    renderingMovieData(initialMovies);
    setupObserver();
    isLoading = false;
}

init()