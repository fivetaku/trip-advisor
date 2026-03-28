#!/usr/bin/env python3
# TourAPI 호출 스크립트 — KorService2
# 관광지/축제/맛집/숙박 데이터를 조회하여 JSON으로 반환
# 주의: TourAPI는 http:// 프로토콜 사용 (https 시 403 발생 가능)

import sys
import json
import re
import argparse
from pathlib import Path
from urllib.parse import unquote

try:
    import requests
except ImportError:
    print(json.dumps({"success": False, "error": "MISSING_DEPENDENCY",
                      "message": "requests 라이브러리가 필요합니다.\n설치: pip install requests"},
                     ensure_ascii=False))
    sys.exit(1)


def load_env(env_file):
    env_path = Path(env_file)
    if not env_path.exists():
        _exit_error("ENV_NOT_FOUND",
                    f".env 파일을 찾을 수 없습니다: {env_file}\n"
                    ".env.example을 복사해서 .env를 만들고 API 키를 입력하세요.")
    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _exit_error(code, message):
    print(json.dumps({"success": False, "error": code, "message": message},
                     ensure_ascii=False))
    sys.exit(1)


# TourAPI는 http:// 사용 (https 호출 시 403 반환하는 경우 있음)
BASE_URL = "http://apis.data.go.kr/B551011/KorService2"

# contentTypeId 매핑
CONTENT_TYPES = {
    "관광지": "12", "문화시설": "14", "행사": "15", "축제": "15",
    "여행코스": "25", "레포츠": "28", "숙박": "32",
    "쇼핑": "38", "음식점": "39", "맛집": "39",
}

# 지역코드 매핑 — 시/도 + 주요 관광도시
AREA_CODES = {
    # 광역시/도
    "서울": "1", "인천": "2", "대전": "3", "대구": "4", "광주": "5",
    "부산": "6", "울산": "7", "세종": "8",
    "경기": "31", "강원": "32", "충북": "33", "충남": "34",
    "경북": "35", "경남": "36", "전북": "37", "전남": "38", "제주": "39",
    # 주요 관광도시 → 상위 시도코드
    "수원": "31", "성남": "31", "용인": "31", "고양": "31", "파주": "31",
    "춘천": "32", "강릉": "32", "속초": "32", "평창": "32", "양양": "32", "정선": "32",
    "청주": "33", "충주": "33", "제천": "33", "단양": "33",
    "천안": "34", "아산": "34", "공주": "34", "부여": "34", "태안": "34", "보령": "34",
    "경주": "35", "포항": "35", "안동": "35", "영주": "35", "울릉": "35",
    "창원": "36", "통영": "36", "거제": "36", "진주": "36", "남해": "36", "하동": "36",
    "전주": "37", "군산": "37", "남원": "37", "무주": "37",
    "여수": "38", "순천": "38", "목포": "38", "담양": "38", "해남": "38", "완도": "38",
    "제주시": "39", "서귀포": "39",
}

# 공공데이터포털 에러코드 → 사용자 메시지
ERROR_MESSAGES = {
    "10": "잘못된 요청 파라미터입니다. 입력값을 확인하세요.",
    "12": "해당 API 서비스가 없거나 폐기되었습니다.",
    "20": "서비스 접근이 거부되었습니다. 공공데이터포털에서 활용 승인을 확인하세요.",
    "22": "일일 요청 한도(1,000건)를 초과했습니다. 내일 다시 시도하세요.",
    "30": "등록되지 않은 서비스키입니다. .env의 TOURAPI_SERVICE_KEY를 확인하세요.",
    "31": "활용 기간이 만료되었습니다. 공공데이터포털에서 연장 신청하세요.",
}


def _parse_xml_error(text):
    """TourAPI XML 에러 응답에서 에러코드와 메시지 추출."""
    code_match = re.search(r'<returnReasonCode>(\d+)</returnReasonCode>', text)
    msg_match = re.search(r'<returnAuthMsg>(.+?)</returnAuthMsg>', text)
    if code_match:
        code = code_match.group(1)
        msg = msg_match.group(1) if msg_match else "알 수 없는 에러"
        return code, msg
    return None, None


