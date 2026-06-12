"""전북대 API Gateway 공용 헬퍼.

- API 키 로딩: 환경변수 JBNU_GATEWAY_API_KEY 우선, 없으면
  ~/.claude/.secrets/jbnu-gateway.key 파일(첫 줄)에서 읽는다.
- HTTP: 외부 의존성 없이 표준 라이브러리(urllib)만 사용한다.

키는 절대 코드/로그에 하드코딩하지 않는다. .secrets/ 는 .gitignore 됨.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

BASE = "https://factchat-cloud.mindlogic.ai/v1/gateway"

# Cloudflare(앞단 보안 게이트)가 기본 Python UA를 봇으로 보고 403/code:1010으로
# 차단하므로 브라우저형 User-Agent를 보낸다.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def load_key() -> str:
    key = os.environ.get("JBNU_GATEWAY_API_KEY", "").strip()
    if key:
        return key
    key_file = Path.home() / ".claude" / ".secrets" / "jbnu-gateway.key"
    if key_file.exists():
        first = key_file.read_text(encoding="utf-8").splitlines()
        if first and first[0].strip():
            return first[0].strip()
    sys.exit(
        "[오류] API 키를 찾을 수 없습니다.\n"
        "  방법1: 환경변수 JBNU_GATEWAY_API_KEY 설정\n"
        f"  방법2: {key_file} 파일 첫 줄에 키 저장\n"
        "  (이 파일은 .gitignore 되어 push되지 않습니다)"
    )


def _headers(key: str, json_body: bool = True) -> dict:
    h = {
        "Authorization": f"Bearer {key}",
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
    }
    if json_body:
        h["Content-Type"] = "application/json"
    return h


def post_json(path: str, body: dict, key: str | None = None):
    """JSON POST → (status, parsed_json_or_bytes, raw_headers)."""
    key = key or load_key()
    url = BASE + path
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=_headers(key), method="POST")
    return _send(req)


def get(path: str, key: str | None = None):
    """GET → (status, parsed_json_or_bytes, raw_headers)."""
    key = key or load_key()
    url = BASE + path
    req = urllib.request.Request(url, headers=_headers(key, json_body=False), method="GET")
    return _send(req)


def _send(req):
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            headers = dict(resp.headers.items())
            if "application/json" in ctype:
                return resp.status, json.loads(raw.decode("utf-8")), headers
            return resp.status, raw, headers
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"[HTTP {e.code}] {e.reason}\n{body}")
    except urllib.error.URLError as e:
        sys.exit(f"[네트워크 오류] {e.reason}")
