"""게이트웨이 잔액을 한 줄로 찍는다 (런처 배너용)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "kairos" / "scripts"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
try:
    import _gw
    _gw.use(sys.argv[1] if len(sys.argv) > 1 else None)
    for part in _gw.get("/credits"):
        if isinstance(part, dict) and "monthly_allocated" in part:
            m = part["monthly_allocated"]
            print(f"잔액 {m['remaining']:,.0f} / {m['quota']:,.0f} 크레딧  (갱신 {m['renewal_date'][:10]})")
            break
    else:
        print("잔액 조회 실패 (응답 형식 불일치)")
except Exception as e:
    print(f"잔액 조회 실패: {e}")
