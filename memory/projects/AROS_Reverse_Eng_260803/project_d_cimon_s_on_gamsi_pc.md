---
name: project-d-cimon-s-on-gamsi-pc
description: "감시운용PC의 D:\\CIMON S — 서버 설치 트리 전체 사본(공식 매뉴얼 CimonD.chm 포함)이 이 PC 로컬에 붙어 있음, 2026-08-26 확인"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9337b8b3-8ada-4d8f-9a23-f323af4f4ab7
  modified: 2026-08-26T09:52:59.477Z
---

감시운용PC(`C:\Users\user\Dev-Mw\AROS_Reverse_Eng_260803`, git identity `mw`/`7maker@gmail.com`)에
`D:\CIMON S` 전체 트리가 **로컬로** 붙어 있다. CIMON 서버 설치 폴더 통째 사본 —
루트 파일 359개 + `전주센터`/`Samples`/`Sys`/`ArosSys` 등 13개 하위 폴더, 그리고
**`D:\CIMON S\CimonD.chm`(공식 매뉴얼 56,635,888 bytes)** 포함. `전주센터` 안에는
`전주센터.dbx`·`CimonDbm.mdb`(2026-08-03 15:26)와 `.ALog` 365개(20250804~20260803)가 있다.

**Why:** 이건 *이 PC에만* 해당하는 사실이라 repo의 CLAUDE.md에 못 쓴다(다른 개발PC에선
D 드라이브가 없거나 다른 내용이라 틀린 서술이 된다 — 전역 규칙 10-c). 반대로 CLAUDE.md는
"이 외장HDD는 mw-lenovo 전용, 상시 연결 아님"이라고 서술하고 있어, 이 PC에서 `D:\CIMON S`를
마주치면 "그럴 리 없다"고 넘겨짚기 쉽다.

**How to apply:** 이 PC에서 CIMON 원본 파일이 필요하면 두 경로가 있다 —
`\\10.20.30.40\c\CIMON\...`(서버 라이브, `CIMON_PROJECT_ROOT`가 가리키는 곳)과
`D:\CIMON S\...`(2026-08-03 시점 정지 스냅샷). 최신 데이터가 필요하면 전자, 서버 공유가
닫혔거나 mw-lenovo에서 하던 작업을 재현할 땐 후자. **매뉴얼(`CimonD.chm`)은 양쪽 다 동일**하므로
서버 공유와 무관하게 언제든 열 수 있다. 다음에 이 PC에서 볼 때 D 드라이브가 여전히 붙어
있는지부터 재확인할 것(이 메모는 2026-08-26 시점 관찰).
