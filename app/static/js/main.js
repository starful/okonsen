// main.js - JinjaMap Core Logic (Fixed for Scope Issues)

let shrinesData = [];
let map;
let markers = [];
let currentInfoWindow = null;
let isMapLoaded = false; // 지도 로딩 상태

document.addEventListener('DOMContentLoaded', () => {
    fetchShrines();
    initThemeFilters();
    initSearch();
    initOmikuji();
});

// [1] Fetch Data
async function fetchShrines() {
    try {
        const response = await fetch('/api/shrines');
        const data = await response.json();
        
        // 최신순 정렬
        shrinesData = data.shrines.sort((a, b) => 
            new Date(b.published) - new Date(a.published)
        );

        // 상단 정보 업데이트
        if (data.last_updated) {
            const dateEl = document.getElementById('last-updated-date');
            if(dateEl) dateEl.textContent = data.last_updated;
        }
        if (data.shrines) {
            const totalEl = document.getElementById('total-shrines');
            if(totalEl) totalEl.textContent = data.shrines.length;
        }

        updateCategoryCounts();
        renderCards(shrinesData);

        // 만약 지도가 이미 로드된 상태라면 마커를 찍음
        if (isMapLoaded) {
            updateMapMarkers(shrinesData);
        }

    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// [2] Google Maps Initialization
// 모듈 스코프 밖인 window 객체에 initMap을 강제로 할당하여 
// HTML의 &callback=initMap 파라미터가 이 함수를 찾을 수 있게 합니다.
window.initMap = async function() {
    const mapEl = document.getElementById('map');
    if (!mapEl) return;

    try {
        // Dynamic Library Import 사용
        const { Map } = await google.maps.importLibrary("maps");
        const center = { lat: 35.6895, lng: 139.6917 }; // 도쿄 중심

        map = new Map(mapEl, {
            zoom: 11,
            center: center,
            mapId: "DEMO_MAP_ID", // 실제 프로덕션용 Map ID가 있다면 교체 필요
            disableDefaultUI: false,
            zoomControl: true,
            streetViewControl: false
        });

        isMapLoaded = true; // 지도 로딩 완료 플래그

        // 데이터가 먼저 로드되어 대기 중이라면 마커를 바로 찍음
        if (shrinesData.length > 0) {
            updateMapMarkers(shrinesData);
        }

    } catch (error) {
        console.error("Map Init Error:", error);
    }
};

// [3] Update Markers (AdvancedMarkerElement 사용)
async function updateMapMarkers(data) {
    if (!map) return; // 지도가 없으면 중단

    // 기존 마커 삭제
    markers.forEach(m => m.map = null);
    markers = [];

    try {
        const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

        data.forEach(shrine => {
            // 커스텀 마커 아이콘 생성
            const markerIcon = document.createElement('div');
            markerIcon.className = 'marker-icon';
            if (shrine.thumbnail) {
                markerIcon.style.backgroundImage = `url(${shrine.thumbnail})`;
                markerIcon.style.backgroundSize = 'cover';
            }

            // 마커 생성
            const marker = new AdvancedMarkerElement({
                map: map,
                position: { lat: parseFloat(shrine.lat), lng: parseFloat(shrine.lng) },
                title: shrine.title,
                content: markerIcon
            });

            // 마커 클릭 이벤트 (Info Window)
            marker.addListener('click', () => {
                if (currentInfoWindow) currentInfoWindow.close();

                const infoContent = `
                    <div class="infowindow-content">
                        <img src="${shrine.thumbnail}" alt="${shrine.title}" loading="lazy">
                        <h3>${shrine.title}</h3>
                        <p>📍 ${shrine.address}</p>
                        <div class="info-btn-group">
                            <a href="${shrine.link}" class="info-btn blog-btn">View Guide</a>
                            <a href="https://www.google.com/maps/dir/?api=1&destination=${shrine.lat},${shrine.lng}" target="_blank" class="info-btn dir-btn">Directions</a>
                        </div>
                    </div>
                `;
                
                // InfoWindow는 아직 레거시 방식을 사용할 수 있으나, importLibrary로 가져올 수도 있음.
                // 편의상 전역 google 객체 사용 (이미 로드됨 보장)
                const infoWindow = new google.maps.InfoWindow({ content: infoContent });
                infoWindow.open(map, marker);
                currentInfoWindow = infoWindow;
            });
            markers.push(marker);
        });
    } catch (e) {
        console.error("Marker Error:", e);
    }
}

// [4] Category Counts
function updateCategoryCounts() {
    const counts = { all: shrinesData.length, wealth: 0, love: 0, health: 0, study: 0, safety: 0, success: 0, history: 0 };
    
    shrinesData.forEach(shrine => {
        if(shrine.categories) {
            shrine.categories.forEach(cat => {
                const key = cat.toLowerCase();
                if (counts.hasOwnProperty(key)) counts[key]++;
            });
        }
    });

    for (const [key, value] of Object.entries(counts)) {
        const badge = document.getElementById(`count-${key}`);
        if (badge) badge.textContent = value;
    }
}

// [5] Render Cards
function renderCards(data) {
    const listContainer = document.getElementById('shrine-list');
    if(!listContainer) return;

    listContainer.innerHTML = '';
    
    if (data.length === 0) {
        listContainer.innerHTML = '<p style="text-align:center; width:100%; color:#666; margin-top:30px;">No shrines found matching your criteria.</p>';
        return;
    }

    data.forEach(shrine => {
        // NEW 뱃지 계산 (7일 이내)
        const pubDate = new Date(shrine.published);
        const now = new Date();
        const diffDays = Math.ceil((now - pubDate) / (1000 * 60 * 60 * 24));
        const isNew = diffDays <= 7;

        const card = document.createElement('div');
        card.className = 'shrine-card';
        card.innerHTML = `
            <a href="${shrine.link}" class="card-thumb-link">
                ${isNew ? '<span class="new-badge">NEW</span>' : ''}
                <img src="${shrine.thumbnail}" alt="${shrine.title}" class="card-thumb" loading="lazy">
            </a>
            <div class="card-content">
                <div class="card-meta">
                    <span>${shrine.categories.join(', ')}</span> • <span>${shrine.published}</span>
                </div>
                <h3 class="card-title"><a href="${shrine.link}">${shrine.title}</a></h3>
                <p class="card-summary">${shrine.summary}</p>
                <div class="card-footer">
                    <a href="${shrine.link}" class="card-btn">Read More &rarr;</a>
                </div>
            </div>`;
        listContainer.appendChild(card);
    });
}

// [6] Search & Filter Logic
function initSearch() {
    const searchInput = document.getElementById('search-input'); // HTML에 검색창이 있다면 사용
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            filterData(e.target.value.toLowerCase(), getCurrentTheme());
        });
    }
}

