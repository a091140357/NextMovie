const urlParams = new URLSearchParams(window.location.search);
const movieId = urlParams.get('id');

//向後端拿單一電影資料
async function getSingleMovieData(id) {
    try {
        const response = await fetch(`/api/movies/${id}`);
        if (!response.ok) throw new Error("找不到該電影");
        
        const result = await response.json();
        console.log(result)
        return result.data;
    } catch (error) {
        console.log(error);
        return null;
    }
}

//渲染電影資訊
function renderMovieDetail(movie) {
    const container = document.getElementById('movieDetail');
    if (!movie) {
        container.innerHTML = "<h2 style='color:white; text-align:center;'>找不到這部電影的資料</h2>";
        return;
    }

    container.innerHTML = `
        <div class="movie-detail-container">
            <img src="${movie.poster_url}" alt="${movie.title_ch}" class="movie-poster">
            
            <div class="movie-info">
                <h1>${movie.title_ch}</h1>
                <h3>${movie.title_en}</h3>
                <p><strong>導演：</strong> ${movie.director}</p>
                <p><strong>演員：</strong> ${movie.cast}</p>
                <p><strong>片長：</strong> ${movie.duration_minutes} 分鐘</p>
                
                <p class="movie-story">${movie.story}</p>
            </div>
        </div>
    `;
}

//向後端拿電影的所有場次資料
async function getShowtimesData(id) {
    try {
        const response = await fetch(`/api/movies/${id}/showtimes`);
        if (!response.ok) throw new Error("找不到場次資料");
        
        const result = await response.json();
        console.log("場次資料：", result.data);
        return result.data;
    } catch (error) {
        console.log(error);
        return [];
    }
}

//渲染場次區域
let allShowtimesData = []; 
let currentSelectedDate = "";

