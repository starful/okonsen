window.initMap = async function() {
    const mapCenter = { lat: 35.681236, lng: 139.767125 };
    const map = new google.maps.Map(document.getElementById("map"), {
        zoom: 12, center: mapCenter, mapId: 'DEMO_MAP_ID', clickableIcons: false
    });

    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

    // 새로운 테마에 맞춘 색상 정의
    const themeColors = { 
        wealth: '#f1c40f',  // 재물 (금색)
        love: '#e74c3c',    // 사랑 (붉은색)
        health: '#2ecc71',  // 건강 (녹색)
        study: '#34495e',   // 학업 (남색)
        safety: '#e67e22',  // 안전 (주황색)
        family: '#ff79c6',  // 가정 (분홍색)
        success: '#3498db', // 성공 (파란색)
        art: '#9b59b6',     // 예술 (보라색)
        relax: '#1abc9c',   // 휴식 (청록색)
        history: '#a1887f'  // 역사 (갈색)
    };

    // 신사 데이터의 theme을 새로운 카테고리로 업데이트
    const shrines = [
        { position: { lat: 35.6764, lng: 139.6993 }, title: "메이지 신궁", description: "도심 속 거대한 숲", theme: "relax", detailPage: "shrine-meiji.html" },
        { position: { lat: 35.7148, lng: 139.7967 }, title: "아사쿠사 신사", description: "도쿄 최고(最古)의 역사", theme: "history", detailPage: "shrine-asakusa.html" },
        { position: { lat: 35.7022, lng: 139.7695 }, title: "칸다 묘진", description: "사업 번창과 IT의 수호신", theme: "wealth", detailPage: "shrine-kanda.html" },
        { position: { lat: 35.6999, lng: 139.7445 }, title: "도쿄 다이진구", description: "사랑과 인연을 맺어주는 신사", theme: "love", detailPage: "shrine-daizingu.html" },
        { position: { lat: 35.7229, lng: 139.7612 }, title: "네즈 신사", description: "아름다운 토리이 터널", theme: "love", detailPage: "shrine-nezu.html" },
        { position: { lat: 35.6784, lng: 139.7423 }, title: "히에 신사", description: "출세와 순산의 신", theme: "success", detailPage: "shrine-hie.html" }
    ];
    
    const infowindow = new google.maps.InfoWindow();
    let lastClickedMarker = null;
    const allMarkers = [];

    shrines.forEach(shrine => {
        const markerElement = document.createElement('div');
        markerElement.className = 'shrine-marker';
        markerElement.style.backgroundColor = themeColors[shrine.theme] || '#808080';

        const marker = new AdvancedMarkerElement({ map, position: shrine.position, title: shrine.title, content: markerElement, zIndex: 1 });
        
        marker.shrineData = shrine;
        allMarkers.push(marker);

        markerElement.addEventListener("click", () => {
            if (lastClickedMarker) lastClickedMarker.zIndex = 1;
            marker.zIndex = 999;
            lastClickedMarker = marker;
            const content = `<div class="infowindow-content"><h3>${shrine.title}</h3><p>${shrine.description}</p><a href="${shrine.detailPage}" target="_blank">자세히 보기 &raquo;</a></div>`;
            infowindow.setContent(content);
            infowindow.open(map, marker);
        });
    });

    google.maps.event.addListener(infowindow, 'closeclick', () => {
        if (lastClickedMarker) lastClickedMarker.zIndex = 1;
        lastClickedMarker = null;
    });

    function filterMarkers(selectedTheme) {
        allMarkers.forEach(marker => {
            if (selectedTheme === 'all' || marker.shrineData.theme === selectedTheme) {
                marker.map = map;
            } else {
                marker.map = null;
            }
        });
    }

    const filterButtons = document.querySelectorAll('.theme-button');
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            const theme = button.dataset.theme;
            filterMarkers(theme);
        });
    });
}