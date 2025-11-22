# cache_warmer.py
import os
import json
import googlemaps
from google.cloud import storage
from hatena_client import get_all_posts

# 환경 변수 (Cloud Build에서 주입받음)
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY') # AIza... 키
BUCKET_NAME = "jinjamap-data" # [수정됨] 사용자 버킷 이름
FILE_NAME = "shrines_data.json"

def main():
    print("🔥 데이터 갱신 스크립트 시작...")

    # 1. 하테나 글 가져오기
    posts = get_all_posts()
    if not posts:
        print("❌ 글을 가져오지 못했습니다. 빈 데이터로 덮어쓰지 않고 종료합니다.")
        return

    print(f"📝 총 {len(posts)}개의 글을 처리합니다. (Geocoding 시작)")

    # 2. 좌표 변환 (서버 사이드)
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    processed_posts = []
    
    for post in posts:
        if not post.get('address'):
            continue
        
        try:
            geocode_result = gmaps.geocode(post['address'])
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                post['lat'] = location['lat']
                post['lng'] = location['lng']
                processed_posts.append(post)
                print(f"  ✅ 좌표 변환: {post['title']}")
            else:
                print(f"  ⚠️ 좌표 못 찾음: {post['title']}")
        except Exception as e:
            print(f"  ❌ 에러: {e}")

    # 3. Cloud Storage 저장
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(FILE_NAME)

        blob.upload_from_string(
            json.dumps(processed_posts, ensure_ascii=False),
            content_type='application/json'
        )
        print(f"💾 저장 완료: gs://{BUCKET_NAME}/{FILE_NAME}")
        print(f"🚀 총 {len(processed_posts)}개의 장소 업데이트 됨!")

    except Exception as e:
        print(f"❌ GCS 업로드 실패: {e}")
        # 배포 중단 (데이터 갱신 실패 시 배포도 안 되게 하려면 exit(1) 사용)
        exit(1)

if __name__ == "__main__":
    main()