# app.py
from flask import Flask, jsonify, send_from_directory
from google.cloud import storage
import json
import os

# 정적 파일 경로 설정
app = Flask(__name__, static_url_path='/assets', static_folder='assets', template_folder='.')

# [중요] 버킷 이름은 cache_warmer.py(makeMapJson.py)와 동일해야 합니다.
# 로그를 보니 gs://jinjamap-data 에 저장 성공하셨으므로 그대로 둡니다.
BUCKET_NAME = "jinjamap-data" 
FILE_NAME = "shrines_data.json"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/shrines')
def api_shrines():
    try:
        # GCS 버킷에서 JSON 파일 읽기
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(FILE_NAME)
        
        data = blob.download_as_text()
        return jsonify(json.loads(data))
    except Exception as e:
        print(f"데이터 로드 실패: {e}")
        # 파일이 없거나 읽기 실패 시 빈 배열 반환
        return jsonify([]), 200

# [수정] 따옴표 오류 수정 (__main__ 앞뒤 따옴표 일치)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)