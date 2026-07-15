# -*- coding: utf-8 -*-
"""
hwp_edit.py — 한글(.hwp) 파일 재사용 편집 헬퍼
================================================================
[무엇을 해결하나]
  매번 .hwp 편집 로직(열기·XML파싱·수정·저장)을 새로 짜던 것을
  한 클래스로 굳혀, 앞으로는 아래 세 줄이면 끝나게 한다.

  from hwp_edit import HwpDoc
  with HwpDoc("양식.hwp") as doc:
      doc.set_cell(1, 2, ["5,047"], append=True)   # (행,열) 셀 채우기
      doc.replace("2025년", "2027년")               # 문서 전체 찾아바꾸기
      doc.save("작성본.hwp")

[동작 원리]
  한글 COM으로 문서를 열어 HWPML2X(XML)로 통째로 받아와,
  그 XML을 lxml로 편집한 뒤 다시 한글에 돌려주고 한글이 저장한다.
  → 저장은 한글이 직접 하므로 표 정렬·글꼴·서식이 원본 그대로 보존된다.

[전제]
  · Windows + 한글(한컴오피스) 설치 PC
  · pip install pywin32 lxml
  · 열기/저장 시 한글 "보안 승인" 창이 뜨면 [허용] 클릭
    (이 PC는 보안모듈 미등록 상태 — 승인창을 끄려면 별도 등록 필요)

[셀 주소를 모를 때]
  python hwp_edit.py "양식.hwp"      ← 표의 모든 셀 (행,열)=내용 을 덤프
"""
import copy
import os
import sys

from lxml import etree
import win32com.client as win32

# 콘솔 인코딩(cp949)에서 한글 출력 시 크래시 방지
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _ln(tag):
    """네임스페이스를 뗀 로컬 태그명."""
    return etree.QName(tag).localname


