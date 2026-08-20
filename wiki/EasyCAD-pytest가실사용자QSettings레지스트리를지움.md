---
repo: Easy_CAD_260718
remote: (로컬 전용 — 사용자 git remote 정보 없음, 리포 경로 C:\Users\aros\Dev\Easy_CAD_260718)
stack: [PyQt6, pytest, QSettings, Windows]
tags: [QSettings, 레지스트리, pytest격리, 테스트오염, 재현안됨, 스턱루프]
used: []
---

# pytest가 실사용자 QSettings(레지스트리)를 격리 없이 지워 "설정이 사라진다"는 유령버그를 만듦

## 함정

사용자가 "AI 게이트웨이 설정창에서 API 키를 저장했는데, 프로그램을 껐다 켜면 사라진다"고
**두 번 반복 보고**(규칙 11-b 스턱루프 트리거). 앱 코드를 세 가지 다른 경로로 재현 시도했으나
전부 정상 동작:
1. `store_api_key()` → `resolve_api_key()` 직접 호출(같은 프로세스·새 프로세스 둘 다)
2. 실제 다이얼로그를 만들어 OK 버튼을 `.click()`으로 눌러 `_on_accept()` 신호 경로까지 태움
3. 실제 창(오프스크린 아님)에서 CanvasWindow → 하위 다이얼로그 → 설정창 전체 체인 재현

전부 성공 — 재현 실패. **"안 되는 걸 코드로 못 잡으면 데이터를 직접 봐야 한다"**는 교훈:
PowerShell `Get-ItemProperty -Path 'HKCU:\Software\<Org>\<App>'`로 실제 레지스트리 값을
직접 조회하자, Python/QSettings로 본 값과 PowerShell(완전히 독립된 네이티브 경로)로 본 값이
**시점에 따라 달랐다** — 방금까지 있던 값이 없어져 있었다. 이게 결정적 단서였다: 재현
스크립트가 아니라 **내가 그 사이에 실행한 다른 것**(이 경우 `pytest`)이 범인이라는 뜻.

원인: 테스트 파일의 헬퍼 함수가 `QSettings("EasyCAD", "EasyCAD")`를 **하드코딩**해서
실사용자 레지스트리를 직접 `.remove()`하고 있었다(`_clear_gateway_settings()`, "테스트끼리
오염 방지" 목적으로 작성됨 — 의도는 맞았지만 **격리 대상을 잘못 골랐다**: "테스트 간 오염"만
막았고 "테스트 vs 실사용자 데이터" 오염은 막지 못했다). 원래 있던 값을 백업/복원하는 로직도
없어서, `pytest tests/`를 돌릴 때마다(같은 세션에서 여러 번!) 사용자가 실제로 저장한 키가
조용히 지워지고 있었다. 사용자는 "앱을 껐다 켜면 사라진다"고 느꼈지만, 실제로는 "Claude가
코드를 고칠 때마다 검증 삼아 pytest를 돌려서" 사라진 것 — 앱 재시작과는 무관, **개발자(AI)의
검증 루프 자체가 사용자 데이터를 파괴**하고 있었다는 게 가장 비직관적인 부분.

같은 프로젝트에 이미 정답 패턴이 있었다(`_isolated_symbol_library()`, tests/_shared.py) —
`patch.object(symbol_library, "_library_path", return_value=<temp path>)`로 **저장 위치
자체를 리다이렉트**하는 방식. 문제의 헬퍼는 이 관례를 안 따르고 직접 하드코딩했다.

## 해법

1. 앱 코드(`gateway.py`) 쪽에 `QSettings(org, app)`의 org/app 문자열을 **모듈 레벨 상수**로
   뺀다(`_SETTINGS_ORG`, `_SETTINGS_APP`). 함수 안에서 `from PyQt6.QtCore import QSettings`를
   지연 임포트하는 기존 설계(헤드리스 순수 파이썬 도구에서도 쓰기 위해 PyQt6 무의존 유지)는
   그대로 두고, **문자열 상수만** 모듈 레벨로 승격 — PyQt6 임포트 없이 순수 파이썬으로 존재
   가능하니 그 설계원칙과 충돌 안 함.
2. `tests/conftest.py`에 **autouse fixture**를 하나 추가해 세션 전체 테스트가 그 상수를
   `monkeypatch.setattr("pkg.module._SETTINGS_ORG", "격리된값")`로 덮어쓰게 한다. 개별 테스트
   파일 하나만 고치는 게 아니라 **진입점(생성자 인자) 자체를 conftest에서 틀어막는 게 핵심**
   — 나중에 다른 파일이 같은 QSettings를 또 건드려도 자동으로 안전하다(파일별로 하나하나
   isolate 하는 방식은 "새 파일에서 또 깜빡함" 재발 위험이 남는다).
3. 기존 헬퍼(`_clear_gateway_settings()`)도 하드코딩 대신 `gw._SETTINGS_ORG`/`gw._SETTINGS_APP`을
   참조하도록 고쳐서, conftest의 monkeypatch가 적용된 값을 그대로 따라가게 한다(하드코딩을
   남겨두면 fixture가 있어도 그 특정 호출만은 여전히 실사용자 값을 칠 수 있음).

## 대가

- 방어적으로 `store_api_key`/`store_base_url`에 `settings.sync()`(즉시 flush)도 같이
  추가했지만, 이건 근본 원인이 아니라 예방적 조치다 — 진짜 원인은 100% 테스트 오염이었다.
- 이미 유실된 사용자의 실제 키는 되돌릴 수 없다(어차피 API 키라 재발급/재입력만 가능) —
  사용자에게 재입력을 요청해야 했다.

## 일반화 (다른 프로젝트에도 적용 가능)

**pytest에서 실제 앱 코드 경로를 그대로 exercise하는 테스트를 쓸 때, 그 코드가 `QSettings`·
`~/.config`류 dotfile·OS 키체인처럼 "사용자 전역 상태"를 만지면, 그 진입점 자체를 conftest
autouse fixture로 격리하는 걸 기본값으로 삼을 것.** "테스트끼리만 안 겹치면 된다"는 좁은
목표로 헬퍼를 짜면, 그 헬퍼가 실사용자 상태까지 건드리고 있다는 걸 몇 달간 못 알아챌 수
있다(이번 사례: 이 헬퍼가 언제부터 있었는지는 불명, 발견은 사용자가 실제로 겪은 뒤였다).
