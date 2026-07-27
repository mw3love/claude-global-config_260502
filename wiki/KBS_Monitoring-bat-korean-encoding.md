---
repo: KBS_Monitoring_v2_260418
remote: https://github.com/mw3love/KBS_Monitoring_v2_260418.git
stack: [Windows, batch, PowerShell]
tags: [.bat, 인코딩, 한글깨짐, chcp, cmd.exe, mojibake, UTF-8, BOM]
used: []
---

# .bat 파일 한글 깨짐 — chcp 65001은 못 믿는다

## 함정

한글이 포함된 `.bat`(`python313_전환.bat` — 실행 줄에 같은 이름의 한글 `.ps1` 파일명을 참조)이
일부 PC에서 "명령이 아닙니다" 오류로 실행 자체가 실패했다(cmd 창이 순식간에 닫혀 원인 파악도 어려움).

시도 1: `chcp 65001 >nul`을 `@echo off` 다음 줄에 추가 + 파일을 UTF-8 BOM으로 저장.
→ dev PC(Windows 10)에서 **더 나빠짐** — cmd.exe는 PowerShell(.ps1)과 반대로 **.bat의 UTF-8 BOM을
지원하지 않는다.** BOM 바이트가 `@echo off` 자체를 깨뜨려 전체 줄이 그대로 에코됨.

시도 2: BOM 제거, `chcp 65001` + UTF-8(BOM 없음) + CRLF로 재조정(`실행.bat`이 이미 쓰던 조합과 동일하게 맞춤).
→ dev PC에서는 통과했지만, **실제 실패했던 Windows 11 PC(관리자 권한 실행)에서 완전히 동일한 증상으로 재발.**
`chcp 65001`이 배치파일 **자체를 파싱하는 시점**에 실제로 적용되는 타이밍이 Windows 빌드마다 다른 것으로 추정
(일부 빌드는 chcp 실행 전에 이후 줄을 미리 읽어들인다는 보고 있음 — 근본원인 확정은 못 함).
→ **`chcp 65001`로 "코드페이지를 맞추는" 접근 자체가 신뢰할 수 없다.**

## 해법

코드페이지를 맞추려 하지 말고, **`.bat`의 실행 줄에 비-ASCII 텍스트를 아예 안 쓴다.**

- 같은 베이스명의 `.bat`/`.ps1` 쌍이면(`python313_전환.bat` ↔ `python313_전환.ps1`),
  `"%~dp0python313_전환.ps1"`(파일명을 텍스트로 타이핑) 대신 **`"%~dpn0.ps1"`**
  (현재 실행 중인 배치파일 **자신의** 경로에서 확장자만 교체 — cmd가 OS 경로 정보에서
  프로그램적으로 가져오므로, 텍스트 재인코딩 문제 자체가 발생하지 않는다) 사용.
- `echo` 메시지도 영문으로 교체해 파일 전체를 순수 ASCII로 만든다(`file` 명령으로 "ASCII text" 확인 가능).
- `chcp 65001`은 남겨둬도 무해하지만(다른 환경에 도움 될 수도 있음), **의존하지는 않는다.**

dev PC(Windows 10)와 실패했던 실제 Windows 11 PC(관리자 권한 실행 포함) 양쪽에서 재현→해결 확인 완료.

## 대가

없음. 파일명 자체는 한글 그대로 유지 가능(사용자에게 익숙한 이름 유지) — 실행 줄에서만 텍스트 참조를 안 할 뿐.
단, `.bat`와 `.ps1`가 **같은 베이스명**이어야 `%~dpn0.<ext>` 트릭이 성립한다(이름이 다르면 이 방법 자체가 안 통함).

## 관련

이 프로젝트의 `실행.bat`에 이미 남아있던 경고 주석("ASCII-only comments: non-ASCII REM lines break batch
parsing on some PCs under chcp 65001")이 정확히 같은 계열의 함정을 먼저 지적하고 있었다 — 처음부터
따랐어야 했다.
