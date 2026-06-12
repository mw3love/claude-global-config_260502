"""크레딧 잔액 조회 — GET /credits/

사용: python credits.py
"""
import json
import _gw

_, resp, _ = _gw.get("/credits/")
print(json.dumps(resp, ensure_ascii=False, indent=2))