class HwpDoc:
    """한글 문서 하나를 열어 XML로 편집하고 저장하는 컨텍스트 매니저."""

    def __init__(self, path, verbose=True):
        self.path = os.path.abspath(path)
        self.verbose = verbose
        self.hwp = None
        self.root = None
        self._cells = None
        self._decl = ""   # 원본 XML 선언(SetTextFile에 그대로 되돌려줘야 함)

    # ── 로그 ──
    def _log(self, *a):
        if self.verbose:
            print(*a)
            sys.stdout.flush()

    # ── 열기 ──
    def open(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError(self.path)
        self._log("한/글 실행 중...")
        self.hwp = win32.DispatchEx("HWPFrame.HwpObject")
        # 보안모듈이 등록돼 있으면 승인창을 건너뛴다(미등록이면 조용히 실패 → 창 뜸)
        self.hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
        # ★ 창을 반드시 보이게 한다. 안 그러면 열기/저장 시 뜨는 보안 승인창이
        #   화면에 안 나와 클릭 불가 → 무한 대기(좀비). visible=True 필수.
        try:
            self.hwp.XHwpWindows.Item(0).Visible = True
        except Exception:
            pass
        self._log("문서 여는 중... (보안 승인 창이 뜨면 [허용] 클릭)")
        # 한글 버전에 따라 Open이 포맷/인자 3개를 요구한다(NEO 등).
        # 인자 1개만 넘기면 "매개 변수 개수" COM 오류가 나므로 3개 명시.
        if not self.hwp.Open(self.path, "", ""):
            raise RuntimeError("열기 실패: " + self.path)
        xml = self.hwp.GetTextFile("HWPML2X", "")
        # ★ 원본 XML 선언을 보존한다. 이 선언이 없으면 SetTextFile이 입력을
        #   HWPML 구조가 아니라 '평문'으로 인식해, 전체 마크업을 글자로 삽입해
        #   문서를 20여 페이지 깨진 상태로 만든다(실측). 저장 때 그대로 되돌린다.
        self._decl = xml[:xml.find("?>") + 2] if xml.startswith("<?xml") else ""
        self.root = etree.fromstring(
            xml.replace('encoding="UTF-16"', 'encoding="UTF-8"')
               .replace('encoding="utf-16"', 'encoding="UTF-8"')
               .encode("utf-8")
        )
        self._index_cells()
        return self

    def _index_cells(self):
        self._cells = {}
        for e in self.root.iter():
            if _ln(e.tag) == "CELL":
                key = (e.get("RowAddr"), e.get("ColAddr"))
                self._cells[key] = e

    # ── 표 셀 ──
    def cells(self):
        """{(row, col): '셀 안 텍스트'} 사전 — 셀 주소 파악용."""
        out = {}
        for (r, c), cell in self._cells.items():
            out[(int(r), int(c))] = self._cell_text(cell)
        return out

    def _cell_text(self, cell):
        parts = []
        for ch in cell.iter():
            if _ln(ch.tag) == "CHAR" and ch.text:
                parts.append(ch.text)
        return "".join(parts)

    def get_cell(self, row, col):
        cell = self._cells.get((str(row), str(col)))
        if cell is None:
            raise KeyError("셀 없음: (%s, %s)" % (row, col))
        return self._cell_text(cell)

    def _make_p(self, ref_p, text):
        """서식 참조 문단(ref_p)을 복제해 텍스트만 바꾼 새 <P>."""
        p = copy.deepcopy(ref_p)
        texts = [c for c in p if _ln(c.tag) == "TEXT"]
        for t in texts[1:]:
            p.remove(t)
        t0 = texts[0]
        for ch in list(t0):
            t0.remove(ch)
        t0.text = None
        if text:
            char = etree.SubElement(t0, t0.tag.replace("TEXT", "CHAR"))
            char.text = text
        return p

    def set_cell(self, row, col, lines, append=False):
        """
        (row, col) 셀 내용 설정.
          lines  : 문단 리스트 (각 원소가 한 줄)
          append : True면 기존 내용 뒤에 추가, False면 교체
        """
        if isinstance(lines, str):
            lines = [lines]
        cell = self._cells.get((str(row), str(col)))
        if cell is None:
            raise KeyError("셀 없음: (%s, %s)" % (row, col))
        paralist = [c for c in cell if _ln(c.tag) == "PARALIST"][0]
        ps = [c for c in paralist if _ln(c.tag) == "P"]
        new_ps = [self._make_p(ps[0], t) for t in lines]
        if not append:
            for p in ps:
                paralist.remove(p)
        for np in new_ps:
            paralist.append(np)
        return self

    # ── 찾아바꾸기 ──
    def replace(self, old, new):
        """문서 전체에서 old→new 텍스트 치환. 바꾼 횟수를 반환."""
        n = 0
        for e in self.root.iter():
            if _ln(e.tag) == "CHAR" and e.text and old in e.text:
                n += e.text.count(old)
                e.text = e.text.replace(old, new)
        return n

    def find(self, text):
        """text가 든 CHAR들의 주변 문맥 리스트(확인용)."""
        hits = []
        for e in self.root.iter():
            if _ln(e.tag) == "CHAR" and e.text and text in e.text:
                hits.append(e.text)
        return hits

    # ── 저장 ──
    def save(self, out_path=None, fmt="HWP"):
        """
        편집한 XML을 한글에 돌려주고 저장.
          out_path : None이면 원본 덮어쓰기, 아니면 새 경로로 SaveAs
          fmt      : "HWP"(기본) / "HWPX" / "PDF" 등 한글 SaveAs 포맷
        """
        body = etree.tostring(self.root, encoding="unicode")
        # ★ 반드시 원본 선언을 앞에 붙인다(open에서 보존). 안 붙이면 문서 깨짐.
        new_xml = (self._decl + body) if self._decl else body
        self.hwp.SetTextFile(new_xml, "HWPML2X", "")
        target = os.path.abspath(out_path) if out_path else self.path
        # 덮어쓰기 확인창을 줄이려 기존 출력본은 미리 삭제
        if out_path and os.path.exists(target):
            try:
                os.remove(target)
            except Exception as e:
                self._log("기존 출력본 삭제 실패(무시 가능):", e)
        self._log("저장 중... (보안/확인 창이 뜨면 [허용]/[예] 클릭)")
        ok = self.hwp.SaveAs(target, fmt, "")
        # 실제 디스크 저장 검증
        if os.path.exists(target):
            import time
            age = time.time() - os.path.getmtime(target)
            if age < 120:
                self._log("[성공] 저장 완료: %s (%d bytes)"
                          % (target, os.path.getsize(target)))
            else:
                self._log("[주의] 파일은 있으나 갱신 안 됨 — 저장 창을 클릭했는지 확인")
        else:
            self._log("[실패] 출력 파일 없음 — 보안 승인 창에서 [허용]을 눌렀는지 확인")
        return ok

    # ── 종료 ──
    def close(self):
        if self.hwp is not None:
            try:
                self.hwp.Clear(1)
                self.hwp.Quit()
            except Exception:
                pass
            self.hwp = None

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


# ── CLI: 셀 주소 덤프 ──
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('사용법: python hwp_edit.py "파일.hwp"   (표의 모든 셀 주소·내용 덤프)')
        sys.exit(1)
    with HwpDoc(sys.argv[1]) as doc:
        print("─" * 50)
        print("(행, 열) = 내용")
        print("─" * 50)
        for (r, c), txt in sorted(doc.cells().items()):
            preview = (txt[:40] + "…") if len(txt) > 40 else txt
            print("(%d, %d) = %s" % (r, c, preview))
