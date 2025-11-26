let map;
let allMarkers = [];
let infoWindow;
let allShrinesData = [];

// 1. 카테고리별 색상 정의
const categoryColors = {
    '재물': '#FBC02D', // Gold
    '연애': '#E91E63', // Pink
    '사랑': '#E91E63',
    '건강': '#2E7D32', // Green
    '학업': '#1565C0', // Blue
    '안전': '#455A64', // BlueGrey
    '성공': '#512DA8', // Purple
    '역사': '#EF6C00', // Orange
    '기타': '#D32F2F'  // Red
};

// 2. 신사에 가장 적합한 카테고리 키 찾기
function findMainCategory(categories) {
    if (!categories || categories.length === 0) return '기타';
    for (const colorKey of Object.keys(categoryColors)) {
        if (colorKey === '기타') continue;
        const match = categories.some(cat => cat.includes(colorKey));
        if (match) return colorKey;
    }
    return '기타';
}

async function initMap() {
    const tokyoCoords = { lat: 35.6895, lng: 139.6917 };
    
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 11,
        center: tokyoCoords,
        mapId: "DEMO_MAP_ID", // 벡터 지도 활성화
        mapTypeControl: false,
        fullscreenControl: false,
        streetViewControl: false,
        options: { gestureHandling: 'greedy' }
    });

    infoWindow = new google.maps.InfoWindow();

    // 내 위치 찾기 버튼 추가
    addLocationButton();

    try {
        const response = await fetch('/api/shrines');
        const jsonData = await response.json();
        allShrinesData = jsonData.shrines ? jsonData.shrines : jsonData;

        if (!Array.isArray(allShrinesData)) return;

        if (jsonData.last_updated) {
            const msgElement = document.getElementById('update-msg');
            if (msgElement) msgElement.textContent = `데이터 업데이트: ${jsonData.last_updated}`;
        }

        addMarkers(allShrinesData);
        renderTop5Shrines(allShrinesData);
        setupFilterButtons();
        
        // [추가됨] 버튼에 건수(숫자) 표시하기
        updateFilterButtonCounts(allShrinesData);

    } catch (error) {
        console.error("초기화 오류:", error);
    }
}

// [추가됨] 카테고리별 개수를 세서 버튼 텍스트 업데이트
function updateFilterButtonCounts(shrines) {
    // 테마 키와 한글 키워드 매핑
    const themeMap = {
        'wealth': '재물', 'love': '연애', 'health': '건강',
        'study': '학업', 'safety': '안전', 'success': '성공', 'history': '역사'
    };

    // 1. 카운트 초기화 (전체 개수 먼저 설정)
    const counts = { 'all': shrines.length };
    Object.keys(themeMap).forEach(key => counts[key] = 0);

    // 2. 데이터 순회하며 개수 세기
    shrines.forEach(shrine => {
        if (!shrine.categories) return;
        
        Object.keys(themeMap).forEach(themeKey => {
            const keyword = themeMap[themeKey];
            // 해당 키워드가 포함되어 있으면 카운트 증가
            if (shrine.categories.some(cat => cat.includes(keyword))) {
                counts[themeKey]++;
            }
        });
    });

    // 3. 버튼 텍스트 업데이트
    const buttons = document.querySelectorAll('.theme-button');
    buttons.forEach(btn => {
        const theme = btn.getAttribute('data-theme');
        const count = counts[theme] || 0;

        // 기존 텍스트(예: "재물")만 가져오기 (혹시 이미 숫자가 있어도 제거)
        // firstChild가 텍스트 노드라고 가정
        const originalText = btn.childNodes[0].nodeValue.trim(); 
        
        // 텍스트 변경: "재물" -> "재물 (5)"
        btn.textContent = `${originalText} (${count})`;
    });
}

