# 기안문 작성 규칙

> 마지막 업데이트: 2026-08-26 (규칙 10 추가 — 새 양식 이미지는 References/에 저장 + 항목구조 절 반영 확인. 기안문 항목 구조에 "유형 B: 구매형" 추가)

---

## 서식 규칙

1. 기안문 첫 줄은 **제목 텍스트만** 적는다 — 볼드 없이, `제목:` 접두어 없이. (사용자가 이 줄을 잘라내 결재시스템 제목칸으로 옮기기 때문.) 수신·경유 줄도 작성하지 않는다.
2. 목차 넘버링 순서는 1 → 가 → (1) 순서로 한다.
3. 문서는 가급적 A4 한 장에 맞춰서 작성하고, 최대 두 장을 넘지 않도록 한다.
4. 첨부 목록의 마침표는 두 곳에만 사용한다: **마지막 첨부명 끝**에 `.` 하나, 그 뒤 두 칸 띄고 `끝.` 하나. 중간 항목에는 마침표를 붙이지 않는다.
   - 올바른 예: `1. 사업개요서 1부` / `2. 견적서 1부.  끝.`
   - 잘못된 예: `1. 사업개요서 1부.` / `2. 견적서 1부.  끝.`
5. 기안문 하단 첨부 목록은 `붙임` 대신 **`첨부 :`** 로 표기한다.

---

## 작성 규칙

6. 관련근거는 항상 **KBS 내부 문서**만 기재한다.
   - 외부기관(교통안전공단, 국토교통부 등) 공문·점검결과는 관련근거에 기재하지 않는다.
   - **예외 — 접수번호가 있는 경우**: 외부기관 공문이라도 KBS가 *접수*하여 문서시스템에 등록된 번호(예: `접수 전주방송총국-1420 (2026.06.04.)`)가 있으면, 그 접수번호·날짜로 관련근거에 기재한다. 이때 형식은 `부서명-번호 (날짜.)  「문서 제목」`을 그대로 쓰고, 문서 제목은 받은 공문의 제목을 「」로 감싼다.
   - 외부기관 내용이 공사 배경이 되는 경우(접수번호도 없을 때), 본문 공사사유 항목에서 서술로 언급한다.
   - 관련근거로 사용할 내부 문서가 없으면 관련근거 항목 자체를 생략한다.
   - 관련근거 문서 제목은 「」로 감싼다.
   - 형식: `부서명-번호 (날짜.)  「문서 제목」`
   - 날짜는 소괄호 안에 `YYYY.MM.DD.` 형식으로 기재
   - 사용자가 날짜를 별도 제공하지 않으면 **빈 괄호 `( )`** 로 남겨둔다 (주석/플레이스홀더 불필요)

6-b. **관련근거는 작성 전에 사용자에게 확인한다.**
   - KBS 기안문은 통상 본문 첫 항목이 관련근거이므로, 소스에서 관련근거(부서명-번호·날짜·문서 제목)가 명확히 잡히지 않으면 작성을 시작하기 전에 사용자에게 묻는다.
   - 질문 예: "관련근거로 넣을 문서가 있나요? (접수/시행 번호·날짜·제목)" — 없다고 하면 그때 항목을 생략한다.
   - 추측으로 생략·기재하지 말 것. (이 한 번의 질문이 "생략→다시 추가" 왕복을 없앤다.)
7. 표가 필요한 부분은 적극적으로 구현한다.

8. **핵심 미확정값은 [작성]으로 채우기 전에 먼저 묻는다.**
   - 본문에 들어갈 실질값(시공/계약업체, 작업·공사 기간, 금액·예산과목, 계약방법, 작업대상 수량 등) 중 소스에서 명확히 잡히지 않는 항목은, 저가 견적·"미정" 등으로 조용히 채우지 말고 **작성 시작 전 `AskUserQuestion`(선택창)으로 먼저 확인**한다.
   - 여러 항목이 비면 한 번의 `AskUserQuestion`에 묶어 묻는다(최대 4문항). 각 항목엔 합리적 기본값을 "(추천)"으로 제시한다.
   - 사용자가 "추측해서 채워라" 또는 "미정으로 둬라"라고 명시하면 그때 채우고 검증표에서 [작성]으로 표기한다. (관련근거는 규칙 6-b가 별도로 강제 — 중복 적용)

9. **구매 물품 단가는 기본적으로 VAT 미포함(공급가액) 기준으로 표기한다.**
   - 영수증·견적서 등 소스에 공급가액/부가세액이 구분되어 있으면, 구매내역 표의 단가는 공급가액(VAT 미포함)을 기본값으로 쓴다.
   - VAT 포함 총액으로 표기해야 하는 경우는 사용자가 명시적으로 요청했을 때만 그 값으로 대체한다.