function renderShowtimes(showtimes) {
    const container = document.getElementById('movieDetail');
    
    if (!showtimes || showtimes.length === 0) {
        container.insertAdjacentHTML('beforeend', '<h3 class="no-showtimes">目前無場次資訊</h3>');
        return;
    }

    allShowtimesData = showtimes;

    const uniqueDates = [...new Set(showtimes.map(st => st.show_date))].sort();
    
    currentSelectedDate = uniqueDates[0];

    let htmlContent = `
        <div class="showtimes-section">
            
            <div id="smartButtonsWrapper" style="display: none; margin-bottom: 30px;">
                <div class="smart-recommendation" style="background: #222; padding: 20px; border-radius: 8px;">
                    <h3 style="margin-top: 0; margin-bottom: 10px; color: #fff;">場次推薦</h3>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button class="rec-btn" onclick="getRecommendation('earliest')" style="padding: 10px; cursor: pointer; background: #444; color: white; border: none; border-radius: 5px;">最快開演</button>
                        <button class="rec-btn" onclick="getRecommendation('nearest')" style="padding: 10px; cursor: pointer; background: #444; color: white; border: none; border-radius: 5px;">離我最近</button>
                        <button class="rec-btn" onclick="getRecommendation('optimal')" style="padding: 10px; cursor: pointer; background: #444; color: white; border: none; border-radius: 5px;">最佳推薦</button>
                    </div>
                    <div id="recStatus" style="margin-top: 15px; color: #ffcc00; font-weight: bold;"></div>
                </div>
            </div>

            <h2>時刻表</h2>
            
            <div class="date-selector">
                ${uniqueDates.map(date => {
                    const displayDate = date.substring(5).replace('-', '/');
                    const isActive = date === currentSelectedDate ? 'active' : '';
                    return `<button class="date-btn ${isActive}" data-date="${date}">${displayDate}</button>`;
                }).join('')}
            </div>

            <div id="showtimesList"></div>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', htmlContent);

    const dateBtns = document.querySelectorAll('.date-btn');
    dateBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            dateBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            currentSelectedDate = e.target.getAttribute('data-date');
            updateShowtimesList();
        });
    });

    updateShowtimesList();
}

//根據目前選擇的日期，更新下方的場次時間列表
function updateShowtimesList() {
    const listContainer = document.getElementById('showtimesList');
    listContainer.innerHTML = "";

    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

    const smartButtonsWrapper = document.getElementById('smartButtonsWrapper');
    if (smartButtonsWrapper) {
        if (currentSelectedDate === todayStr) {
            smartButtonsWrapper.style.display = 'block';
            document.getElementById('recStatus').innerHTML = '';
        } else {
            smartButtonsWrapper.style.display = 'none';
        }
    }

    const filteredShowtimes = allShowtimesData.filter(st => st.show_date === currentSelectedDate);

    const groupedShowtimes = {};
    filteredShowtimes.forEach(st => {
        const brand = st.brand || "其他影城";
        const theater = st.theater_name;

        if (!groupedShowtimes[brand]) {
            groupedShowtimes[brand] = {};
        }
        if (!groupedShowtimes[brand][theater]) {
            groupedShowtimes[brand][theater] = [];
        }
        
        groupedShowtimes[brand][theater].push(st);
    });

    let htmlContent = "";
    for (const [brand, theaters] of Object.entries(groupedShowtimes)) {
        htmlContent += `
            <div class="brand-group">
                <h2 class="brand-name" style="margin-top: 30px; border-bottom: 2px solid #555; padding-bottom: 10px; color: #f0f0f0;">
                    ${brand}
                </h2>
        `;
        
        for (const [theater, times] of Object.entries(theaters)) {
            htmlContent += `
                <div class="theater-group" style="margin-left: 15px;">
                    <h3 class="theater-name" style="color: #ccc; margin-top: 15px;"> ${theater}</h3>
                    <div class="time-list" style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px;">
                        ${times.map(t => `
                            <div class="time-tag" data-theater="${theater}" data-time="${t.show_time}" style="background-color: #333; padding: 10px; border-radius: 5px; min-width: 80px; text-align: center; transition: all 0.3s ease;">
                                <div class="time-tag-info" style="font-size: 12px; color: #aaa; margin-bottom: 5px;">
                                    ${t.version || '2D'} ${t.venue || ''}
                                </div>
                                <div class="time-tag-time" style="font-size: 16px; font-weight: bold; color: white;">
                                    ${t.show_time}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        htmlContent += `</div>`;
    }
    if (htmlContent === "") {
        htmlContent = "<p style='color: white; margin-top: 20px;'>這天沒有排定場次喔。</p>";
    }
    listContainer.innerHTML = htmlContent;
}

//根據指定條件取得並顯示推薦場次
function getRecommendation(type) {
    const statusDiv = document.getElementById('recStatus');
    statusDiv.innerHTML = " 查詢中，請稍候...";

    document.querySelectorAll('.time-tag').forEach(tag => {
        tag.style.backgroundColor = '#333';
        tag.style.transform = 'scale(1)';
        tag.style.border = 'none';
    });

    if (!navigator.geolocation) {
        statusDiv.innerHTML = " 您的瀏覽器不支援地理位置功能。";
        return;
    }

    navigator.geolocation.getCurrentPosition(async (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        console.log(lat, lng)

        try {
            const response = await fetch(`/api/movies/${movieId}/recommend?type=${type}&lat=${lat}&lng=${lng}`);
            const data = await response.json();

            if (data.data) {
                const st = data.data;

                const dist = Math.round(st.distance);

                statusDiv.innerHTML = ` 找到場次！距離您約 ${Math.round(st.distance_m)} 公尺`;

                const targetTag = document.querySelector(`.time-tag[data-theater="${st.theater_name}"][data-time="${st.show_time}"]`);
                
                if (targetTag) {
                    statusDiv.innerHTML = `找到場次！距離您約 ${dist} 公尺`;
                    targetTag.style.backgroundColor = '#e50914';
                    targetTag.style.border = '2px solid white';
                    targetTag.style.transform = 'scale(1.1)';
                    targetTag.scrollIntoView({ behavior: 'smooth', block: 'center' });
                } else {
                    statusDiv.innerHTML = `推薦結果為 <strong>${st.show_date}</strong> 的 <strong>${st.theater_name} (${st.show_time})</strong>，距離約 ${dist} 公尺。 (請點擊上方日期切換查看)`;
                }

            } else {
                statusDiv.innerHTML = "目前沒有符合條件的場次。";
            }
        } catch (error) {
            statusDiv.innerHTML = "查詢失敗，請稍後再試。";
        }
    }, (error) => {
        statusDiv.innerHTML = "請允許網頁存取您的位置，才能推薦場次喔！";
    });
}

//電影頁面初始化
async function initMoviePage() {
    if (!movieId) {
        document.getElementById('movieDetail').innerHTML = "<h2>參數錯誤：沒有電影 ID</h2>";
        return;
    }
    const movieData = await getSingleMovieData(movieId);
    renderMovieDetail(movieData);

    const showtimesData = await getShowtimesData(movieId);
    renderShowtimes(showtimesData);
}

initMoviePage();