function addMarkers(shrines) {
    allMarkers.forEach(marker => marker.map = null);
    allMarkers = [];

    shrines.forEach((shrine) => {
        if (!shrine.lat || !shrine.lng) return;

        const mainCategoryKey = findMainCategory(shrine.categories);
        const borderColor = categoryColors[mainCategoryKey] || categoryColors['기타'];

        // 이미지 마커 생성
        const pinImg = document.createElement("img");
        pinImg.src = "assets/images/marker_torii.png"; 
        
        pinImg.style.width = "40px";
        pinImg.style.height = "40px";
        pinImg.style.borderRadius = "50%";
        pinImg.style.border = `3px solid ${borderColor}`;
        pinImg.style.backgroundColor = "white";
        pinImg.style.boxShadow = "0 3px 6px rgba(0,0,0,0.3)";
        pinImg.style.objectFit = "contain";
        pinImg.style.padding = "2px";

        const marker = new google.maps.marker.AdvancedMarkerElement({
            map: map,
            position: { lat: shrine.lat, lng: shrine.lng },
            title: shrine.title,
            content: pinImg,
        });

        marker.categories = shrine.categories || [];
        marker.mainCategoryKey = mainCategoryKey;

        marker.addListener("click", () => {
            const directionsUrl = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(shrine.title)}&travelmode=walking`;
            const contentString = `
                <div class="infowindow-content">
                    <img src="${shrine.thumbnail}" alt="${shrine.title}">
                    <h3>${shrine.title}</h3>
                    <p>🏷️ ${shrine.categories.join(', ')}</p>
                    <div style="margin-top: 10px; display: flex; gap: 8px;">
                        <a href="${directionsUrl}" target="_blank" 
                           style="flex: 1; background: #4285F4; color: white; text-align: center; padding: 6px; border-radius: 4px; text-decoration: none; font-size: 13px;">
                           📍 길찾기
                        </a>
                        <a href="${shrine.link}" target="_blank" 
                           style="flex: 1; background: #f1f1f1; color: #333; text-align: center; padding: 6px; border-radius: 4px; text-decoration: none; font-size: 13px; border: 1px solid #ddd;">
                           블로그 보기
                        </a>
                    </div>
                </div>
            `;
            infoWindow.setContent(contentString);
            infoWindow.open(map, marker);
        });

        allMarkers.push(marker);
    });
}

function filterMapMarkers(theme) {
    const themeMap = {
        'wealth': '재물', 'love': '연애', 'health': '건강',
        'study': '학업', 'safety': '안전', 'success': '성공', 'history': '역사'
    };

    const targetCategory = themeMap[theme];

    allMarkers.forEach(marker => {
        let isVisible = false;
        if (theme === 'all') {
            isVisible = true;
        } else {
            isVisible = marker.categories.some(cat => cat.includes(targetCategory));
        }
        marker.map = isVisible ? map : null;
    });
}

function addLocationButton() {
    const locationButton = document.createElement("button");
    locationButton.innerHTML = "🎯 내 위치";
    locationButton.style.backgroundColor = "#fff";
    locationButton.style.border = "2px solid #fff";
    locationButton.style.borderRadius = "2px";
    locationButton.style.boxShadow = "0 2px 6px rgba(0,0,0,.3)";
    locationButton.style.color = "rgb(25,25,25)";
    locationButton.style.cursor = "pointer";
    locationButton.style.fontFamily = "Roboto,Arial,sans-serif";
    locationButton.style.fontSize = "14px";
    locationButton.style.lineHeight = "38px";
    locationButton.style.margin = "10px";
    locationButton.style.padding = "0 10px";
    locationButton.style.textAlign = "center";
    
    locationButton.addEventListener("click", () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const pos = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                    };
                    new google.maps.marker.AdvancedMarkerElement({
                        map: map,
                        position: pos,
                        title: "내 위치",
                    });
                    map.setCenter(pos);
                    map.setZoom(14);
                },
                () => { alert("위치 정보를 가져올 수 없습니다."); }
            );
        } else {
            alert("브라우저가 위치 정보를 지원하지 않습니다.");
        }
    });
    map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(locationButton);
}

function renderTop5Shrines(shrines) {
    const listContainer = document.getElementById('shrine-list');
    if (!listContainer) return;

    listContainer.innerHTML = ''; 
    const sortedShrines = [...shrines].sort((a, b) => new Date(b.published) - new Date(a.published));
    const top5 = sortedShrines.slice(0, 5);

    top5.forEach(shrine => {
        const categoryTag = shrine.categories && shrine.categories.length > 0 
            ? ` • <span>🏷️ ${shrine.categories[0]}</span>` 
            : '';

        const cardHTML = `
            <div class="shrine-card">
                <a href="${shrine.link}" target="_blank" class="card-thumb-link">
                    <img src="${shrine.thumbnail}" alt="${shrine.title}" class="card-thumb" loading="lazy">
                </a>
                <div class="card-content">
                    <h3 class="card-title">
                        <a href="${shrine.link}" target="_blank">${shrine.title}</a>
                    </h3>
                    <div class="card-meta">
                        <span>📅 ${shrine.published}</span>
                        ${categoryTag}
                    </div>
                    <p class="card-summary">${shrine.summary}</p>
                    <a href="${shrine.link}" target="_blank" class="card-btn">더 보기 →</a>
                </div>
            </div>
        `;
        listContainer.insertAdjacentHTML('beforeend', cardHTML);
    });
}

function setupFilterButtons() {
    const buttons = document.querySelectorAll('.theme-button');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const selectedTheme = btn.getAttribute('data-theme');
            filterMapMarkers(selectedTheme);
        });
    });
}

/* --------------------------------------
   오미쿠지 (운세 뽑기) 로직
-------------------------------------- */

// 1. 운세 데이터 정의 (결과에 따라 지도 필터 연동)
const omikujiResults = [
    { 
        title: "대길 (大吉)", 
        desc: "금전운이 폭발하는 날입니다!💰<br>지금 당장 복권이라도 사야 할 기세!", 
        theme: "wealth", 
        btnText: "💰 재물운 신사 지도 보기",
        color: "#FBC02D"
    },
    { 
        title: "중길 (中吉)", 
        desc: "마음이 설레는 인연이 다가옵니다.💘<br>사랑을 쟁취할 준비 되셨나요?", 
        theme: "love", 
        btnText: "💘 연애운 신사 지도 보기",
        color: "#E91E63"
    },
    { 
        title: "소길 (小吉)", 
        desc: "건강이 최고입니다.🌿<br>몸과 마음을 힐링하는 시간이 필요해요.", 
        theme: "health", 
        btnText: "🌿 건강기원 신사 지도 보기",
        color: "#2E7D32"
    },
    { 
        title: "길 (吉)", 
        desc: "노력한 만큼 성과가 나오는 날!📚<br>학업이나 승진에 좋은 기운이 있어요.", 
        theme: "study", 
        btnText: "🎓 학업/성공 신사 지도 보기",
        color: "#1565C0"
    },
    { 
        title: "흉 (凶)", 
        desc: "조금 조심해야 할 시기입니다.🚧<br>신사에서 액운을 씻어내고 보호받으세요!", 
        theme: "safety", 
        btnText: "🛡️ 액막이/안전 신사 지도 보기",
        color: "#455A64"
    }
];

// 2. 이벤트 리스너 설정
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('omikuji-modal');
    const openBtn = document.getElementById('omikuji-btn');
    const closeBtn = document.querySelector('.close-modal');
    const drawBtn = document.getElementById('draw-btn');
    const step1 = document.getElementById('omikuji-step1');
    const step2 = document.getElementById('omikuji-step2');
    const boxImg = document.getElementById('shaking-box');

    // 모달 열기
    openBtn.addEventListener('click', () => {
        modal.style.display = 'flex';
        step1.style.display = 'block';
        step2.style.display = 'none';
        boxImg.classList.remove('shake'); // 흔들림 초기화
    });

    // 모달 닫기
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // 배경 클릭 시 닫기
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // [핵심] 운세 뽑기 버튼 클릭
    drawBtn.addEventListener('click', () => {
        // 1. 흔들리는 애니메이션 시작
        boxImg.classList.add('shake');
        
        // 2. 1초 뒤에 결과 보여주기
        setTimeout(() => {
            boxImg.classList.remove('shake');
            
            // 랜덤 뽑기 로직
            const randomResult = omikujiResults[Math.floor(Math.random() * omikujiResults.length)];
            
            // 결과 화면 구성
            document.getElementById('result-title').textContent = randomResult.title;
            document.getElementById('result-title').style.color = randomResult.color;
            document.getElementById('result-desc').innerHTML = randomResult.desc;
            
            const goMapBtn = document.getElementById('go-map-btn');
            goMapBtn.textContent = randomResult.btnText;
            goMapBtn.style.backgroundColor = randomResult.color;
            
            // 버튼 클릭 시 해당 필터 적용
            goMapBtn.onclick = () => {
                // 1. 상단 필터 버튼 UI 업데이트
                const buttons = document.querySelectorAll('.theme-button');
                buttons.forEach(b => {
                    b.classList.remove('active');
                    if(b.getAttribute('data-theme') === randomResult.theme) {
                        b.classList.add('active');
                    }
                });
                
                // 2. 지도 마커 필터링 실행
                filterMapMarkers(randomResult.theme);
                
                // 3. 모달 닫기
                modal.style.display = 'none';

                // 4. (선택사항) 알림 띄우기
                alert(`"${randomResult.title}"이 나와서 [${randomResult.btnText}] 테마를 적용했습니다!`);
            };

            // 화면 전환
            step1.style.display = 'none';
            step2.style.display = 'block';
            
        }, 1000); // 1초 딜레이
    });
});