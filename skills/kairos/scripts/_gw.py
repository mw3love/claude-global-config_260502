"""mindlogic API Gateway 공용 헬퍼 (kairos·jbnu 두 계정 지원).

- 계정: kairos(회사, 월 4만) 기본 / jbnu(학교, 월 1만). 용도가 분리돼
  있으므로 자동 폴백은 하지 않는다 — 전환은 항상 명시적으로.
- API 키 로딩: 환경변수 우선, 없으면 ~/.claude/.secrets/<계정>.key 첫 줄.
- HTTP: 외부 의존성 없이 표준 라이브러리(urllib)만 사용한다.

키는 절대 코드/로그에 하드코딩하지 않는다. .secrets/ 는 .gitignore 됨.
"""
import json
import os
import ssl
import sys
import urllib.request
import urllib.error
from pathlib import Path


def _ssl_context():
    """Windows 인증서 저장소에 Amazon Root CA 1이 없어 kairos 도메인이
    'self-signed certificate in certificate chain'으로 거부되는 문제를 피한다.
    certifi 번들(Amazon 루트 포함)을 우선 쓰고, 없으면 기본값으로 되돌린다.
    검증 자체는 절대 끄지 않는다."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


_SSL = _ssl_context()

ACCOUNTS = {
    "kairos": {
        "base": "https://factchat.mindlogic-kr-api.com/v1/gateway",
        "key_file": "kairos-gateway.key",
        "env": "KAIROS_GATEWAY_API_KEY",
        "quota": 40000,
        "use": "코딩·교차검증(주 계정)",
    },
    "jbnu": {
        "base": "https://factchat-cloud.mindlogic.ai/v1/gateway",
        "key_file": "jbnu-gateway.key",
        "env": "JBNU_GATEWAY_API_KEY",
        "quota": 10000,
        "use": "번역·OCR 등 저비용 도구",
    },
}
DEFAULT_ACCOUNT = "kairos"
_current = DEFAULT_ACCOUNT


def use(account=None):
    """스크립트 시작 시 1회 호출해 이후 요청이 쓸 계정을 고정한다."""
    global _current
    _current = resolve(account)
    return _current


def resolve(account=None):
    name = (account or os.environ.get("MINDLOGIC_ACCOUNT") or _current).lower()
    if name not in ACCOUNTS:
        sys.exit(f"[오류] 알 수 없는 계정: {name} (가능: {', '.join(ACCOUNTS)})")
    return name


def cfg(account=None):
    return ACCOUNTS[resolve(account)]


def base(account=None):
    return cfg(account)["base"]

# Cloudflare(앞단 보안 게이트)가 기본 Python UA를 봇으로 보고 403/code:1010으로
# 차단하므로 브라우저형 User-Agent를 보낸다.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def load_key(account=None) -> str:
    name = resolve(account)
    c = ACCOUNTS[name]
    key = os.environ.get(c["env"], "").strip()
    if key:
        return key
    key_file = Path.home() / ".claude" / ".secrets" / c["key_file"]
    if key_file.exists():
        first = key_file.read_text(encoding="utf-8").splitlines()
        if first and first[0].strip():
            return first[0].strip()
    sys.exit(
        f"[오류] '{name}' 계정의 API 키를 찾을 수 없습니다.\n"
        f"  방법1: 환경변수 {c['env']} 설정\n"
        f"  방법2: {key_file} 파일 첫 줄에 키 저장\n"
        "  (이 파일은 .gitignore 되어 push되지 않습니다)\n"
        f"  터미널에서: ! printf '%s' '키' > {key_file}"
    )


def has_key(account=None) -> bool:
    """키 존재 여부만 조용히 확인(없어도 종료하지 않음)."""
    c = ACCOUNTS[resolve(account)]
    if os.environ.get(c["env"], "").strip():
        return True
    f = Path.home() / ".claude" / ".secrets" / c["key_file"]
    return f.exists() and bool(f.read_text(encoding="utf-8").strip())


def _headers(key: str, json_body: bool = True) -> dict:
    h = {
        "Authorization": f"Bearer {key}",
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
    }
    if json_body:
        h["Content-Type"] = "application/json"
    return h


def post_json(path: str, body: dict, key: str | None = None, account=None):
    """JSON POST → (status, parsed_json_or_bytes, raw_headers)."""
    key = key or load_key(account)
    url = base(account) + path
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=_headers(key), method="POST")
    return _send(req)


def get(path: str, key: str | None = None, account=None):
    """GET → (status, parsed_json_or_bytes, raw_headers)."""
    key = key or load_key(account)
    url = base(account) + path
    req = urllib.request.Request(url, headers=_headers(key, json_body=False), method="GET")
    return _send(req)


def _send(req):
    try:
        with urllib.request.urlopen(req, timeout=300, context=_SSL) as resp:
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
