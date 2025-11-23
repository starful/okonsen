// map.js
let map;
let markers = []; // 마커들을 담을 배열

// 1. 카테고리 매핑 (한글 태그 -> 영어 코드)
const categoryMap = {
    "재물": "wealth", "금전": "wealth", "사업": "wealth", "로또": "wealth",
    "사랑": "love", "연애": "love", "인연": "love", "결혼": "love",
    "건강": "health", "치유": "health", "장수": "health",
    "학업": "study", "합격": "study", "시험": "study",
    "안전": "safety", "교통안전": "safety", "액운": "safety",
    "성공": "success", "승진": "success", "목표": "success",
    "휴식": "relax", "힐링": "relax", "여행": "relax",
    "역사": "history", "전통": "history", "관광": "history"
};

// 2. 구글 맵 초기화
async function initMap() {
    console.log("Google Maps initMap 시작됨!");

    const { Map } = await google.maps.importLibrary("maps");
    const { AdvancedMarkerElement, PinElement } = await google.maps.importLibrary("marker");

    // [수정됨] 기본 중심 좌표 (도쿄 신주쿠/황거 주변)
    const initialCenter = { lat: 35.6895, lng: 139.6917 };

    map = new Map(document.getElementById("map"), {
        zoom: 12, // [수정됨] 10 -> 12 (도쿄 시내가 더 잘 보이도록 확대)
        center: initialCenter,
        mapId: "2938bb3f7f034d78a2dbaf56",
        mapTypeControl: false,
        streetViewControl: false,
        
        // [수정됨] '두 손가락' 안내 없이 한 손가락으로 이동 가능하게 변경
        gestureHandling: "greedy" 
    });

    fetchBlogPosts(AdvancedMarkerElement, PinElement);
    setupFilterButtons();
}

// 3. 데이터 가져오기
async function fetchBlogPosts(AdvancedMarkerElement, PinElement) {
    const API_ENDPOINT = "/api/shrines";
    try {
        const response = await fetch(API_ENDPOINT);
        const posts = await response.json();
        
        if (posts.length === 0) {
            console.log("데이터가 없습니다.");
            return;
        }

        processBlogData(posts, AdvancedMarkerElement, PinElement);
    } catch (error) {
        console.error("API 호출 실패:", error);
    }
}

// 4. 데이터 처리 및 마커 생성
function processBlogData(posts, AdvancedMarkerElement, PinElement) {
    // [수정됨] 초기화면이 너무 광범위해지는 것을 막기 위해 bounds 로직 주석 처리
    // const bounds = new google.maps.LatLngBounds(); 

    for (const post of posts) {
        if (post.lat && post.lng) {
            
            // 카테고리 결정 로직
            let matchedTheme = 'history'; 
            if (post.categories && post.categories.length > 0) {
                for (let cat of post.categories) {
                    if (categoryMap[cat]) {
                        matchedTheme = categoryMap[cat];
                        break;
                    }
                }
            }

            const shrineData = {
                name: post.title,
                lat: post.lat,
                lng: post.lng,
                theme: matchedTheme,
                link: post.link,
                address: post.address,
                thumbnail: post.thumbnail
            };

            createMarker(shrineData, AdvancedMarkerElement, PinElement);
            
            // [수정됨] bounds 확장 로직 제거
            // bounds.extend({ lat: post.lat, lng: post.lng });
        }
    }

    // [수정됨] fitBounds 제거 (이것 때문에 지도가 일본 전체로 줌아웃 되었습니다)
    // if (!bounds.isEmpty()) {
    //     map.fitBounds(bounds);
    // }
}

// 5. 마커 생성 함수
function createMarker(shrine, AdvancedMarkerElement, PinElement) {
    // 테마별 색상
    const colors = {
        wealth: "#FFD700",  // 재물
        love: "#FF4081",    // 사랑
        health: "#4CAF50",  // 건강
        study: "#2196F3",   // 학업
        safety: "#607D8B",  // 안전
        success: "#673AB7", // 성공
        relax: "#00BCD4",   // 휴식
        history: "#795548"  // 역사
    };
    
    const markerColor = colors[shrine.theme] || colors['history'];

    const pin = new PinElement({
        background: markerColor,
        borderColor: "#ffffff",
        glyphColor: "#ffffff"
    });

    const marker = new AdvancedMarkerElement({
        map: map,
        position: { lat: shrine.lat, lng: shrine.lng },
        title: shrine.name,
        content: pin.element
    });

    marker.category = shrine.theme; 

    const directionsUrl = `https://www.google.com/maps/dir/?api=1&destination=${shrine.lat},${shrine.lng}`;

    const contentString = `
        <div class="infowindow-content">
            <img src="${shrine.thumbnail}" 
                 alt="${shrine.name}" 
                 onerror="this.src='assets/images/JinjaMapLogo_Horizontal.png'">
            
            <h3>${shrine.name}</h3>
            <p style="font-size:12px; color:#666; margin-bottom:5px;">${shrine.address}</p>
            
            <p style="margin-bottom:8px;">
                <span style="display:inline-block; padding:2px 6px; background:${markerColor}; color:#fff; border-radius:10px; font-size:11px;">
                    ${getKoreanThemeName(shrine.theme)}
                </span>
            </p>

            <div style="display:flex; gap:5px;">
                <a href="${shrine.link}" target="_blank" style="flex:1; text-align:center; padding:6px 0; background:#333; color:#fff; text-decoration:none; border-radius:4px; font-size:12px;">블로그 보기</a>
                <a href="${directionsUrl}" target="_blank" style="flex:1; text-align:center; padding:6px 0; background:#4285F4; color:#fff; text-decoration:none; border-radius:4px; font-size:12px;">🗺️ 길찾기</a>
            </div>
        </div>
    `;

    const infowindow = new google.maps.InfoWindow({
        content: contentString
    });

    marker.addListener("click", () => {
        infowindow.open(map, marker);
    });

    markers.push(marker);
}

function getKoreanThemeName(theme) {
    const names = {
        wealth: "재물", love: "사랑", health: "건강",
        study: "학업", safety: "안전",
        success: "성공", relax: "휴식", history: "역사"
    };
    return names[theme] || "역사";
}

// 6. 필터 버튼 로직
function setupFilterButtons() {
    const buttons = document.querySelectorAll('.theme-button');
    buttons.forEach(button => {
        button.addEventListener('click', () => {
            buttons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            const selectedTheme = button.getAttribute('data-theme');
            
            markers.forEach(marker => {
                if (selectedTheme === 'all' || marker.category === selectedTheme) {
                    marker.map = map;
                } else {
                    marker.map = null;
                }
            });
        });
    });
}

window.initMap = initMap;