function initThemeFilters() {
    const buttons = document.querySelectorAll('.theme-button');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            // 버튼 활성화 스타일 변경
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // 필터링 실행
            filterData('', btn.dataset.theme);
        });
    });
}

function getCurrentTheme() {
    const activeBtn = document.querySelector('.theme-button.active');
    return activeBtn ? activeBtn.dataset.theme : 'all';
}

function filterData(keyword, theme) {
    let filtered = shrinesData;

    // 테마 필터링
    if (theme !== 'all') {
        filtered = filtered.filter(item => 
            item.categories.some(cat => cat.toLowerCase() === theme.toLowerCase())
        );
    }

    // 키워드 검색 (제목, 주소, 태그)
    if (keyword) {
        filtered = filtered.filter(item => 
            item.title.toLowerCase().includes(keyword) || 
            item.address.toLowerCase().includes(keyword) || 
            (item.tags && item.tags.some(tag => tag.toLowerCase().includes(keyword)))
        );
    }

    renderCards(filtered);
    updateMapMarkers(filtered);
}

// [7] Omikuji (Fortune) Logic
function initOmikuji() {
    const btn = document.getElementById('omikuji-btn');
    const modal = document.getElementById('omikuji-modal');
    const close = document.querySelector('.close-modal');
    const drawBtn = document.getElementById('draw-btn');
    const step1 = document.getElementById('omikuji-step1');
    const step2 = document.getElementById('omikuji-step2');
    
    if(!btn) return;

    btn.addEventListener('click', () => { 
        modal.style.display = 'flex'; 
        step1.style.display = 'block'; 
        step2.style.display = 'none'; 
    });

    // 모달 닫기
    close.addEventListener('click', () => { modal.style.display = 'none'; });
    window.addEventListener('click', (e) => { if (e.target === modal) modal.style.display = 'none'; });

    drawBtn.addEventListener('click', () => {
        const box = document.getElementById('shaking-box');
        box.style.animation = 'shake 0.5s infinite';
        
        setTimeout(() => { 
            box.style.animation = 'none'; 
            showResult(); 
        }, 1500);
    });

    function showResult() {
        if (shrinesData.length === 0) return;

        // 랜덤 신사 및 운세 추천
        const randomShrine = shrinesData[Math.floor(Math.random() * shrinesData.length)];
        const fortuneTypes = ['Great Blessing (Dai-kichi)', 'Blessing (Kichi)', 'Middle Blessing (Chu-kichi)', 'Small Blessing (Sho-kichi)'];
        const randomFortune = fortuneTypes[Math.floor(Math.random() * fortuneTypes.length)];

        step1.style.display = 'none'; 
        step2.style.display = 'block';
        
        document.getElementById('result-title').innerText = randomFortune;
        document.getElementById('result-desc').innerText = `Your lucky spot is:\n${randomShrine.title}`;
        
        const goBtn = document.getElementById('go-map-btn');
        goBtn.innerText = "Go to Shrine";
        goBtn.onclick = () => { window.location.href = randomShrine.link; };

        // 폭죽 효과 (라이브러리 로드 시)
        if (typeof confetti === 'function') {
            confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
        }
    }
}

// 오미쿠지 흔들림 애니메이션 주입
const style = document.createElement('style');
style.innerHTML = `@keyframes shake { 0% { transform: translate(1px, 1px) rotate(0deg); } 10% { transform: translate(-1px, -2px) rotate(-1deg); } 20% { transform: translate(-3px, 0px) rotate(1deg); } 30% { transform: translate(3px, 2px) rotate(0deg); } 40% { transform: translate(1px, -1px) rotate(1deg); } 50% { transform: translate(-1px, 2px) rotate(-1deg); } 60% { transform: translate(-3px, 1px) rotate(0deg); } 70% { transform: translate(3px, 1px) rotate(-1deg); } 80% { transform: translate(-1px, -1px) rotate(1deg); } 90% { transform: translate(1px, 2px) rotate(0deg); } 100% { transform: translate(1px, -2px) rotate(-1deg); } }`;
document.head.appendChild(style);