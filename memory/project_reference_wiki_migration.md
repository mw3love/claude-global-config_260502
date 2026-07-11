---
name: project-reference-wiki-migration
description: reference 지식을 repos.json 블롭에서 wiki/*.md로 이관 — 완료(전 repo 이관 끝)
metadata: 
  node_type: memory
  type: project
  originSessionId: ee19d96b-127b-468e-be1f-eaeef87add59
---

**2026-07-09 완료.** Notion(3493→375자, wiki 6개: notion-페이지분할기/에디터-크롬-제거/스냅샷-이미지인라인/css-격리-디버깅/미리보기-스크롤-ux + shared-headless-pdf-인쇄검증)까지 이관 끝. shared-형광펜의 dangling `[[notion-페이지분할-인쇄]]`→`[[notion-페이지분할기]]`로 수정. 커밋 a4fbaba. 남은 별건: post-commit 훅이 커밋마다 별도 이력커밋 생성(미해결, 이관과 무관).


`~/.claude`에서 reference 지식 저장을 **repos.json 한 줄 JSON 블롭 → `wiki/<repo>-<기법>.md` 파일 하나당 기법 하나** 로 재설계하는 작업. 2026-07-09 세션에서 시작, 대부분 완료.

**완료:**
- 정책 전환: CLAUDE.md 4-c, `reference-repos`·`doc-sync` 스킬 개정. 트리거를 스턱루프 하나로 축소(구 Type B 폐지), `used:` frontmatter로 인용 횟수 측정, `ref-cache/` gitignore.
- PasteFlow 이관 완료(2476→148자, wiki 6개).
- AI 사전 이관 완료(1184→237자, 고유 2 + 공유 2).
- **공유 위키 패턴 도입**: `shared-svg-png-래스터화-우회.md`(AI사전+Notion), `shared-형광펜-dom-range-직렬화.md`(AI사전+ReadingHighlighter+Notion). 여러 repo가 참조.
- 짧은 3개 repo(youtube_dual_subtitle 141자·전역Claude 219자·Reading_Highlighter 226자)는 함정 없어 손대지 않기로 확정.

**남은 일 — Notion_PDF_Preview_260706 이관(3493자, 최대):** remote `https://github.com/mw3love/Notion_PDF_Preview_260706.git`. 감사 결과 6파일 계획:
1. `notion-페이지분할기` — paged.js 0.4.3 Chrome149 조판멈춤 대체·재귀 그리디 블록 분할(표 tr단위·thead반복·lazy 빈페이지방지)·A2/A1은 @page size명명 없어 mm 명시·이미지 decode 강제
2. `notion-에디터-크롬-제거` — offsetHeight 0 판정(getBoundingClientRect는 absolute자식 잡혀 0 안나옴)·DB 컬렉션뷰 편집크롬 제거(난독화 클래스·:last-child는 읽기전용서 헤더 지울 위험·padding-inline:0 하면 float 붕괴로 표 전체 소멸)
3. `notion-스냅샷-이미지인라인` — 동일출처 스냅샷(link fetch·url()절대화·@page통제)·이미지 인라인(인증프록시→프리사인S3라 콘텐츠스크립트 fetch 불가→서비스워커 host_permissions CORS우회 data URL)·가상화 블록 실체화(스크롤 훑기)
4. `notion-css-격리-디버깅` — iframe srcdoc에 스냅샷+CSS 넣고 규칙 하나씩 켜 어느 CSS가 깨는지 격리(라이브에 클론 붙이면 페이지JS 간섭 위양성). 이미 예전 커밋 8b462fa에 있던 것
5. `notion-미리보기-스크롤-ux` — 썸네일 미니맵(cloneNode+scale)·IntersectionObserver 스크롤스파이(spyLock+scrollend 1500ms폴백)·하이브리드 이동(가까우면 smooth 멀면 instant)·webkit-scrollbar 무시될때 표준 scrollbar-color로 강제·레일 드래그리사이즈(4px)·커스텀커서 SVG halo
6. `shared-headless-pdf-인쇄검증` — headless chrome --print-to-pdf→pymupdf(fitz) get_pixmap 육안(PDF는 headless 스크린샷 안 됨). 프로젝트 무관 일반 기법이라 shared로.
   - Notion의 SVG→PNG·형광펜 인쇄귀속은 이미 shared-* 에 흡수됨 → Notion 파일에선 참조만.

**감사 기준(사용자 승인):** 스턱루프(코드로 복원 불가능한 막다른 길)만 위키에. "검색 5분짜리 일반지식"·"코드 읽으면 나오는 구현"은 탈락. 관련 함정끼리 묶어 과분할 방지. 중복은 shared-* 로.

**커밋 방식:** 새 wiki는 `git -C ~/.claude add -N <경로> && git commit <경로> -m` (add -N 없으면 untracked라 pathspec 실패, add … && commit 은 사용자 스테이징 삼킴 — 둘 다 실측). push 안 함. 이 세션 unpushed 6커밋 — 다음 세션이 다른 PC면 push 먼저 필요.

관련: [[project-commit-push-workflow-review]]
