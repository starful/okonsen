#!/bin/bash
# ♨️ OKOnsen 자동 배포 파이프라인 (GCS 이미지 서버 연동 풀 버전)
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
GCS_BUCKET="gs://ok-project-assets/okonsen"
COMMIT_MSG="update: auto-generated contents and synced to GCS $(date '+%Y-%m-%d %H:%M')"

print_step() {
    echo ""
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}
print_ok()   { echo -e "${GREEN}  ✅ $1${NC}"; }
print_info() { echo -e "  ℹ️  $1"; }

clear
echo -e "${BOLD}${CYAN}  ♨️  OKOnsen GCS 통합 배포 파이프라인 시작${NC}"
START_TIME=$SECONDS

# STEP 1: AI 컨텐츠 및 가이드 생성
print_step "STEP 1: AI 컨텐츠 생성"
echo "📝 가이드 생성 중 (3개 제한)..."
python3 script/guide_generator.py
echo "♨️ 온천 상세페이지 생성 중..."
python3 script/onsen_generator.py
print_ok "컨텐츠 생성 완료"

# STEP 2: 이미지 처리 및 GCS 동기화
print_step "STEP 2: 이미지 수집 및 GCS 동기화"
python3 script/fetch_images.py
python3 script/optimize_images.py

print_info "GCS 버킷으로 이미지 동기화 중 ($GCS_BUCKET)..."
gcloud storage rsync app/static/images "$GCS_BUCKET" --recursive --checksum

# 공개 읽기 권한 일괄 부여
gsutil -m acl ch -u AllUsers:R "$GCS_BUCKET/**" &>/dev/null || true
print_ok "이미지 GCS 업로드 및 권한 설정 완료"

# STEP 3: 데이터 빌드 (GCS 주소 및 사이트맵 반영)
print_step "STEP 3: 데이터 빌드"
python3 script/build_data.py
print_ok "데이터 빌드(JSON + Sitemap) 완료"

# STEP 4: Git Push
print_step "STEP 4: GitHub 업데이트"
git add .
git commit -m "$COMMIT_MSG" || echo "변경 사항 없음"
git push origin main
print_ok "Git 업데이트 완료"

# STEP 5: Cloud Build 배포
print_step "STEP 5: Google Cloud Run 배포"
gcloud builds submit
print_ok "Cloud Run 배포 완료"

ELAPSED=$(( SECONDS - START_TIME ))
echo -e "\n${BOLD}${GREEN} 🎉 모든 배포 공정이 성공적으로 완료되었습니다!${NC}"
echo -e "  ⏱️  총 소요시간: $((ELAPSED/60))분 $((ELAPSED%60))초"
echo -e "  🌐 라이브 주소: https://okonsen.net\n"