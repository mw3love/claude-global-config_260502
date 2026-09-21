"""클로드코드의 두뇌를 mindlogic 게이트웨이로 토글한다 (settings.json 스위치).

  python ~/.claude/scripts/kairos-toggle.py status
  python ~/.claude/scripts/kairos-toggle.py on   [--account kairos|jbnu]
  python ~/.claude/scripts/kairos-toggle.py off

on  → settings.json 에 apiKeyHelper + env.ANTHROPIC_BASE_URL 두 항목을 넣는다.
off → 우리가 넣은 그 두 항목만 뺀다(남의 값은 건드리지 않는다).

키는 settings.json 에 절대 들어가지 않는다 — apiKeyHelper 가 .secrets/ 의
키 파일을 읽는 '명령어'만 저장된다(.secrets/ 는 gitignore, settings.json 은 git 추적).
이 스크립트는 키 내용을 출력하지도 않는다.

⚠ 켜는 동안: 구독 사용량 미차감(크레딧 차감) / claude.ai 커넥터·Remote Control·
   음성입력 비활성 / fast mode 체크 실패. 끄면 저장된 구독 로그인으로 자동 복귀.
⚠ 긴 대화 도중 켜면 프롬프트 캐시가 새로 잡혀 첫 요청에 컨텍스트를 통째로
   재전송한다(크레딧이 한 번에 크게 나감).
"""
import argparse
import json
import os
import sys
from pathlib import Path

HOME = Path.home()
DEFAULT_SETTINGS = HOME / ".claude" / "settings.json"
SECRETS = HOME / ".claude" / ".secrets"

ACCOUNTS = {
    "kairos": {
        "base": "https://factchat.mindlogic-kr-api.com/v1/gateway/claude",
        "key_file": "kairos-gateway.key",
    },
    "jbnu": {
        "base": "https://factchat-cloud.mindlogic.ai/v1/gateway/claude",
        "key_file": "jbnu-gateway.key",
    },
}
BASES = {a["base"] for a in ACCOUNTS.values()}


SHIM = HOME / ".claude" / "scripts" / "gateway-key.ps1"


def helper_cmd(key_path: Path) -> str:
    """apiKeyHelper 명령. 키 '외의 것'을 한 글자도 찍으면 헬퍼가 실패한다.

    Windows 는 -Command 에 중첩 따옴표를 쓰면 cmd.exe 를 거칠 때 따옴표가
    벗겨져 명령이 '실행'되지 않고 '출력'된다(실측: 키 대신 명령문이 찍힘).
    그래서 공식문서 권장대로 작은 .ps1 을 만들고 -File 로 넘긴다 —
    인자가 한 토막뿐이라 어느 쉘을 거쳐도 깨지지 않는다.

    경로는 역슬래시가 아니라 슬래시로 쓴다 — bash 를 거칠 때 역슬래시가
    이스케이프로 먹혀 경로가 뭉개진다(실측: 'C:UsersKBS...'). PowerShell 은
    슬래시 경로를 그대로 받는다.
    -ExecutionPolicy Bypass 가 필요한 이유: 이 PC 기본 정책이 .ps1 실행을
    막아 UnauthorizedAccess 로 떨어진다(실측). 이 한 파일에만 적용된다."""
    if os.name == "nt":
        SHIM.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# kairos-toggle.py 가 생성. 키 외에는 아무것도 출력하지 않는다.",
            f"[Console]::Out.Write((Get-Content -Raw '{key_path.as_posix()}'))",
        ]
        SHIM.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return f"powershell -NoProfile -ExecutionPolicy Bypass -File {SHIM.as_posix()}"
    return f"cat '{key_path}'"


def is_ours(cmd) -> bool:
    if not isinstance(cmd, str):
        return False
    return "gateway-key.ps1" in cmd or (".secrets" in cmd and "-gateway.key" in cmd)


def load(path: Path):
    raw = path.read_text(encoding="utf-8", newline="")
    try:
        return json.loads(raw), raw
    except json.JSONDecodeError as e:
        sys.exit(f"[중단] JSON 을 읽을 수 없음: {path}\n  {e}\n"
                 "  설정 파일이 이미 깨져 있다. 먼저 고친 뒤 다시 실행할 것.")


def save(path: Path, data, raw_before: str):
    """원본의 개행 방식을 유지하고, 임시파일→교체로 원자적으로 쓴다.

    개행 유지 이유: 이 repo 는 core.autocrlf=true 라 체크아웃 뒤 settings.json 이
    CRLF 가 된다. 그때 LF 로 다시 써 버리면 두 줄 고치려다 파일 전체가 diff 로
    뜬다. 원자적 쓰기 이유: 쓰다 중단되면 클로드코드의 설정 파일이 반쪽으로
    남는다(설정 파일은 부팅 경로라 반쪽이 제일 나쁘다)."""
    nl = "\r\n" if "\r\n" in raw_before else "\n"
    out = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").replace("\n", nl)
    if out == raw_before:
        return False
    tmp = path.with_name(path.name + ".kairos-tmp")
    tmp.write_text(out, encoding="utf-8", newline="")
    os.replace(tmp, path)
    return True