def _call_api(endpoint, params, env):
    """TourAPI 호출."""
    raw_key = env.get('TOURAPI_SERVICE_KEY')
    if not raw_key:
        _exit_error("MISSING_CONFIG", "TOURAPI_SERVICE_KEY가 .env에 설정되지 않았습니다.")

    # P0 Fix: .env에 URL 인코딩된 키가 있으면 디코딩 후 requests에 전달
    # requests.get(params=...)가 자동 인코딩하므로 이중 인코딩 방지
    service_key = unquote(raw_key)

    num_of_rows = env.get('TOURAPI_NUM_OF_ROWS', '10')

    url = f"{BASE_URL}/{endpoint}"
    base_params = {
        "serviceKey": service_key,
        "MobileOS": "ETC",
        "MobileApp": "TripAdvisor",
        "_type": "json",
        "numOfRows": params.get("numOfRows", num_of_rows),
        "pageNo": params.get("pageNo", "1"),
    }
    # params가 보호 키를 덮어쓰지 않도록 필터링
    for k, v in params.items():
        if k not in ("serviceKey", "MobileOS", "MobileApp", "_type"):
            base_params[k] = v

    try:
        response = requests.get(url, params=base_params, timeout=30)
    except requests.exceptions.Timeout:
        _exit_error("TIMEOUT", "API 요청 시간이 초과되었습니다.")
    except requests.exceptions.ConnectionError:
        _exit_error("CONNECTION_ERROR", "API 서버에 연결할 수 없습니다.")

    if response.status_code == 403:
        _exit_error("AUTH_ERROR",
                    "API 인증에 실패했습니다. .env의 TOURAPI_SERVICE_KEY를 확인하세요.")
    elif response.status_code != 200:
        _exit_error("API_ERROR", f"API 오류 (HTTP {response.status_code})")

    # P0 Fix: 에러 응답은 _type=json이어도 XML로 옴
    content_type = response.headers.get('Content-Type', '')
    if 'xml' in content_type or response.text.strip().startswith('<?xml') \
       or '<OpenAPI_ServiceResponse>' in response.text:
        error_code, error_msg = _parse_xml_error(response.text)
        if error_code:
            user_msg = ERROR_MESSAGES.get(error_code, error_msg)
            _exit_error("API_ERROR", f"TourAPI 에러 [{error_code}]: {user_msg}")
        _exit_error("API_ERROR", f"XML 에러 응답: {response.text[:300]}")

    try:
        data = response.json()
    except (json.JSONDecodeError, ValueError):
        _exit_error("PARSE_ERROR", f"JSON 파싱 실패. 응답: {response.text[:300]}")

    header = data.get("response", {}).get("header", {})
    # P0 Fix: resultCode "0000"과 "00" 둘 다 허용
    if header.get("resultCode") not in ("0000", "00"):
        _exit_error("API_ERROR",
                    f"API 에러: {header.get('resultMsg', 'Unknown')} "
                    f"(코드: {header.get('resultCode')})")

    return data


def _extract_items(data):
    """API 응답에서 items 추출. 결과 0건 시 items가 빈 문자열("")로 올 수 있음."""
    body = data.get("response", {}).get("body", {})
    total = body.get("totalCount", 0)
    items = body.get("items", {})
    # P0 Fix: items가 "", None, [] 등 dict가 아닌 경우 방어
    if not items or not isinstance(items, dict):
        return [], total
    item_list = items.get("item", [])
    if isinstance(item_list, dict):
        item_list = [item_list]
    return item_list, total


def _resolve_area(area_name):
    """지역명을 areaCode로 변환. 미매칭 시 None 반환."""
    if not area_name:
        return None
    return AREA_CODES.get(area_name)


