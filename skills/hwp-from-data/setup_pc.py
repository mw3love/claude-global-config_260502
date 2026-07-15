# -*- coding: utf-8 -*-
"""이 PC(이 계정)에 한글 보안모듈을 1회 등록 — 새 PC마다 딱 한 번 실행.
   실행:  python setup_pc.py

   [무엇을 하나]
     pyhwpx가 번들한 FilePathCheckerModule.dll을 HKCU에 등록해,
     한글 COM 열기/저장 시 뜨는 "보안 승인" 창을 줄인다.
     (이 PC 환경·권한에 따라 승인창이 남을 수 있음 — 그러면 실행 중
      창이 뜰 때 [모두 허용(A)]을 한 번 누르면 그 실행 전체가 커버된다.)

   [주의] 이건 보안 통제를 다소 완화하는 설정이다(사용자 계정 한정, 되돌리기 쉬움).
          본인 PC에서 본인이 실행하는 것을 전제로 한다.
"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from pyhwpx import Hwp
except ImportError:
    print("[오류] pyhwpx 미설치 →  pip install pyhwpx pywin32 lxml")
    sys.exit(1)

print("한글 실행 + 보안모듈 등록 중...")
h = Hwp()                       # 생성 시 FilePathCheckerModule 자동 등록
print("한글 버전:", h.Version)
h.quit()
print("─" * 30)
print("[완료] 보안모듈 등록됨.")
print("이후 hwp_edit.py로 열기/저장 시, 승인창이 뜨면 [모두 허용(A)] 1클릭.")
