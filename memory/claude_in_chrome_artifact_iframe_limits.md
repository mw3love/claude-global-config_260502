---
name: claude-in-chrome-artifact-iframe-limits
description: claude-in-chrome 브라우저 자동화가 claude.ai 아티팩트 뷰어의 iframe 내부를 스크롤·조회 못하는 한계와 우회법
metadata:
  type: reference
---

`mcp__claude-in-chrome__*` 도구로 `claude.ai/code/artifact/...` 페이지(내가 게시한 Artifact)를 열면,
실제 콘텐츠는 cross-origin 샌드박스 iframe 안에 렌더된다. 이 환경에서 실측(2026-09-05, Eng Shorts
프로젝트 세션)한 제약:

- **스크롤 안 됨** — `computer` 도구의 `scroll`(휠), `key`(PageDown/End) 둘 다 iframe 내부 스크롤에
  전혀 반응 없음(페이지가 항상 최상단에 고정). 바깥 래퍼(claude.ai 헤더)만 있는 outer document는
  `scrollHeight`가 작고(예: 613px), 실제 콘텐츠는 iframe 안에 있어 outer window 스크롤로는 안 움직임.
- **`find`(접근성 트리) 안 됨** — iframe 안 요소는 접근성 트리에 전혀 안 잡힘("존재하지 않음" 오류).
- **`javascript_tool`로 iframe 내부 접근 안 됨** — `iframe.contentWindow.document` 접근 시
  "Blocked a frame with origin ... from accessing a cross-origin frame" 에러.
- **`resize_window`로 뷰포트를 늘려 스크롤 우회하는 것도 화면 해상도 제약에 걸림** — 창 높이가
  화면의 50% 이상 벗어나면 거부됨.
- **`computer`의 클릭(`left_click` 등)은 정상 작동** — 뷰포트 안에 실제로 보이는 좌표는 클릭 가능
  (진짜 OS 레벨 합성 입력이라 iframe 경계와 무관). 문제는 스크롤로 그 좌표까지 도달할 수 없다는 것.

**우회법 (실측 성공)**
1. **레이아웃/시각 확인** — 게시한 아티팩트의 로컬 HTML 파일을 `python -m http.server`로 로컬
   서빙(`http.server`는 charset 헤더를 안 보내 한글이 깨지므로, 테스트용 사본에
   `<meta charset="utf-8">`를 앞에 붙여서 서빙)한 뒤 그 `http://127.0.0.1:PORT/...` 로 새 탭에서
   열면 진짜 iframe이 아니라 최상위 문서라 스크롤·스크린샷이 정상 작동. 단 `window.claude.*`
   capability는 당연히 없음(순수 정적 파일이라 claude.ai 런타임이 안 붙음) — 레이아웃 검증 전용.
2. **`db`/`artifact` 등 capability 동작 확인** — 실제 claude.ai 호스팅이 필요하므로, 검증하고 싶은
   위젯만 담은 **최소 probe 아티팩트**(뷰포트 최상단, 스크롤 없이 보이는 위치)를 별도로 하나 더
   게시해 그 자리에서 클릭·`read_db`로 왕복 확인한 뒤, 실제 콘텐츠는 원래 아티팩트(스크롤이 필요한
   위치)에 반영. 확인 끝나면 probe 문서는 `write_db`(delete)로 정리.

**적용 시점** — Artifact에 인터랙션 위젯(특히 스크롤 필요한 위치에 있는 것)을 추가하고
전역 CLAUDE.md 규칙 11-d(자체확인)를 지키려 할 때. "스크롤이 안 되네" 자체를 스턱루프로
붙잡지 말고 바로 이 우회법으로 전환.
