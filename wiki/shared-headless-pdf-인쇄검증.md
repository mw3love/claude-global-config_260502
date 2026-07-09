---
shared: true
repos:
  - Notion_PDF_Preview_260706 (https://github.com/mw3love/Notion_PDF_Preview_260706.git)
stack: [headless-chrome, Python, pymupdf]
tags: [인쇄검증, headless, print-to-pdf, pymupdf, fitz, get_pixmap, 육안검증, PDF스크린샷불가, 프록시검증]
reuse: 인쇄(print) 출력물을 실제로 육안 검증해야 하는 모든 프로젝트 — 화면 렌더가 아니라 PDF 인쇄 결과
used: []
---

# 인쇄물(print) 출력을 육안 검증하는 법

WYSIWYG 인쇄가 "화면과 같게" 나오는지 **에이전트가 직접 눈으로** 확인해야 하는데, 인쇄 출력은 화면 스크린샷과 다르다(규칙 11-c: 프록시 아닌 실조건 검증).

## 함정 — PDF는 headless 스크린샷으로 못 본다

headless Chrome의 화면 스크린샷은 **인쇄용 페이지 조판(@page·페이지 경계)을 반영하지 않는다.** 화면을 찍어봐야 "인쇄가 맞는지"를 증명 못 한다(프록시 검증 함정).

## 해법 — print-to-pdf → 픽셀 렌더 → 육안

1. **headless Chrome `--print-to-pdf`** 로 실제 인쇄 경로를 태워 PDF를 뽑는다.
2. **`pymupdf`(fitz) `page.get_pixmap()`** 으로 각 페이지를 PNG로 렌더.
3. 그 PNG를 `Read`로 **육안 확인**.

- **`pdftoppm`(poppler) 없이** `pip install pymupdf` 만으로 렌더된다(외부 바이너리 불요).
- 페이지 경계·형광펜/네모박스 인쇄 여부·페이지박스 mm 매칭까지 실제 인쇄 산출물에서 확인된다.
