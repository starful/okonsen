// main.js - JinjaMap Core Logic

let shrinesData = [];
let map;
let markers = [];
let currentInfoWindow = null;
let isMapLoaded = false;

document.addEventListener('DOMContentLoaded', () => {
    fetchShrines();
    initThemeFilters();
    // initSearch(); // 검색 기능이 UI에 없으므로 주석 처리 또는 삭제 가능
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

        // 지도 로드 후 데이터가 오면 마커 표시 및 뷰 조정
        if (isMapLoaded) {
            updateMapMarkers(shrinesData);
        }

    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// [2] Google Maps Initialization
window.initMap = async function() {
    const mapEl = document.getElementById('map');
    if (!mapEl) return;

    try {
        const { Map } = await google.maps.importLibrary("maps");
        const center = { lat: 36.2048, lng: 138.2529 }; // 일본 중심부

        map = new Map(mapEl, {
            zoom: 5,
            center: center,
            // mapId: "DEMO_MAP_ID", // 실제 Map ID로 교체하시는 것을 권장합니다.
            disableDefaultUI: false,
            zoomControl: true,
            streetViewControl: false,
            mapTypeControl: false, // 지도/위성 버튼 비활성화
        });

        isMapLoaded = true;

        // 데이터가 이미 로드되었다면 마커 업데이트
        if (shrinesData.length > 0) {
            updateMapMarkers(shrinesData);
        }

    } catch (error) {
        console.error("Map Init Error:", error);
    }
};

// [3] Update Markers
async function updateMapMarkers(data) {
    if (!map) return;

    // 기존 마커 삭제
    markers.forEach(m => m.map = null);
    markers = [];
    
    // [수정] 데이터가 없으면 함수 종료
    if (data.length === 0) {
        return;
    }

    // [추가] 모든 마커를 포함할 경계(bounds) 객체 생성
    const bounds = new google.maps.LatLngBounds();

    try {
        const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
        const { InfoWindow } = await google.maps.importLibrary("maps");

        data.forEach(shrine => {
            const position = { lat: parseFloat(shrine.lat), lng: parseFloat(shrine.lng) };

            const markerIcon = document.createElement('div');
            markerIcon.className = 'marker-icon';
            // 썸네일 이미지를 마커 배경으로 사용하지 않도록 수정 (기본 아이콘 사용)
            // if (shrine.thumbnail) {
            //     markerIcon.style.backgroundImage = `url(${shrine.thumbnail})`;
            //     markerIcon.style.backgroundSize = 'cover';
            // }

            const marker = new AdvancedMarkerElement({
                map: map,
                position: position,
                title: shrine.title,
                content: markerIcon
            });

            marker.addListener('click', () => {
                if (currentInfoWindow) currentInfoWindow.close();

                const onsenTag = shrine.has_onsen 
                    ? '<span class="info-onsen-tag">♨️ Onsen Nearby</span>' 
                    : '';

                const infoContent = `
                    <div class="infowindow-content">
                        <div style="position:relative;">
                            <img src="${shrine.thumbnail}" alt="${shrine.title}" loading="lazy">
                            ${onsenTag}
                        </div>
                        <h3>${shrine.title}</h3>
                        <p>📍 ${shrine.address}</p>
                        <div class="info-btn-group">
                            <a href="${shrine.link}" class="info-btn blog-btn">View Guide</a>
                            <a href="https://www.google.com/maps/dir/?api=1&destination=${shrine.lat},${shrine.lng}" target="_blank" class="info-btn dir-btn">Directions</a>
                        </div>
                    </div>
                `;
                
                const infoWindow = new InfoWindow({ content: infoContent, maxWidth: 250 });
                infoWindow.open(map, marker);
                currentInfoWindow = infoWindow;
            });
            markers.push(marker);

            // [추가] 생성된 마커의 위치를 bounds에 포함
            bounds.extend(position);
        });

        // [추가] 모든 마커가 보이도록 지도의 중심과 줌 레벨을 자동으로 조절
        map.fitBounds(bounds);

    } catch (e) {
        console.error("Marker Error:", e);
    }
}

// [4] Category Counts
function updateCategoryCounts() {
    const counts = { all: shrinesData.length, wealth: 0, love: 0, health: 0, safety: 0, success: 0, history: 0 };
    
    shrinesData.forEach(shrine => {
        if(shrine.categories) {
            // 카테고리 이름의 대소문자 통일 (예: "Success"와 "success"를 동일하게 처리)
            shrine.categories.forEach(cat => {
                const key = cat.toLowerCase().trim();
                if (counts.hasOwnProperty(key)) {
                    counts[key]++;
                }
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
        const pubDate = new Date(shrine.published);
        const now = new Date();
        const diffDays = Math.ceil((now - pubDate) / (1000 * 60 * 60 * 24));
        const isNew = diffDays <= 14; // NEW 뱃지 표시 기간을 14일로 늘림

        const onsenBadge = shrine.has_onsen 
            ? '<span class="onsen-badge">♨️ Onsen</span>' 
            : '';

        const card = document.createElement('div');
        card.className = 'shrine-card';
        card.innerHTML = `
            <a href="${shrine.link}" class="card-thumb-link">
                ${isNew ? '<span class="new-badge">NEW</span>' : ''}
                ${onsenBadge}
                <img src="${shrine.thumbnail}" alt="${shrine.title}" class="card-thumb" loading="lazy">
            </a>
            <div class="card-content">
                <div class="card-meta">
                    <span>${shrine.categories.join(', ')}</span> • <span>${shrine.published.replace(/-/g, '.')}</span>
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

// [6] Filter Logic
// 검색 기능이 없으므로 initSearch()는 제거하고 필터 기능만 남깁니다.
function initThemeFilters() {
    const buttons = document.querySelectorAll('.theme-button');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterByTheme(btn.dataset.theme);
        });
    });
}

function filterByTheme(theme) {
    let filtered = shrinesData;

    if (theme !== 'all') {
        filtered = filtered.filter(item => 
            item.categories.some(cat => cat.toLowerCase().trim() === theme.toLowerCase())
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
    
    if(!btn || !modal || !close || !drawBtn || !step1 || !step2) return;

    btn.addEventListener('click', () => { 
        modal.style.display = 'flex'; 
        step1.style.display = 'block'; 
        step2.style.display = 'none'; 
    });

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

        const randomShrine = shrinesData[Math.floor(Math.random() * shrinesData.length)];
        const fortuneTypes = ['Great Blessing (Dai-kichi)', 'Blessing (Kichi)', 'Middle Blessing (Chu-kichi)', 'Small Blessing (Sho-kichi)'];
        const randomFortune = fortuneTypes[Math.floor(Math.random() * fortuneTypes.length)];

        step1.style.display = 'none'; 
        step2.style.display = 'block';
        
        document.getElementById('result-title').innerText = randomFortune;
        document.getElementById('result-desc').innerText = `Your lucky spot is:\n${randomShrine.title}`;
        
        const goBtn = document.getElementById('go-map-btn');
        goBtn.innerText = `Explore ${randomShrine.categories[0] || 'Shrine'}`;
        goBtn.onclick = () => { window.location.href = randomShrine.link; };

        if (typeof confetti === 'function') {
            confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
        }
    }
}

// 쉐이킹 애니메이션을 위한 스타일 동적 추가
const style = document.createElement('style');
style.innerHTML = `@keyframes shake { 0% { transform: translate(1px, 1px) rotate(0deg); } 10% { transform: translate(-1px, -2px) rotate(-1deg); } 20% { transform: translate(-3px, 0px) rotate(1deg); } 30% { transform: translate(3px, 2px) rotate(0deg); } 40% { transform: translate(1px, -1px) rotate(1deg); } 50% { transform: translate(-1px, 2px) rotate(-1deg); } 60% { transform: translate(-3px, 1px) rotate(0deg); } 70% { transform: translate(3px, 1px) rotate(-1deg); } 80% { transform: translate(-1px, -1px) rotate(1deg); } 90% { transform: translate(1px, 2px) rotate(0deg); } 100% { transform: translate(1px, -2px) rotate(-1deg); } }`;
document.head.appendChild(style);