---

## 기안문 항목 구조

문서 성격에 따라 구조가 다르다. 소스·참고문서로 유형이 명확히 판단되면 맞는 쪽을 쓰고, 애매하면 사용자에게 확인한다. 항목은 상황에 따라 가감한다.

### 유형 A — 공사·사업형 (시설 공사, 용역 등)

```
1. 관련근거
2. 공사(사업) 사유
3. 공사(사업) 개요  ← 표로 구현
4. 공사(사업) 내용
5. 기대 효과

첨부 :  1. ...
        2. ...  끝.
```

### 유형 B — 구매형 (물품 구매)

참고: `References/260203 모악산송신소 집수정 순환펌프 구매(구매형 양식 예시).png`, `References/250305 모악산(송) 식당 직원용 식탁 구입(구매형 양식 예시).png`

```
(본문 인트로 한 줄 — "~목적으로 다음과 같이 ~를 구매하고자 합니다.")

1. 구매 개요/구매품목
   가. 품 명 : ...
   나. 가 격 : 총 ...원 (수량 * 단가, 부가세 포함/미포함 명시)
   ← 품목·단가·수량·합계·비고 표로 구현
   (인터넷 최저가 등 변동 가능성 있으면 표 하단에 "※ ..." 비고)

2. 예산과목 : (계정과목명)(코드)

3. 협조사항 : (있는 경우만 — 예: 자산 등재 업무 (담당부서))

첨부 :  1. ...  끝.
```

- 단가는 규칙 9(VAT 미포함 기본값)를 따른다. 단, 소스가 오픈마켓 소비자가처럼 VAT 구분이 없는 총액이면 "(부가세 포함)"으로 명시한다.
- 협조사항은 자산 등재·설치 등 타 부서 후속 업무가 실제로 있을 때만 넣는다 — 소스에 없으면 사용자에게 확인 후 결정한다(규칙 8).

---

## 새 양식 이미지·문서를 받으면 (규칙 10)

10. 사용자가 이전에 쓰던 결재 양식(스크린샷·문서)을 새로 보여주면:
   - 그 이미지/문서를 `References/` 폴더에 저장한다. 파일명은 `[YYMMDD 시행일자] [사업명](양식 성격 메모).png` 형식으로, 기존 References 파일명 관례를 따른다.
   - 그 구조가 위 "기안문 항목 구조" 절의 기존 유형과 다르면, 새 유형으로 추가할지 사용자에게 확인 후(규칙 6) 반영한다. 이미 있는 유형과 같으면 저장만 하고 구조 절은 건드리지 않는다.
   - 이 저장·반영은 규칙 6단계(규칙 업데이트 제안) 승인 절차를 그대로 따른다 — 묻지 않고 조용히 파일만 추가하지 않는다.

---

## 출력 형식

기안문은 **HTML 파일 하나**로 저장한다. md·txt 파일은 작성하지 않는다.

- 파일명: `기안문_[사업명 요약].html`
- 저장 위치: 해당 기안 사전자료 폴더 내
- 구조: `<!DOCTYPE>` 없이 **fragment 형태**로 작성 (아래 HTML 스타일 규칙 준수)

---

## HTML 기안문 스타일 규칙

### 문서 시작 구조

```html
<p style="..."><meta charset="UTF-8"></p>
<style>
  body { font-family: "굴림체", "Gulim", sans-serif; font-size: 12pt; line-height: 24px; margin: 40px 60px; color: #000; }
  p { margin-top: 0px; margin-bottom: 0px; }
</style>
```

> **중요 — `<style>` 블록은 브라우저 미리보기용일 뿐이다.** HWP·KOBIS(결재시스템) 등 리치텍스트 편집기에 붙여넣으면 `<style>` 블록은 통째로 제거되고 **인라인 스타일만 살아남는다.** 따라서 표의 테두리·너비·배경·글꼴은 절대 `<style>` 블록의 `table{}`·`td{}` 선택자에 의존하지 말고 **모든 `<table>`/`<td>` 태그에 인라인으로** 넣는다. (본문 `<p>`도 이미 전부 인라인 스타일이라 동일 이유로 안전하다.)

### 본문 텍스트

- 모든 `<p>` 태그에 인라인 스타일 포함: `style="font-family: 굴림체; font-size: 12pt; line-height: 24px; margin-top: 0px; margin-bottom: 0px;"`
- 단어 사이 공백: `&nbsp;`
- 들여쓰기:
  - 가/나 항목 (2단계): `&nbsp;&nbsp;` (2칸)
  - (1)/(2) 항목 (3단계): `&nbsp;&nbsp;&nbsp;&nbsp;` (4칸)
- 빈 줄: `<p style="..."><br></p>`

