---
name: trip-advisor
description: 여행 코스, 맛집, 관광지, 축제, 숙박 정보를 종합 정리합니다
arguments:
  - name: destination
    description: 여행지 또는 요청 (예: "부산 2박3일", "제주도 맛집")
    required: false
---

$ARGUMENTS가 있으면 해당 여행지로, 없으면 여행지를 물어본 후 trip-advisor 스킬의 워크플로우를 실행한다.

Read `SKILL.md` and execute the workflow with destination: $ARGUMENTS
