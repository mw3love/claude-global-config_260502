---
repo: PDF_Maker_260406
remote: https://github.com/mw3love/PDF_Maker_260406.git
stack: [Python, pywin32, 한컴오피스COM, Windows]
tags: [HWP, 한글, SaveAs, PDF, 모아찍기, 2-up, nup, PrintToPDFEx, PrintMethod, Hancom, 가로출력, landscape]
used: []
---

# 한글(HWP) 자동화 SaveAs("PDF")가 2-up 모아찍기로 저장되는 함정

## 증상
`hwp.SaveAs(dst, "PDF", "")`로 PDF 저장 시, 한글 편집기에서는 세로 1쪽씩
멀쩡한 문서가 PDF에서는 **A4 가로 한 장에 세로 2쪽이 나란히**(2-up) 박혀 나온다.
세로 6쪽 원본 → 가로 3장. 사용자는 "쪽수가 이상하다"로 인지.

## 함정 (막다른 길 — 값은 여기 있다)
원인은 `SaveAs("PDF")`가 **한컴에 저장돼 있던 인쇄 '모아 찍기' 설정
(`PrintMethod=4` = 2쪽)** 을 그대로 물려받는 것. PDF 저장이 내부적으로
Hancom PDF 프린터 경유 인쇄 파이프라인이라 인쇄 설정에 종속된다.

안 통한 것들:
1. `HAction.GetDefault("FileSaveAsPdf", ...)` 로 기본값을 받아 저장해도
   여전히 2-up (GetDefault가 이 설정을 리셋하지 못함).
2. `SaveAs` 3번째 인자(옵션 문자열)로도 n-up 제어 안 됨.
3. 레지스트리 `HKCU\Software\HNC\Shared\9.6\Print Setting` 을 뒤졌으나
   모아찍기 값이 binary DevMode/불명확해 여기서 못 끔.

## 해법
`SaveAs` 대신 **`PrintToPDFEx` 액션 + `PrintMethod=0`(1쪽씩)** 을 명시한다:

```python
pset = hwp.HParameterSet.HPrint
hwp.HAction.GetDefault("PrintToPDFEx", pset.HSet)
pset.PrinterName = "Hancom PDF"
pset.FileName    = str(dst)
pset.PrintMethod = 0      # 0=자동 인쇄(1쪽씩) / 4=2쪽 모아찍기
pset.PrintToFile = 1
hwp.HAction.Execute("PrintToPDFEx", pset.HSet)
```

- `PrintMethod`: 0=1쪽씩, 3=자동 모아찍기, 4=2쪽 모아찍기. **0이 핵심.**
- 프린터 스풀은 **비동기** → Execute 직후 파일이 없을 수 있다. 파일 존재+
  크기 안정화까지 폴링 대기(예: 크기 연속 2회 동일 → 완료).
- `Execute()` 반환이 False(프린터 부재 등)면 `SaveAs`로 폴백(2-up이라도 생성).
- 근거: 한컴 개발자 포럼 https://forum.developer.hancom.com/t/saveas-pdf/1670
- 실조건검증 2026-07-22: 실제 원본 6쪽 → 세로 6쪽(595×841) 정상, errors 없음,
  사용자 exe 우클릭 실검증 통과.

## 대가
- `PrintToPDFEx`는 "Hancom PDF" 프린터 이름에 의존 → 그 프린터가 없는 PC면
  폴백 SaveAs로 떨어져 2-up이 재현될 수 있음(한컴 설치 시 보통 함께 설치됨).
- 스풀 비동기라 완료 대기 로직이 없으면 "파일 없음"으로 오판할 수 있음.
