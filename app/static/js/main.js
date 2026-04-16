let map;
let allOnsens = [];
let markers = [];
const currentLang = new URLSearchParams(window.location.search).get('lang') || 'en';

const CATEGORY_MAP = {
    '가족탕': 'private', 'Private Bath': 'private',
    '타투 허용': 'tattoo', 'Tattoo OK': 'tattoo',
    '절경': 'view', 'Great View': 'view',
    '고급 료칸': 'luxury', 'Luxury': 'luxury',
    '로컬': 'local', 'Local': 'local'
};

async function initPage() {
    try {
        // 💡 주소 뒤에 ?t=시간값을 붙여서 캐시를 강제로 무효화합니다.
        const cacheBuster = new Date().getTime();
        const response = await fetch(`/api/onsens?lang=${currentLang}&v=${cacheBuster}`);
        const data = await response.json();
        
        // 풋터 업데이트 (데이터가 잘 왔는지 확인용)
        console.log("데이터 업데이트 날짜:", data.last_updated);
        
        allOnsens = data.onsens;
        updateFilterStats();
        renderList('all');
        initMap();

    } catch (error) {
        console.error("❌ 데이터 로드 실패:", error);
    }
}

function initMap() {
    const mapContainer = document.getElementById("map");
    if (!mapContainer || !window.google) return;

    // 지도 생성 (AdvancedMarker를 위해 mapId 권장)
    map = new google.maps.Map(mapContainer, {
        center: { lat: 36.5, lng: 138.0 },
        zoom: 6,
        mapId: "OKONSEN_MAP_ID", 
    });

    // 지도 로드 직후 마커 표시
    renderMarkers('all');
}

function renderList(theme) {
    const listContainer = document.getElementById('onsen-list');
    if (!listContainer) return;
    listContainer.innerHTML = '';

    const filtered = allOnsens.filter(onsen => {
        if (theme === 'all') return true;
        return onsen.categories.some(cat => CATEGORY_MAP[cat] === theme);
    });

    // main.js 내의 renderList 함수 부분 수정
    filtered.forEach(onsen => {
        const card = document.createElement('div');
        card.className = 'onsen-card';
        card.innerHTML = `
            <a href="${onsen.link}?lang=${currentLang}">
                <img src="${onsen.thumbnail}" 
                    class="card-thumb" 
                    alt="${onsen.title}" 
                    onerror="this.onerror=null; this.src='https://storage.googleapis.com/ok-project-assets/okonsen/default.png';">
                <div class="card-content">
                    <div class="card-meta">📍 ${onsen.address}</div>
                    <h3 class="card-title">${onsen.title}</h3>
                    <p class="card-summary">${onsen.summary.substring(0, 100)}...</p>
                    <div style="margin-top:10px;">
                        ${onsen.categories.map(c => `<span class="count-badge">${c}</span>`).join(' ')}
                    </div>
                </div>
            </a>
        `;
        listContainer.appendChild(card);
    });
}

function renderMarkers(theme) {
    if (!map || !google.maps.marker) return;

    // 기존 마커 제거
    markers.forEach(m => m.map = null);
    markers = [];

    const filtered = allOnsens.filter(onsen => {
        if (theme === 'all') return true;
        return onsen.categories.some(cat => CATEGORY_MAP[cat] === theme);
    });

    filtered.forEach(onsen => {
        const markerTag = document.createElement('div');
        markerTag.className = 'marker-icon';
        markerTag.style.backgroundImage = `url(${onsen.thumbnail})`;

        // AdvancedMarkerElement 사용
        const marker = new google.maps.marker.AdvancedMarkerElement({
            map: map,
            position: { lat: parseFloat(onsen.lat), lng: parseFloat(onsen.lng) },
            title: onsen.title,
            content: markerTag
        });

        marker.addListener('click', () => {
            window.location.href = `${onsen.link}?lang=${currentLang}`;
        });

        markers.push(marker);
    });
}

function setupFilters() {
    const buttons = document.querySelectorAll('.theme-button');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const theme = btn.dataset.theme;
            renderList(theme);
            renderMarkers(theme);
        });
    });
}

function updateFilterStats() {
    const counts = { all: allOnsens.length, private: 0, tattoo: 0, view: 0, luxury: 0, local: 0 };
    allOnsens.forEach(o => {
        const uniqueThemesInOnsen = new Set();
        o.categories.forEach(cat => {
            const key = CATEGORY_MAP[cat];
            if (key) uniqueThemesInOnsen.add(key);
        });
        uniqueThemesInOnsen.forEach(t => counts[t]++);
    });

    Object.keys(counts).forEach(key => {
        const el = document.getElementById(`count-${key}`);
        if (el) el.innerText = counts[key];
    });
}

// 초기 실행
document.addEventListener('DOMContentLoaded', () => {
    initPage();
    setupFilters();
});