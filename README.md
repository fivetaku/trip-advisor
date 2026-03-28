# Trip Advisor — Claude Code 여행 가이드 스킬

> "부산 2박3일 코스 짜줘" 한 마디로 관광지, 맛집, 축제, 숙박 정보를 종합 정리해주는 Claude Code 스킬

공공데이터포털의 **TourAPI**(한국관광공사)와 **블로그 검색**을 결합하여 국내 여행 가이드를 자동 생성합니다.

---

## 주요 기능

- 전국 17개 시도 + 30개 주요 관광도시 지원
- 관광지 / 맛집 / 축제·행사 / 숙박 통합 검색
- 블로그 후기와 TourAPI 공식 데이터 교차 검증
- 일정 기반 여행 코스 추천 (1박2일, 2박3일 등)

---

## 설치

### 방법 1: 스킬 폴더에 직접 복사

```bash
# Claude Code 프로젝트의 스킬 폴더에 복사
git clone https://github.com/fivetaku/trip-advisor.git
cp -r trip-advisor/ your-project/.claude/skills/trip-advisor/
```

### 방법 2: .claude/skills 하위에 클론

```bash
cd your-project/.claude/skills/
git clone https://github.com/fivetaku/trip-advisor.git
```

---

## 초기 설정 (온보딩)

처음 한 번만 하면 됩니다. **스킬이 자동으로 안내**해주지만, 미리 하고 싶다면:

### 1. TourAPI 인증키 발급

1. [공공데이터포털 TourAPI 페이지](https://www.data.go.kr/data/15101578/openapi.do)에 접속 (회원가입/로그인 필요)
2. **"활용신청"** 버튼 클릭
3. 활용목적: "여행 정보 조회" (아무거나 입력 OK) → 동의 체크 → **"신청"**
4. 마이페이지 → 데이터활용 → 오픈API → 개발계정에서 **일반 인증키 (Encoding)** 복사

> 신청 후 자동 승인되며, 약 10분 뒤부터 사용 가능합니다.

### 2. .env 파일 생성

```bash
cp .env.example .env
```

`.env` 파일을 열고 발급받은 인증키를 입력:

```
TOURAPI_SERVICE_KEY=발급받은_인증키_붙여넣기
TOURAPI_NUM_OF_ROWS=10
```

> 또는 설정 없이 바로 사용해도 됩니다 — 스킬이 처음 실행될 때 발급 가이드를 보여주고, 키를 입력하면 .env 파일을 자동으로 만들어줍니다.

### 3. Python requests 라이브러리 확인

```bash
pip install requests
```

---

## 사용법

### 슬래시 커맨드 (추천)

```
/trip-advisor 부산 2박3일          → 부산 여행 가이드 생성
/trip-advisor 제주도 맛집          → 제주도 맛집 추천
/trip-advisor                      → 여행지를 물어본 후 생성
```

### 자연어로도 가능

```
"부산 2박3일 코스 짜줘"
"전주 맛집 추천해줘"
"강릉 가볼만한곳 알려줘"
"4월 부산 축제 뭐 있어?"
"경주 숙소 추천해줘"
"이번 주말 속초 여행 계획 세워줘"
```

### 실행 흐름

```
사용자: "부산 2박3일 여행 코스 짜줘"
    │
    ├─ [첫 실행] Step 0: 온보딩 → API 키 발급 안내 → 키 입력 → .env 생성
    │                          → 이어서 바로 검색 진행 ↓
    │
    ├─ Step 1: 지역(부산) + 기간(2박3일) 파싱
    ├─ Step 2: TourAPI 호출 (관광지 + 맛집 + 축제 + 숙박)
    ├─ Step 3: 블로그 후기 검색 + 교차 검증
    └─ Step 4: 종합 여행 가이드 출력
```

---

## 지원 지역

**17개 시도**: 서울, 인천, 대전, 대구, 광주, 부산, 울산, 세종, 경기, 강원, 충북, 충남, 경북, 경남, 전북, 전남, 제주

**30개+ 주요 관광도시**: 경주, 강릉, 속초, 전주, 여수, 통영, 제주시, 서귀포, 안동, 춘천, 평창, 담양, 목포, 남해 등

---

## 파일 구조

```
trip-advisor/
├── SKILL.md           ← 스킬 정의 (워크플로우 + 온보딩)
├── .env.example       ← 환경변수 템플릿
├── .gitignore         ← .env 보호
├── README.md          ← 이 파일
└── scripts/
    └── tour_api.py    ← TourAPI 호출 스크립트
```

---

## 라이선스

MIT
