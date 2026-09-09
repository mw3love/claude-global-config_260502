"""생성 전 사전 고지 — 실시간 잔액 + 모델 메뉴 + 예상 비용.

사용:
  python preflight.py video      # 비디오 모델·단가·구매가능 수량
  python preflight.py image
  python preflight.py tts
  python preflight.py chat        # /models 실시간 41종(단가 미노출)
  python preflight.py            # 잔액만

이미지/비디오/TTS 생성 *전에* 호출해 사용자에게 보여준다.
비디오는 costs.json의 approval=required → 명시적 승인 후 생성.
"""
import json
import sys
from pathlib import Path

import _gw

# Windows 콘솔(cp949)에서 이모지·한글이 깨지지 않도록 출력 UTF-8 고정
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

COSTS = json.loads((Path(__file__).parent / "costs.json").read_text(encoding="utf-8"))


def balance(account=None):
    _, data, _ = _gw.get("/credits/", account=account)
    t = data["total"]
    return t["remaining"], t["quota"], data["monthly_allocated"].get("renewal_date", "")


def show_balance(active):
    """두 계정 잔액을 함께 표시하고 활성 계정의 잔액을 반환한다."""
    rem_active = None
    for name, c in _gw.ACCOUNTS.items():
        mark = "▶" if name == active else " "
        if not _gw.has_key(name):
            print(f" {mark} {name:7} 키 없음 — {c['use']}")
            continue
        rem, quota, renew = balance(name)
        print(f" {mark} {name:7} {rem:>9,.1f} / {quota:,.0f} 크레딧"
              f"  (리셋 {renew[:10]})  {c['use']}")
        if name == active:
            rem_active = rem
    if rem_active is None:
        sys.exit(f"[오류] 활성 계정 '{active}'의 키가 없어 진행 불가")
    return rem_active


def show_capability(cap: str, rem: float):
    spec = COSTS.get(cap)
    if not spec:
        sys.exit(f"알 수 없는 기능: {cap} (video|image|tts|chat)")
    print(f"\n[{cap}] 단위: {spec['unit']}  · 출처: {spec['source']}"
          + ("  · ⚠️ 비디오는 생성 전 명시 승인 필요" if spec["approval"] == "required" else ""))
    rows = sorted(spec["models"].items(), key=lambda kv: (kv[1]["cost"] is None, kv[1]["cost"] or 0))
    rec = None
    for model, info in rows:
        cost = info["cost"]
        if cost is None:
            afford = "비동기·단가미상"
            cost_s = "?"
        elif cost >= 1:
            afford = f"~{int(rem // cost):,}개 가능"
            cost_s = f"{cost:g}"
        else:
            afford = "사실상 무료"
            cost_s = f"{cost:g}"
        mark = "★" if info.get("recommend") else " "
        if info.get("recommend"):
            rec = (model, info.get("best_for", ""))
        print(f" {mark} {model:42} {cost_s:>6}  {afford}")
        bf = info.get("best_for", "")
        sp = info.get("size_param", "")
        detail = "  · ".join(x for x in (bf, sp) if x)
        if detail:
            print(f"      └ {detail}")
    if rec:
        print(f"\n  ★추천: {rec[0]} — {rec[1]}")


def show_chat(rem: float):
    _, data, _ = _gw.get("/models/")
    spec = COSTS.get("chat", {})
    known = spec["models"]
    print(f"\n[chat] 단위: {spec['unit']}  · 출처: {spec['source']}")
    rec = None
    for model, info in sorted(known.items(), key=lambda kv: kv[1]["in"]):
        mark = "★" if info.get("recommend") else " "
        if info.get("recommend"):
            rec = (model, info["best_for"])
        print(f" {mark} {model:18} 입력 {info['in']:>6,} / 출력 {info['out']:>6,}"
              f"   잔액으로 입력 ~{rem / info['in']:.1f}M토큰")
        print(f"      └ {info['best_for']}")
    if rec:
        print(f"\n  ★추천: {rec[0]} — {rec[1]}")
    print(f"\n  ⚠ {spec['cache_note']}")

    print(f"\n  [전체 {len(data['data'])}종 — 위 5종 외에는 단가 미측정]")
    by_owner = {}
    for it in data["data"]:
        by_owner.setdefault(it.get("owned_by", "?"), []).append(it["id"])
    for owner in sorted(by_owner):
        print(f"  {owner:12} " + ", ".join(sorted(by_owner[owner])))


def main():
    args = [a for a in sys.argv[1:]]
    account = None
    if "--account" in args:
        i = args.index("--account")
        account = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]
    active = _gw.use(account)
    cap = args[0].lower() if args else None
    rem = show_balance(active)
    if cap == "chat":
        show_chat(rem)
    elif cap in ("video", "image", "tts"):
        show_capability(cap, rem)
    elif cap:
        sys.exit(f"알 수 없는 기능: {cap} (video|image|tts|chat)")


if __name__ == "__main__":
    main()
