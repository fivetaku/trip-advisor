---
name: trip-advisor
description: This skill should be used when the user asks to "여행 코스 짜줘", "맛집 추천해줘", "관광지 알려줘", "축제 정보", "여행 가이드", "숙박 추천", "travel plan", "trip advisor", "여행지 추천", "주말에 어디 갈까", "여행 계획 세워줘". Make sure to use this skill whenever the user mentions travel planning, tourist information, restaurant recommendations, or festival searches for Korean destinations.
---

# Trip Advisor

> 지역명이나 자연어 요청 하나로 관광지, 맛집, 축제, 숙박 정보를 TourAPI + 블로그 검색으로 종합 정리하는 여행 가이드 스킬.

---

## 워크플로우

### Step 0: API 키 확인 (온보딩)
**타입**: script

스킬 실행 전, `${SKILL_DIR}/.env` 파일에 `TOURAPI_SERVICE_KEY`가 설정되어 있는지 확인한다.

**.env 파일이 없거나 키가 비어있으면**, 아래 안내를 사용자에게 보여주고 키 입력을 받은 후 `.env` 파일을 생성한다:

```
이 스킬을 사용하려면 공공데이터포털의 TourAPI 인증키가 필요해요.
처음 한 번만 설정하면 됩니다. 3분이면 끝나요!

━━━ TourAPI 인증키 발급 가이드 ━━━

1. 아래 링크에 접속하세요 (회원가입/로그인 필요):
   https://www.data.go.kr/data/15101578/openapi.do

2. "활용신청" 버튼 클릭

3. 활용신청 화면에서:
   - 활용목적: "여행 정보 조회" (아무거나 입력 OK)
   - 동의 체크 후 "신청" 클릭

4. 마이페이지 → 데이터활용 → 오픈API → 개발계정 에서:
   - 일반 인증키 (Encoding) ← 복사

※ 신청 후 자동 승인되며, 약 10분 뒤부터 사용 가능합니다.

인증키를 알려주시면 .env 파일을 만들어드릴게요!
```

사용자가 인증키를 알려주면 `${SKILL_DIR}/.env` 파일을 생성한다:
```
# Trip Advisor 스킬 설정
TOURAPI_SERVICE_KEY={입력받은 값}
TOURAPI_NUM_OF_ROWS=10
```

**.env 파일이 이미 있고 키가 설정되어 있으면**, 이 단계를 건너뛰고 Step 1로 바로 진행한다.

**중요**: 온보딩 완료 후, 사용자가 처음에 요청했던 내용(예: "부산 여행 코스 짜줘")을 이어서 바로 처리한다. 키 설정만 하고 끝내지 말고, 원래 요청의 Step 1~4를 연속으로 실행한다.

### Step 1: 요청 분석 + 지역 파싱
**타입**: prompt

사용자 입력에서 아래 정보를 추출한다:
- **지역명**: "경주", "부산 해운대", "제주" 등 → 스크립트의 지역코드로 변환
- **관심사**: 관광지/맛집/축제/숙박/전체 (기본: 전체)
- **기간**: "이번 주말", "4월", "다음 주" 등 → 날짜 범위 계산 (축제 검색용)

지역코드 매핑 (스크립트 내장):
서울(1), 인천(2), 대전(3), 대구(4), 광주(5), 부산(6), 울산(7), 세종(8), 경기(31), 강원(32), 충북(33), 충남(34), 경북(35), 경남(36), 전북(37), 전남(38), 제주(39)

특정 도시명(경주, 강릉, 전주 등)은 상위 시도 코드로 매핑한다. 예: 경주 → 경북(35), 전주 → 전북(37)

### Step 2: TourAPI 데이터 수집
**타입**: script

Bash 도구로 Python 스크립트를 실행하여 TourAPI 데이터를 수집한다. 사용자 관심사에 따라 필요한 API만 호출한다.

**관광지 검색** (키워드 또는 지역 기반):
```bash
python3 "${SKILL_DIR}/scripts/tour_api.py" \
  --action keyword --keyword "경주" --type "관광지" --num 10 \
  --env-file "${SKILL_DIR}/.env"
```

**맛집 검색**:
```bash
python3 "${SKILL_DIR}/scripts/tour_api.py" \
  --action area --area "경북" --type "음식점" --num 10 \
  --env-file "${SKILL_DIR}/.env"
```

**축제/행사 검색**:
```bash
python3 "${SKILL_DIR}/scripts/tour_api.py" \
  --action festival --start-date "20260401" --area "경북" --num 10 \
  --env-file "${SKILL_DIR}/.env"
```

**숙박 검색**:
```bash
python3 "${SKILL_DIR}/scripts/tour_api.py" \
  --action stay --area "경북" --num 5 \
  --env-file "${SKILL_DIR}/.env"
```

`SKILL_DIR`은 이 SKILL.md가 위치한 디렉토리의 절대 경로다.

### Step 3: 블로그/웹 검색으로 실제 후기 수집
**타입**: prompt (WebSearch 도구 사용)

WebSearch 도구로 블로그 후기와 추천 글을 검색한다:
- "{지역명} 여행코스 추천 블로그"
- "{지역명} 맛집 추천 현지인"
- "{지역명} 가볼만한곳 2026"

검색 결과에서 핵심 추천 장소와 팁을 추출한다. TourAPI 공식 데이터와 교차 검증하여 신뢰도를 높인다.

### Step 4: 종합 여행 가이드 생성
**타입**: prompt + generate

TourAPI 데이터 + 블로그 후기를 종합하여 여행 가이드를 생성한다.

출력 형식:

```markdown
# {지역명} 여행 가이드

## 추천 관광지
| 장소 | 주소 | 한줄 소개 |
|------|------|----------|
| {title} | {addr1} | {overview 요약} |

## 맛집 추천
### TourAPI 공식 등록 맛집
| 식당 | 주소 | 전화 |
|------|------|------|
| {title} | {addr1} | {tel} |

### 블로그 추천 맛집
- {블로그에서 추출한 맛집 + 추천 이유}

## 이달의 축제/행사
| 행사명 | 기간 | 장소 |
|--------|------|------|
| {title} | {eventstartdate}~{eventenddate} | {addr1} |

## 숙박 옵션
| 숙소 | 주소 | 전화 |
|------|------|------|
| {title} | {addr1} | {tel} |

## 블로그 여행 팁
- {웹 검색에서 추출한 현지 꿀팁들}
```

사용자가 파일 저장을 원하면 마크다운 파일로 저장한다.

---

## Scripts
- **`scripts/tour_api.py`** — TourAPI KorService2 호출 스크립트. keyword/festival/area/stay/detail 5가지 액션 지원. http:// 프로토콜 사용 (TourAPI 공식 스펙).

## Settings

| 설정 | 기본값 | 변경 방법 |
|------|--------|-----------|
| TourAPI 인증키 | (없음, 필수) | `.env`의 `TOURAPI_SERVICE_KEY` |
| 기본 결과 수 | 10 | `.env`의 `TOURAPI_NUM_OF_ROWS` |
