---
repo: (범용 — 한글 HWP COM 자동화)
remote: 
stack: [Windows, 한글 NEO, win32com, HWPML2X, lxml]
tags: [hwp, 한글, HWPML2X, SetTextFile, GetTextFile, xml선언, 문서깨짐, pyhwpx, 보안모듈]
used: []
---

# 한글 HWPML2X 왕복 편집 — 문서가 20여 페이지 마크업으로 깨지는 함정

한글 COM(`HWPFrame.HwpObject`)으로 `.hwp`를 편집할 때, 문서를 `GetTextFile("HWPML2X")`로 XML로 받아 lxml로 고치고 `SetTextFile(...,"HWPML2X")`로 되돌리는 하이브리드가 있다(한글이 직접 저장하므로 서식 100% 보존). 이때 겪은 함정들.

## 함정 1 (핵심) — XML 선언(`<?xml?>`) 빠지면 문서가 통째로 깨진다

`etree.tostring(root, encoding="unicode")`는 **XML 선언을 안 붙인다**(unicode 모드는 선언 불가). 그 문자열을 `SetTextFile`에 넘기면, 한글이 입력을 **HWPML 구조가 아니라 '평문'으로 인식**해 **전체 마크업(`Top=`, `CELL`, `BorderFill`, `function OnDocument_New()` …)을 글자 그대로 본문에 삽입** → 20여 페이지 깨진 문서 + 마지막 장에 원본. 증상: 저장본을 열면 앞쪽이 온통 XML 태그 텍스트.

**해법:** `open` 때 원본 선언을 보존했다가 `SetTextFile` 입력 앞에 그대로 붙인다.
```python
decl = xml[:xml.find("?>")+2] if xml.startswith("<?xml") else ""   # GetTextFile 직후
# ...편집...
new_xml = decl + etree.tostring(root, encoding="unicode")           # SetTextFile 직전
```
한글 NEO 9.6이 뱉는 실제 선언: `<?xml version="1.0" encoding="UTF-16" standalone="no" ?>`. BSTR(UTF-16)로 전달되므로 encoding=UTF-16 명시가 자연스럽다.

**검증법(희망고문 방지):** 저장본을 다시 `Open`해 `hwp.PageCount`가 폭증(20+) 안 했는지, 재취득 XML에 `BorderFill=`/`CELLMARGIN`이 CHAR 텍스트로 대량 삽입됐는지로 깨짐 판별. 페이지수 1 + 셀값 정상이면 통과.

## 함정 2 — Open은 인자 3개를 요구 (버전별)

한글 NEO에서 `hwp.Open(path)` 1인자는 `com_error: 매개 변수의 개수가 잘못되었습니다`. **`hwp.Open(path, "", "")` 3인자** 명시. `SaveAs(path, "HWP", "")`도 3인자.

## 함정 3 — 보안 승인창은 레지스트리 등록만으론 못 없앤다(관리자 없을 때)

파일 열기/저장마다 "접근 허용" 승인창이 뜬다. `pyhwpx`가 `HKCU\Software\HNC\HwpUserAction\Modules`에 `FilePathCheckerModule` DLL을 등록해도, **DLL을 regsvr32로 COM 등록(관리자 권한)** 까지 안 되면 승인창이 계속 뜬다. 또 `visible=False`/백그라운드로 돌리면 창이 **화면에 안 뜬 채 무한 대기**(좀비 프로세스) → 반드시 `visible=True`+포그라운드.

**실용 해법:** 자동 억제를 포기하고, 창이 뜨면 **[모두 허용(A)] 한 번** 클릭(그 실행의 열기+저장+재열기 모두 커버). 사용자가 늘 옆에 있는 대화형 워크플로면 충분.

## 함정 4 — early-binding 캐시(gen_py) 오염

`DispatchEx` 시 gen_py 캐시가 깨져 `RegisterModule`이 조용히 무력화되거나 `_get_good_object_` circular import 경고. 캐시 재빌드 후엔 동작. 문제 지속 시 `%LOCALAPPDATA%\Temp\gen_py` 삭제.
