"""교차검증 — 다른 회사 모델(GPT 계열)에 2차 소견을 받는다.

설계 원칙: **1차 자료만 넘기고 내 추론은 넘기지 않는다.**
같은 컨텍스트를 공유하면 같은 오해도 공유하므로, 검증자를 내 프레임에
끌어들이지 않는 것이 이 도구의 존재 이유다.

사용:
  python crosscheck.py --mode plan --req 요구사항.txt --target 계획.md
  python crosscheck.py --mode code --req "로그인 후 리다이렉트" \
      --target src/auth.py --error error.log
  python crosscheck.py --mode plan --target 계획.md --dry-run   # 전송 전 확인만

옵션:
  --model    기본 gpt-6-astra (sol/terra로 낮추면 저렴)
  --account  kairos(기본) | jbnu
  --dry-run  실제 호출 없이 보낼 프롬프트와 예상 비용만 출력
"""
import argparse
import json
import sys
from pathlib import Path

import _gw

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

COSTS = json.loads((Path(__file__).parent / "costs.json").read_text(encoding="utf-8"))

SYSTEM = {
    "plan": (
        "You are an independent reviewer. You are given a plan written by ANOTHER "
        "engineer, plus the original requirement it must satisfy. You do NOT have "
        "their reasoning, and you should not try to reconstruct it.\n"
        "Report, in Korean, concisely:\n"
        "1) 요구사항 대비 빠진 것\n2) 틀렸거나 위험한 가정\n"
        "3) 더 단순한 대안이 있으면 그것\n4) 검증 불가능한 항목(측정 기준이 없는 것)\n"
        "If the plan is sound, say so plainly instead of inventing problems."
    ),
    "code": (
        "You are an independent reviewer. You are given source code written by "
        "ANOTHER engineer, the requirement it must satisfy, and (optionally) an "
        "error/log. You do NOT have their reasoning.\n"
        "Report, in Korean, concisely:\n"
        "1) 이 증상을 설명할 수 있는 원인 후보(가장 그럴듯한 것부터)\n"
        "2) 각 후보를 확인/반증하는 방법\n3) 놓치기 쉬운 엣지 케이스\n"
        "Do not propose a rewrite. Point at the specific line or condition."
    ),
}


def read_arg(value):
    """파일 경로면 내용을, 아니면 문자열 그대로."""
    if not value:
        return None
    p = Path(value)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8", errors="replace")
    return value


def build(mode, req, target, error):
    parts = []
    if req:
        parts.append(f"# 원 요구사항 (사용자 원문)\n{req}")
    label = "검토 대상 계획" if mode == "plan" else "검토 대상 코드"
    parts.append(f"# {label}\n{target}")
    if error:
        parts.append(f"# 에러/로그 원문\n{error}")
    return "\n\n".join(parts)


def estimate(model, chars_in, max_out):
    spec = COSTS["chat"]["models"].get(model)
    if not spec:
        return None
    tok_in = chars_in / 3          # 한글 혼용 기준 보수적 추정
    return (tok_in * spec["in"] + max_out * spec["out"]) / 1e6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["plan", "code"], required=True)
    ap.add_argument("--target", required=True, help="검토 대상(파일 경로 또는 문자열)")
    ap.add_argument("--req", default=None, help="원 요구사항(파일 또는 문자열)")
    ap.add_argument("--error", default=None, help="에러/로그(파일 또는 문자열)")
    ap.add_argument("--model", default="gpt-6-astra")
    ap.add_argument("--max-tokens", type=int, default=4000,
                    help="추론 모델은 이 값이 작으면 답변 없이 크레딧만 소모됨")
    ap.add_argument("--account", default=None, help="kairos(기본) | jbnu")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    account = _gw.use(args.account)
    target = read_arg(args.target)
    if not target:
        sys.exit("[오류] --target 이 비어 있음")
    user = build(args.mode, read_arg(args.req), target, read_arg(args.error))

    est = estimate(args.model, len(user), args.max_tokens)
    print(f"[교차검증] mode={args.mode}  model={args.model}  account={account}")
    print(f"  전송 크기: {len(user):,}자 (약 {len(user)//3:,} 토큰)")
    if est:
        print(f"  예상 비용: 약 {est:,.0f} 크레딧 (출력 상한 {args.max_tokens:,} 기준)")

    if args.dry_run:
        print("\n--- 보낼 내용 (dry-run) ---")
        print(user[:2000] + ("\n... (이하 생략)" if len(user) > 2000 else ""))
        return

    _, resp, _ = _gw.post_json("/chat/completions/", {
        "model": args.model,
        "max_tokens": args.max_tokens,
        "messages": [
            {"role": "system", "content": SYSTEM[args.mode]},
            {"role": "user", "content": user},
        ],
    })

    u = resp.get("usage", {}) or {}
    msg = (resp.get("choices") or [{}])[0].get("message", {}).get("content", "")
    print("\n--- 2차 소견 ---")
    print(msg.strip() or "(빈 응답 — max-tokens가 추론에 다 쓰였을 수 있음)")
    rt = (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
    print(f"\n[usage] 입력 {u.get('prompt_tokens',0):,} / "
          f"출력 {u.get('completion_tokens',0):,}(추론 {rt:,})")


if __name__ == "__main__":
    main()