### 표(table) — 전부 인라인 (KBS 편집기 네이티브 포맷)

붙여넣기 시 깨지지 않도록 **모든 스타일을 인라인으로** 둔다. `<tbody>`로 행을 감싸고, 표 속성(너비·collapse·테두리·글꼴크기)은 `<table>` 태그에, 셀 테두리는 `<td>`마다 반복한다.

```html
<table border="1" cellspacing="0" cellpadding="0" style="word-break: break-all; font-size: 12pt; width: 643px; border-collapse: collapse; border: 1px solid rgb(0, 0, 0);">
  <tbody>
    <tr>
      <td style="border: 1px solid rgb(0, 0, 0); width: 90px; height: 20px; padding: 2px 5px; background-color: rgb(242, 242, 242); text-align: center;"><p style="font-family: 굴림체; font-size: 12pt; line-height: 24px; margin-top: 0px; margin-bottom: 0px; font-weight: bold;">구분</p></td>
      <td style="border: 1px solid rgb(0, 0, 0); width: 430px; height: 20px; padding: 2px 5px; background-color: rgb(242, 242, 242); text-align: center;"><p style="font-family: 굴림체; font-size: 12pt; line-height: 24px; margin-top: 0px; margin-bottom: 0px; font-weight: bold;">내용</p></td>
      <td style="border: 1px solid rgb(0, 0, 0); width: 123px; height: 20px; padding: 2px 5px; background-color: rgb(242, 242, 242); text-align: center;"><p style="font-family: 굴림체; font-size: 12pt; line-height: 24px; margin-top: 0px; margin-bottom: 0px; font-weight: bold;">비고</p></td>
    </tr>
    <tr>
      <td style="border: 1px solid rgb(0, 0, 0); height: 20px; padding: 2px 5px; text-align: center;"><p style="font-family: 굴림체; font-size: 12pt; line-height: 24px; margin-top: 0px; margin-bottom: 0px;">검사대상</p></td>
      <td style="border: 1px solid rgb(0, 0, 0); height: 20px; padding: 2px 5px;"><p style="font-family: 굴림체; font-size: 12pt; line-height: 24px; margin-top: 0px; margin-bottom: 0px;">내용 텍스트(좌측 정렬)</p></td>
      <td style="border: 1px solid rgb(0, 0, 0); height: 20px; padding: 2px 5px;"><p style="font-family: 굴림체; font-size: 12pt; line-height: 24px; margin-top: 0px; margin-bottom: 0px;"><br></p></td>
    </tr>
  </tbody>
</table>
```

세부 규칙:
- **표 태그**: `style="word-break: break-all; font-size: 12pt; width: 643px; border-collapse: collapse; border: 1px solid rgb(0, 0, 0);"`
- **모든 `<td>`**: `border: 1px solid rgb(0, 0, 0); height: 20px; padding: 2px 5px;` 인라인 필수. 첫 행 셀에 `width:`로 열 너비 지정.
- **셀 안쪽 여백**: 텍스트가 테두리에 딱 붙지 않도록 각 `<td>`에 `padding: 2px 5px;`(좌우 5px) 인라인. 수동 `&nbsp;` 띄어쓰기로 여백 주지 말 것 — 셀 padding이 좌우 균일하게 적용되고 편집기에서 다시 열어도 유지(round-trip)되며 내용 텍스트를 오염시키지 않는다.
- **셀 글꼴**: 본문과 같은 **굴림체** (`<p>`에 인라인). `<td>` 자체엔 글꼴 안 둠.
- **헤더 행**: 각 셀에 `background-color: rgb(242, 242, 242); text-align: center;` + `<p>`에 `font-weight: bold;`
- **열 너비 기본 패턴**: 구분 90px / 내용 430px / 비고 123px (= 643px). 표 내용에 맞게 가감.
- **정렬**: 구분·비고 등 짧은 열은 `text-align: center;`, 긴 내용 열은 좌측(미지정).
- **빈 셀**: `<p style="..."><br></p>`로 채운다.

### 첨부 목록 정렬

`1.` 과 `2.` 이하 항목의 숫자가 세로로 정렬되어야 한다.

```html
<p ...>첨부&nbsp;:&nbsp;&nbsp;1.&nbsp;사업개요서&nbsp;1부</p>
<p ...>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.&nbsp;견적서&nbsp;1부.&nbsp;&nbsp;끝.</p>
```

- `첨부 :` 뒤 `&nbsp;&nbsp;`(2칸) + `1.` 시작
- 2번 이하: 앞에 `&nbsp;` 8칸으로 `1.`의 숫자와 세로 정렬

---

## 미확인 사항 처리

작성 중 모르는 부분이 있으면 참고문서의 기본 양식 형태를 따라 최대한 비슷하게 작성한다.
