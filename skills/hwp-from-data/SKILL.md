---
name: hwp-from-data
description: |
  데이터를 바탕으로 한글(.hwp) 문서·양식의 표 칸을 채워 완성본을 만든다.
  "이 데이터로 이 양식 채워줘", "hwp 양식 작성", "투자사업계획서 채워줘",
  "한글 문서 자동 작성" 류 요청에 사용. Windows + 한글(한컴오피스) 설치 PC 전용.
  단순 .hwp 열람·텍스트 추출만이면 쓰지 않는다(그건 GetTextFile 한 번이면 됨).
  .hwpx(zip+xml)만 다룰 땐 python-hwpx가 더 낫다 — 이 스킬은 이진 .hwp가 대상.
---

## 무엇 / 언제

데이터(md·표·사용자 지시)를 받아 한글 양식의 표 칸을 채워 작성본 .hwp를 만든다.
한글 COM으로 열고 저장하되 **편집은 HWPML2X(XML)를 lxml로** 한다 —
한글이 직접 저장하므로 표·서식이 원본 그대로 보존된다.

**비유:** 문서를 통째로 다시 짜지 않고, 한글에게 "이 표 이 칸에 이 글자"만 시키고
나머지는 한글이 원본 그대로 두게 하는 것. (붕어빵 틀은 그대로, 반죽만 붓기)

## 전제 (PC마다 1회 확인)

1. Windows + 한글(한컴오피스) 설치.
2. `pip install pywin32 lxml pyhwpx`
3. **보안모듈 1회 등록:** `python setup_pc.py` 실행(그 PC에서 딱 한 번).
   - 이걸 해도 이 PC 환경에 따라 승인창이 남을 수 있다(아래 함정 3).

## 절차

1. **셀 주소 파악** — `python hwp_edit.py "양식.hwp"` 로 표의 모든 (행,열)=내용 덤프.
2. **채우기** — `HwpDoc`로 열어 `set_cell(row, col, [줄들], append=?)` / `replace(old,new)`.
   - 라벨+값이 한 칸에 있으면 `append=True`(값이 라벨 아래 줄에 붙음).
3. **저장** — `doc.save("작성본.hwp")`. 원본은 건드리지 않고 새 파일로.
4. **검증(필수)** — 저장본을 **다시 열어** `hwp.PageCount`가 폭증(20+) 안 했는지,
   채운 셀 값이 남았는지 확인. 통과해야 "완료".

사용 예시:
```python
from hwp_edit import HwpDoc
with HwpDoc("양식.hwp") as doc:
    doc.set_cell(0, 1, ["모악산(송) 삭도 정기검사 수수료"])
    doc.set_cell(1, 2, ["5,047"], append=True)      # 라벨 아래 값
    doc.set_cell(6, 0, ["■ 사업개요", " 1) 추진사유", "  ㅇ ..."])
    doc.replace("2025년", "2027년")
    doc.save("작성본.hwp")
```

## 성공 기준

- 저장본 페이지수가 정상 범위(양식 원래 페이지수 ±1).
- 채운 칸 값이 재열기 후에도 그대로.
- 표·서식 시각적으로 멀쩡(사용자 눈 확인이 최종).

## 함정 (실제로 헛디딘 것들)

1. **XML 선언 누락 → 문서 20여 페이지 깨짐.**
   이렇게 하면 안 됨: `SetTextFile(etree.tostring(root, encoding="unicode"), "HWPML2X", "")`
   → 선언이 빠져 한글이 마크업을 '글자'로 삽입, 문서 붕괴.
   대신: `open`에서 원본 `<?xml?>` 선언 보존 → `save`에서 앞에 재부착.
   (hwp_edit.py에 반영됨. 상세: ~/.claude/wiki/hwp-hwpml2x-선언누락-문서깨짐.md)
2. **Open은 3인자.** `hwp.Open(path)` → COM 오류. `hwp.Open(path, "", "")`.
3. **승인창 + visible.** 열기/저장마다 보안 승인창이 뜬다. 레지스트리 등록만으론
   못 없앨 수 있음(관리자 권한 필요). 반드시 `visible=True`(안 그러면 창이 숨어
   무한 대기·좀비). 실용: 창 뜨면 [모두 허용(A)] 1클릭(그 실행 전체 커버).
4. **검증 없이 "완료" 금지.** 옛 스크립트가 문서를 깨뜨리고 있었는데 아무도
   안 열어봐서 몰랐다. 반드시 저장본 재열기로 페이지수·값 확인.
5. **백그라운드 실행 주의.** 승인창은 사람 클릭이 필요하니, 스크립트는
   포그라운드로 돌리고 사용자에게 "창 뜨면 [모두 허용] 클릭"을 안내한다.

## 자산 (이 폴더)

- `hwp_edit.py` — HwpDoc 엔진(열기·set_cell·replace·저장·셀덤프 CLI). 실검증 완료.
- `setup_pc.py` — PC마다 1회 보안모듈 등록.

새 PC 온보딩: 전역 git pull → `pip install pywin32 lxml pyhwpx` → `python setup_pc.py` → 끝.
