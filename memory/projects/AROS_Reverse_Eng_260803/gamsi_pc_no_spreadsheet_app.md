---
name: gamsi-pc-no-spreadsheet-app
description: "감시운용PC엔 스프레드시트 앱이 하나도 없음(Excel·LibreOffice·한컴·WPS 전부 미설치) — 대신 G:\\내 드라이브(구글 드라이브)로 다른 PC와 파일을 주고받음, 2026-09-17 확인"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0eb004fa-d91c-42f5-bc91-33ab27801bff
  modified: 2026-09-17T03:11:59.671Z
---

감시운용PC(`C:\Users\user\Dev-Mw\AROS_Reverse_Eng_260803`, git identity `mw`/`7maker@gmail.com`)에는
**스프레드시트 앱이 하나도 설치돼 있지 않다** — Excel(COM `REGDB_E_CLASSNOTREG`)·LibreOffice
(`soffice.exe` 없음)·한컴오피스(`C:\Program Files*\Hnc` 없음)·WPS 전부. `.xlsx` 파일 연결
프로그램도 등록돼 있지 않다(설치목록 레지스트리 3곳 전수 확인, 2026-09-17).

대신 **구글 드라이브가 `G:\`로 마운트돼 있다**(`G:\내 드라이브`, 2026-09-17 기준 여유 52GB).
사용자가 다른 PC에서 열어야 하는 산출물은 여기로 옮기면 된다 — 이날 현장 대조 체크리스트를
`G:\내 드라이브\CIMON 현장대조\`에 두고 다른 PC에서 채우기로 했다.

**Why:** 이 PC는 CIMON 화면에서 5m라 현장 대조의 주 무대인데, 정작 **그 결과를 적을 도구가
없다.** 「엑셀로 뽑아 드립니다」가 여기서는 완결된 산출물이 아니라는 뜻이고, 전역 규칙 11-d의
자체 렌더 확인도 원리적으로 불가능하다(앱이 없어 열어볼 수가 없음). 앱이 있으리라 넘겨짚고
`.xlsx`를 만들어 「확인해 보세요」로 넘기면 사용자가 열지도 못한 채 왕복이 한 번 는다.

**How to apply:** 이 PC에서 스프레드시트·문서 산출물을 만들면 ⓐ 렌더 검증은 「불가(앱 없음)」로
명시하고 ⓑ 전달은 `G:\내 드라이브` 경유 또는 git 커밋(다른 개발PC에서 `pull`)으로 잡는다.
반대로 **이 PC에서 바로 쓰게 하려면 브라우저로 가는 것(대시보드에 폼을 붙이거나 단독 로컬
HTML)이 유일한 길**이다 — 브라우저는 대시보드를 쓰므로 확실히 있다.
관련: [[project-d-cimon-s-on-gamsi-pc]]