def cmd_status(path: Path):
    data, _ = load(path)
    helper = data.get("apiKeyHelper")
    base = (data.get("env") or {}).get("ANTHROPIC_BASE_URL")
    on = is_ours(helper) and base in BASES
    print(f"[설정 파일] {path}")
    print(f"[상태] {'ON — 게이트웨이' if on else 'OFF — 구독 로그인'}")
    print(f"  ANTHROPIC_BASE_URL : {base or '(없음)'}")
    if helper is None:
        print("  apiKeyHelper       : (없음)")
    elif is_ours(helper):
        print("  apiKeyHelper       : 이 스크립트가 넣은 것")
    else:
        print("  apiKeyHelper       : 남의 값 (건드리지 않음)")
    for name, acc in ACCOUNTS.items():
        kp = SECRETS / acc["key_file"]
        print(f"  키 {name:<6} : {'있음' if kp.is_file() else '없음'}  {kp}")
    return 0


def cmd_on(path: Path, account: str):
    acc = ACCOUNTS[account]
    key_path = SECRETS / acc["key_file"]
    if not key_path.is_file():
        sys.exit(f"[중단] 키 파일 없음: {key_path}\n"
                 f"  터미널에서 직접:  ! printf '%s' '발급받은_키' > ~/.claude/.secrets/{acc['key_file']}")
    if key_path.stat().st_size == 0:
        sys.exit(f"[중단] 키 파일이 비어 있음: {key_path}")
    # 헬퍼는 키 원문만 내보내야 한다 — 앞뒤 공백·개행·BOM 이 섞이면 그대로
    # Authorization 헤더에 실려 401 이 난다. 키 내용은 출력하지 않는다.
    blob = key_path.read_bytes()
    if blob.startswith(b"\xef\xbb\xbf"):
        sys.exit(f"[중단] 키 파일에 BOM 이 있음: {key_path}\n"
                 "  BOM 없이 다시 저장할 것:  ! printf '%s' '키' > " + str(key_path))
    if blob != blob.strip():
        sys.exit(f"[중단] 키 파일 앞뒤에 공백·개행이 있음: {key_path}\n"
                 "  개행 없이 다시 저장할 것:  ! printf '%s' '키' > " + str(key_path))

    data, raw = load(path)
    helper = data.get("apiKeyHelper")
    if helper is not None and not is_ours(helper):
        sys.exit("[중단] apiKeyHelper 에 이미 다른 값이 있음. 덮어쓰지 않음.\n"
                 f"  현재값: {helper}")
    env = data.get("env")
    if env is not None and not isinstance(env, dict):
        sys.exit("[중단] env 키가 객체가 아님. 손대지 않음.")
    cur_base = (env or {}).get("ANTHROPIC_BASE_URL")
    if cur_base and cur_base not in BASES:
        sys.exit(f"[중단] ANTHROPIC_BASE_URL 에 이미 다른 주소가 있음: {cur_base}")

    data["apiKeyHelper"] = helper_cmd(key_path)
    data.setdefault("env", {})["ANTHROPIC_BASE_URL"] = acc["base"]
    changed = save(path, data, raw)
    print(f"[ON] {account} 게이트웨이로 전환{'' if changed else ' (이미 같은 상태)'}")
    print(f"  {acc['base']}")
    print("  확인: 클로드코드에서 /status → 'Anthropic base URL' 줄")
    print("  되돌리기: python ~/.claude/scripts/kairos-toggle.py off")
    return 0


def cmd_off(path: Path):
    data, raw = load(path)
    removed = []
    if is_ours(data.get("apiKeyHelper")):
        data.pop("apiKeyHelper")
        removed.append("apiKeyHelper")
    elif "apiKeyHelper" in data:
        print("[건너뜀] apiKeyHelper 가 남의 값이라 그대로 둠")
    env = data.get("env")
    if isinstance(env, dict) and env.get("ANTHROPIC_BASE_URL") in BASES:
        env.pop("ANTHROPIC_BASE_URL")
        removed.append("env.ANTHROPIC_BASE_URL")
        if not env:
            data.pop("env")
    changed = save(path, data, raw)
    print(f"[OFF] 구독 로그인으로 복귀{'' if changed else ' (이미 꺼져 있음)'}")
    if removed:
        print("  제거: " + " / ".join(removed))
    print("  확인: 클로드코드에서 /status → 'Login method' 줄")
    return 0


def main():
    # 이 터미널은 UTF-8 인데 Windows Python 은 기본이 cp949 라 한글이 깨진다
    # (실측: '[OFF] 구독 로그인으로 복귀' → '[OFF] ���� �α�...').
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    p = argparse.ArgumentParser(description="게이트웨이 전환 토글")
    p.add_argument("action", choices=["on", "off", "status"])
    p.add_argument("--account", choices=list(ACCOUNTS), default="kairos")
    p.add_argument("--file", default=str(DEFAULT_SETTINGS),
                   help="대상 settings.json (테스트용 사본 지정 가능)")
    a = p.parse_args()
    path = Path(a.file).expanduser()
    if not path.is_file():
        sys.exit(f"[중단] 설정 파일 없음: {path}")
    if a.action == "status":
        return cmd_status(path)
    if a.action == "on":
        return cmd_on(path, a.account)
    return cmd_off(path)


if __name__ == "__main__":
    sys.exit(main())
