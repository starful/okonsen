#!/bin/bash
# ♨️ OKOnsen 자동 배포 파이프라인 (Safe Admin Sync 버전)
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
LOCAL_IMAGES="app/static/images"
COMMIT_MSG="update: auto-generated contents and synced to GCS $(date '+%Y-%m-%d %H:%M') (Safe Sync)"

print_step() {
    echo ""
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}
print_ok()   { echo -e "${GREEN}  ✅ $1${NC}"; }
print_info() { echo -e "  ℹ️  $1"; }

clear
echo -e "${BOLD}${CYAN}  ♨️  OKOnsen GCS 통합 배포 파이프라인 시작 (Safe Sync)${NC}"
START_TIME=$SECONDS

# STEP 0: 클라우드 이미지 동기화 (알바생 업로드 사진 가져오기)
print_step "STEP 0: 클라우드 이미지 역동기화"
mkdir -p "$LOCAL_IMAGES"
print_info "알바생이 올린 사진을 가져오는 중 ($GCS_BUCKET -> 로컬)..."
# 클라우드의 최신 상태를 로컬로 먼저 가져와서 로컬의 옛날 사진이 덮어쓰는 것을 방지합니다.
gcloud storage rsync "$GCS_BUCKET" "$LOCAL_IMAGES" --recursive
print_ok "클라우드 이미지 동기화 완료"

# STEP 1: AI 컨텐츠 및 가이드 생성
print_step "STEP 1: AI 컨텐츠 생성"
echo "📝 가이드 생성 중 (3개 제한)..."
python3 script/guide_generator.py
echo "♨️ 온천 상세페이지 생성 중..."
python3 script/onsen_generator.py
print_ok "컨텐츠 생성 완료"

# STEP 2: 이미지 처리 및 GCS 동기화
print_step "STEP 2: 이미지 수집 및 최적화"
# fetch_images.py가 돌아갈 때, STEP 0에서 가져온 사진이 이미 있으면 새로 생성하지 않습니다.
python3 script/fetch_images.py
python3 script/optimize_images.py

print_info "최종 이미지 버킷 동기화 중..."
gcloud storage rsync "$LOCAL_IMAGES" "$GCS_BUCKET" --recursive --checksum

# 공개 읽기 권한 일괄 부여 (필요 시)
gsutil -m acl ch -u AllUsers:R "$GCS_BUCKET/**" &>/dev/null || true
print_ok "이미지 GCS 업로드 완료"

# STEP 3: 데이터 빌드
print_step "STEP 3: 데이터 빌드"
python3 script/build_data.py
print_ok "데이터 빌드(JSON + Sitemap) 완료"

# STEP 4: Git Push
print_step "STEP 4: GitHub 업데이트"
git add .
# 변경사항이 있을 때만 커밋
if ! git diff-index --quiet HEAD --; then
    git commit -m "$COMMIT_MSG"
    git push origin main
    print_ok "Git 업데이트 완료 (최신 사진 정보 포함)"
else
    print_info "변경 사항 없음 -> Git Push 건너뜀"
fi

# STEP 5: Cloud Build 배포
print_step "STEP 5: Google Cloud Run 배포"
gcloud builds submit --project starful-258005
print_ok "Cloud Run 배포 완료"

ELAPSED=$(( SECONDS - START_TIME ))
echo -e "\n${BOLD}${GREEN} 🎉 모든 배포 공정이 성공적으로 완료되었습니다!${NC}"
echo -e "  ⏱️  총 소요시간: $((ELAPSED/60))분 $((ELAPSED%60))초"
echo -e "  🌐 라이브 주소: https://okonsen.net\n"