#!/bin/bash
# ♨️ OKOnsen 자동 배포 파이프라인 (컨텐츠 + 가이드 + 이미지 수집)
# 실행: ./deploy.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
COMMIT_MSG="update: auto-generated contents and guides $(date '+%Y-%m-%d %H:%M')"

print_step() {
    echo ""
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}
print_ok()   { echo -e "${GREEN}  ✅ $1${NC}"; }
print_warn() { echo -e "${YELLOW}  ⚠️  $1${NC}"; }
print_err()  { echo -e "${RED}  ❌ $1${NC}"; }
print_info() { echo -e "  ℹ️  $1"; }

clear
echo ""
echo -e "${BOLD}${CYAN}  ♨️  OKOnsen 자동 배포 파이프라인${NC}"
echo -e "  $(date '+%Y년 %m월 %d일 %H:%M:%S') 시작"
echo ""

START_TIME=$SECONDS

# ==========================================
# STEP 0: 환경 체크
# ==========================================
print_step "STEP 0 / 5  |  환경 체크"

cd "$PROJECT_ROOT"
print_info "프로젝트 경로: $PROJECT_ROOT"

if [ ! -f ".env" ]; then
    print_err ".env 파일이 없습니다."; exit 1
fi
print_ok ".env 파일 확인"

if ! grep -q "GEMINI_API_KEY" .env; then
    print_err "GEMINI_API_KEY가 없습니다."; exit 1
fi
print_ok "Gemini API 키 확인"

# CSV 파일들 체크
ONSEN_CSV="script/csv/onsens.csv"
GUIDE_CSV="script/csv/guides.csv"
[ ! -f "$ONSEN_CSV" ] && { print_err "온천 CSV 없음"; exit 1; }
[ ! -f "$GUIDE_CSV" ] && { print_err "가이드 CSV 없음"; exit 1; }
print_ok "CSV 데이터 파일 확인 완료"

# 명령어 체크
for cmd in python3 gcloud git; do
    if ! command -v $cmd &>/dev/null; then print_err "$cmd 없음"; exit 1; fi
done
print_ok "필수 도구(Python, GCloud, Git) 확인 완료"

# ==========================================
# STEP 1: AI 컨텐츠 및 가이드 생성
# ==========================================
print_step "STEP 1 / 5  |  AI 컨텐츠 생성 (Gemini API)"

CONTENT_DIR="app/content"
GUIDE_DIR="app/content/guides"

# 생성 전 카운트
BEFORE_ONSEN=$(find "$CONTENT_DIR" -maxdepth 1 -name "*.md" | wc -l | tr -d ' ')
BEFORE_GUIDE=$(find "$GUIDE_DIR" -name "*.md" | wc -l | tr -d ' ')

# 1. 온천 상세페이지 생성
print_info "온천 상세페이지 생성 중 (script/onsen_generator.py)..."
python3 script/onsen_generator.py

# 2. 가이드 블로그 포스트 생성 (새로 추가된 단계)
print_info "여행 가이드 포스트 생성 중 (script/guide_generator.py)..."
python3 script/guide_generator.py

# 생성 후 카운트
AFTER_ONSEN=$(find "$CONTENT_DIR" -maxdepth 1 -name "*.md" | wc -l | tr -d ' ')
AFTER_GUIDE=$(find "$GUIDE_DIR" -name "*.md" | wc -l | tr -d ' ')

NEW_ONSEN=$(( AFTER_ONSEN - BEFORE_ONSEN ))
NEW_GUIDE=$(( AFTER_GUIDE - BEFORE_GUIDE ))
TOTAL_NEW=$(( NEW_ONSEN + NEW_GUIDE ))

print_ok "컨텐츠 생성 완료! (신규: 온천 ${NEW_ONSEN}개 / 가이드 ${NEW_GUIDE}개)"

# ==========================================
# STEP 2: 이미지 수집 및 최적화
# ==========================================
print_step "STEP 2 / 5  |  이미지 수집 및 최적화"

if ! grep -q "GOOGLE_PLACES_API_KEY" .env; then
    print_warn "GOOGLE_PLACES_API_KEY 없음 → 수집 건너뜁니다"
    MISSING=0
else
    # 이미지 존재 여부 체크 로직 (생략 가능하지만 기존 로직 유지)
    MISSING=0
    print_info "누락된 이미지 확인 및 수집 중..."
    python3 script/fetch_images.py
    
    print_info "이미지 최적화(Resize/Compress) 중..."
    python3 script/optimize_images.py
    print_ok "이미지 처리 완료"
fi

# 빌드 데이터 스크립트 실행 (JSON 갱신)
print_info "사이트 데이터 빌드 중 (build_data.py)..."
python3 script/build_data.py
print_ok "데이터 빌드 완료"

# 새로 생성된 것이 아무것도 없으면 확인
if [ "$TOTAL_NEW" -eq 0 ]; then
    print_warn "새로 생성된 컨텐츠나 가이드가 없습니다."
    echo ""
    read -p "  그래도 계속 배포하시겠습니까? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "배포를 취소했습니다."; exit 0
    fi
fi

# ==========================================
# STEP 3: Git Push
# ==========================================
print_step "STEP 3 / 5  |  GitHub Push"

GIT_STATUS=$(git status --porcelain)
if [ -z "$GIT_STATUS" ]; then
    print_warn "변경 사항이 없습니다."
else
    git add .
    git commit -m "$COMMIT_MSG"
    git push origin main
    print_ok "GitHub push 완료"
fi

# ==========================================
# STEP 4: Cloud Build & Cloud Run 배포
# ==========================================
print_step "STEP 4 / 5  |  Google Cloud 배포"
print_info "gcloud builds submit 실행 중 (약 3분 소요)..."

gcloud builds submit

print_ok "Cloud Run 배포 완료"

# ==========================================
# STEP 5: 완료 요약
# ==========================================
print_step "STEP 5 / 5  |  완료 요약"

ELAPSED=$(( SECONDS - START_TIME ))
MINUTES=$(( ELAPSED / 60 ))
SECS=$(( ELAPSED % 60 ))

echo ""
echo -e "${BOLD}${GREEN}  🎉 모든 공정이 성공적으로 완료되었습니다!${NC}"
echo ""
echo -e "  ⏱️  총 소요 시간  : ${MINUTES}분 ${SECS}초"
echo -e "  📄 신규 온천     : ${NEW_ONSEN}개"
echo -e "  📝 신규 가이드   : ${NEW_GUIDE}개"
echo -e "  🌐 라이브 사이트 : https://okonsen.net"
echo ""

# 맥 사용자라면 알림 발송
if command -v osascript &>/dev/null; then
    osascript -e 'display notification "가이드 및 온천 배포 완료! 🎉" with title "OKOnsen 파이프라인"' 2>/dev/null || true
fi

echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""