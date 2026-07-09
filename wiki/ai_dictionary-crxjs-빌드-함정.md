---
repo: AI_Dictionary_260622
remote: https://github.com/mw3love/AI_Dictionary_260622.git
stack: [crxjs, Vite, Chrome Extension MV3]
tags: [crxjs, vite, rollupOptions, 팝업HTML, 아이콘경로, publicDir, 이중emit]
used: []
---

# crxjs (Vite 크롬 확장 플러그인) 빌드 함정

## 함정 1 — 팝업 HTML이 변환 안 됨

crxjs에서 팝업 HTML이 **manifest 엔트리가 아니면** Vite가 변환하지 않아 dist에 안 나오거나 원본 그대로 나온다.

**해법:** manifest 엔트리가 아닌 HTML은 **`vite` 설정 `rollupOptions.input` 에 명시적으로 등록**해야 변환된다.

## 함정 2 — 아이콘 경로 해석 순서 & 이중 emit

crxjs 매니페스트 아이콘 경로는 **`<root>/경로` → 없으면 `<publicDir>/경로`** 순으로 찾아, 해싱 없이 그대로 dist에 출력한다.

**함정:** Vite의 `public` 자동 복사와 crxjs의 아이콘 emit이 **이중으로 겹칠 수 있다.**

**해법:** 아이콘을 **루트 `icons/`** 에 둔다 (publicDir이 아니라). 그러면 public 자동 복사와 crxjs emit이 겹치지 않는다.