def search_keyword(keyword, content_type=None, area=None, env=None, num=None):
    """키워드 검색."""
    params = {"keyword": keyword}
    if content_type and content_type in CONTENT_TYPES:
        params["contentTypeId"] = CONTENT_TYPES[content_type]
    area_code = _resolve_area(area)
    if area_code:
        params["areaCode"] = area_code
    if num:
        params["numOfRows"] = str(num)
    return _call_api("searchKeyword2", params, env)


def search_festival(start_date, end_date=None, area=None, env=None, num=None):
    """축제/행사 검색."""
    params = {"eventStartDate": start_date}
    if end_date:
        params["eventEndDate"] = end_date
    area_code = _resolve_area(area)
    if area_code:
        params["areaCode"] = area_code
    if num:
        params["numOfRows"] = str(num)
    return _call_api("searchFestival2", params, env)


def area_based_list(area, content_type=None, env=None, num=None):
    """지역기반 관광정보 조회."""
    params = {}
    area_code = _resolve_area(area)
    if area_code:
        params["areaCode"] = area_code
    if content_type and content_type in CONTENT_TYPES:
        params["contentTypeId"] = CONTENT_TYPES[content_type]
    if num:
        params["numOfRows"] = str(num)
    params["arrange"] = "Q"  # 인기순 (이미지 필수)
    return _call_api("areaBasedList2", params, env)


def search_stay(area, env=None, num=None):
    """숙박 검색."""
    params = {}
    area_code = _resolve_area(area)
    if area_code:
        params["areaCode"] = area_code
    if num:
        params["numOfRows"] = str(num)
    return _call_api("searchStay2", params, env)


def detail_common(content_id, env=None):
    """공통정보 조회 (개요 포함)."""
    params = {
        "contentId": content_id,
        "defaultYN": "Y",
        "overviewYN": "Y",
        "addrinfoYN": "Y",
        "mapinfoYN": "Y",
    }
    return _call_api("detailCommon2", params, env)


def main():
    parser = argparse.ArgumentParser(description='TourAPI 호출 스크립트 (KorService2)')
    parser.add_argument('--action', required=True,
                        choices=['keyword', 'festival', 'area', 'stay', 'detail'],
                        help='API 액션')
    parser.add_argument('--keyword', help='검색 키워드')
    parser.add_argument('--area', help='지역명 (서울/부산/경주/강릉 등)')
    parser.add_argument('--type', help='콘텐츠 타입 (관광지/음식점/숙박/축제 등)')
    parser.add_argument('--start-date', help='시작일 (YYYYMMDD)')
    parser.add_argument('--end-date', help='종료일 (YYYYMMDD)')
    parser.add_argument('--content-id', help='콘텐츠 ID (상세 조회용)')
    parser.add_argument('--num', help='결과 수', default=None)
    parser.add_argument('--env-file', required=True, help='.env 파일 경로')
    args = parser.parse_args()

    env = load_env(args.env_file)

    if args.action == 'keyword':
        if not args.keyword:
            _exit_error("MISSING_PARAM", "--keyword가 필요합니다.")
        data = search_keyword(args.keyword, args.type, args.area, env, args.num)
    elif args.action == 'festival':
        if not args.start_date:
            _exit_error("MISSING_PARAM", "--start-date가 필요합니다 (YYYYMMDD).")
        data = search_festival(args.start_date, args.end_date, args.area, env, args.num)
    elif args.action == 'area':
        if not args.area:
            _exit_error("MISSING_PARAM", "--area가 필요합니다.")
        data = area_based_list(args.area, args.type, env, args.num)
    elif args.action == 'stay':
        if not args.area:
            _exit_error("MISSING_PARAM", "--area가 필요합니다.")
        data = search_stay(args.area, env, args.num)
    elif args.action == 'detail':
        if not args.content_id:
            _exit_error("MISSING_PARAM", "--content-id가 필요합니다.")
        data = detail_common(args.content_id, env)

    items, total = _extract_items(data)
    result = {
        "success": True,
        "action": args.action,
        "total_count": total,
        "count": len(items),
        "items": items,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
