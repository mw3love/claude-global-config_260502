---
repo: PasteFlow
remote: https://github.com/mw3love/Paste_flow.git
stack: [Python, ctypes, Windows]
tags: [ctypes, windll, WinDLL, argtypes, GetWindowRect, 유령버그, 프로브-앱-불일치, MSAA, 영역캡처]
used: []
---

# ctypes.windll.user32 공유 argtypes 전역 충돌 — "프로브는 되는데 앱만 깨짐"

## 함정
`ctypes.windll.user32`는 **프로세스 전역에서 캐시·공유되는 단일 객체**다. 두 모듈이
같은 함수(예: `GetWindowRect`)에 각자의 Structure로 `argtypes`를 걸면 **나중에 import된
쪽이 앞의 설정을 덮어쓴다**. 그러면 앞 모듈이 자기 `_RECT`로 그 함수를 호출하는 순간
`ArgumentError: expected LP__RECT instance instead of pointer to _RECT`로 터진다
(둘 다 이름은 `_RECT`지만 ctypes는 클래스 *정체*로 구분).

증상이 지독한 이유: **단위 프로브(문제 모듈 하나만 import)에선 충돌이 없어 통과**하는데,
**실제 앱(여러 모듈 로드)에선만 터진다.** 게다가 호출한 함수가 예외를 `try/except`로
삼켜 `None`을 반환하면(우리 경우 `rect_in_window_at`), 겉으론 크래시 없이 **조용히
폴백**해 "함수 로직은 맞는데 앱에서만 다르게 동작하는" 유령 버그가 된다. 실제로 HWP
편집영역 스냅이 프로브에선 편집영역을 주는데 앱에선 창 전체로 폴백돼 몇 라운드를 헤맸다.

## 해법
충돌하는 모듈은 공유 `ctypes.windll.user32` 대신 **전용 인스턴스 `ctypes.WinDLL("user32")`**
를 만들어 쓴다. `WinDLL(...)`는 호출마다 새 래퍼 객체를 만들어 함수 `argtypes`가 그
인스턴스에 격리되므로 다른 모듈의 설정과 안 부딪힌다. (같은 DLL이라 동작은 동일, 마샬링
설정만 분리.)

```python
_user32 = ctypes.WinDLL("user32")   # not ctypes.windll.user32
_user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(_RECT)]
```

## 발견법 (이게 핵심 — 추측으론 절대 안 나옴)
프로브와 앱이 갈리는데 코드를 읽어선 원인이 안 보이면, **앱 코드 경로에 로그를 심어
실제 계산값(과 잡힌 예외)을 파일로 실측**한다. 우리는 오버레이의 `_target_rect_logical`에
임시 `_dbg_overlay()`를 넣어 hover마다 값을 append했고, 로그에 값 대신 `DBG ERROR:
ArgumentError(...)`가 찍혀 원인이 한 방에 드러났다. "프로브 통과 → 앱만 실패 + 예외를
삼키는 폴백"이 보이면 **전역 공유 상태(argtypes·전역 변수·모듈 캐시) 오염**을 의심하라.

## 대가
전용 WinDLL 인스턴스는 그 모듈에서만 유효하므로, 같은 함수를 쓰는 다른 모듈도 각자
argtypes를 세팅해야 한다(공유로 한 번만 세팅하던 것보다 중복). 사소한 비용.
