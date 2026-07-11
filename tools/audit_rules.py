#!/usr/bin/env python3
"""전역 CLAUDE.md 규칙 감사 — 각 규칙이 '실제로 발화했는가'를 세션 기록으로 측정한다.

사용법:
    PYTHONIOENCODING=utf-8 python ~/.claude/tools/audit_rules.py

배경: 2026-07-11 감사(173세션)에서 규칙 22개 → 17개로 개편. 결론은
"규칙의 발화를 가른 건 내용·중요도·개수가 아니라 형태"였다.
  - 훅(기계적 강제)      → doc-sync 114회. 최다. 모델 판단을 안 거치기 때문.
  - 산출물 강제(라벨·한 줄) → 세션당 다수. 토큰을 찍으려면 판정을 실제로 해야 한다.
  - 성향 + 모델이 판정하는 트리거 → 거의 0회.

━━ 이 스크립트를 다시 짤 때 반드시 알아야 할 함정 2개 ━━
(1) 단순 grep은 전부 오염된다.
    스킬 이름과 CLAUDE.md 규칙 본문이 *모든 세션의 시스템 프롬프트에 주입*되므로
    `grep -r "self-review"` 는 세션 수만큼 히트한다(첫 시도에서 전부 150+로 나왔다).
    → 반드시 type=="assistant" 의 text 블록과 tool_use 블록만 추출해서 세야 한다.
(2) 사용자가 친 슬래시 명령과 Claude의 자발적 스킬 호출은 기록 형태가 다르고,
    서로 겹치지 않는다(173세션 전수 확인: 둘 다 있는 세션 0개).
      - 사용자가 침       → user 턴 텍스트의 <command-name>/self-review</command-name>
      - Claude가 자발 호출 → assistant 의 tool_use (name="Skill", input.skill="self-review")
    이 구분이 규칙 11의 인과를 증명한 핵심이다. 섞으면 결론이 통째로 무너진다.

가장 신뢰할 수 있는 지표는 '규칙이 만든 어휘'가 아니라 '사용자가 손으로 개입한 횟수'다.
규칙 11만 인과가 깨끗했던 이유가 그것이다(도입 후 사용자 수동 요구 38→0).
규칙이 발명한 단어(예: "프록시검증")의 빈도는 어휘 채택만 증명할 뿐 판단 개선은 증명 못 한다.
"""
import json
import os
import re
import sys
import glob
import collections
from datetime import date

# 출력에 ⏳·✓·✗가 섞인다. Windows 콘솔 기본 cp949로는 인코딩 불가라
# UnicodeEncodeError로 죽는다(2026-07-11 실측: '⏳ 판정보류'가 처음 출력되며 크래시).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.expanduser("~/.claude/projects")
TODAY = date.today().isoformat()

# ── 측정할 규칙: (라벨, CLAUDE.md 추가일, 지문, 플래그) ────────────────────────
#   지문 종류: ("skill", 스킬명) | ("cmd", "/슬래시명령") | ("re", 정규식 → assistant 발언에서)
#            | ("tool", 도구명 → assistant tool_use, 예: AskUserQuestion)
#   함정 (3): 도구를 ("skill", …)로 적으면 영영 0이다. skills는 name=="Skill"인 tool_use만
#            담고 input.skill로 세므로, AskUserQuestion처럼 이름이 곧 도구인 것은 못 잡는다.
#            0으로 잡히면 '사문화'로 오판해 멀쩡한 규칙을 자르게 된다 → 반드시 ("tool", …).
#   ("re", …)는 re.M으로 돈다 — ^…$ 앵커가 줄 단위로 걸린다.
#   플래그(선택):
#     "goal_zero" — 0이 성공인 줄. 사용자가 손으로 개입한 횟수 같은 것.
#                   (이걸 '사문화'로 찍으면 정반대로 읽힌다)
#   추가 후 세션이 MIN_SESSIONS 미만이면 '사문화'로 단정하지 않고 판정을 보류한다 —
#   갓 심은 규칙을 죽었다고 표시하면 멀쩡한 규칙을 잘라낸다.
#   새 규칙을 추가하면 여기 한 줄만 넣으면 된다.
MIN_SESSIONS = 15   # 이만큼 세션이 쌓이기 전엔 사문화 판정 보류

RULES = [
    # ── 2026-07-11 개편으로 새로 심은 규칙들. 다음 재감사의 본체.
    #    0회면 그 규칙도 죽은 것 — 옛 규칙 4·6-b를 자른 것과 같은 기준으로 자른다.
    ("규칙2 '손안의 카드' 한 줄",      "2026-07-11", ("re", r"손안의 카드")),
    ("규칙11-b '🔁 스턱루프' 블록",     "2026-07-11", ("re", r"🔁 ?스턱루프")),
    ("규칙7 '검토한 대안:' 한 줄",      "2026-07-11", ("re", r"검토한 대안\s*:")),
    ("규칙10-b '세션 상태:' 한 줄",     "2026-07-11", ("re", r"세션 상태\s*:")),
    # ── 2026-07-11 저녁 2차: 10-b 블록의 내부 형식. '세션 상태:'가 발화한 뒤
    #    그 안이 규격대로인지를 잰다. 세션 상태 발화 수보다 적으면 형식이 새는 것.
    ("규칙10-b '커밋 상태:' 마지막 줄", "2026-07-11", ("re", r"커밋 상태\s*:")),
    ("  └ 권장 항목 '▸ 프롬프트:' 라벨", "2026-07-11", ("re", r"^\s*▸\s*프롬프트\s*[:：]")),
    ("  └ 선택창 '지금 이어서'",        "2026-07-11", ("tool", "AskUserQuestion:이어서")),
    # 규칙 7-b(비유)는 오래된 성향 문장이라 측정조차 안 됐다. 2026-07-11에 '**비유:**'
    # 라벨을 강제해 비로소 셀 수 있게 만들었다. 라벨 없는 본문 속 '비유'라는 낱말은 세지
    # 않는다 — 이 규칙을 *논의*하는 답까지 먹어 오염되기 때문. 굵게 라벨 형태만 잡는다.
    # 실측 baseline(2026-07-11): 추가 前 10회 / 173세션 = 0.06회per세션.
    #   → 오염이 아니라 진짜 발화율이다. 성향 문장이 거의 죽어 있었다는 방증(17세션에 1회).
    # ⚠ 해석 함정: 라벨 강제 *이전*엔 라벨 없는 비유가 안 잡힌다. 그래서 8월에 수치가
    #   올라도 "비유가 늘었다"로 읽으면 안 된다 — 라벨링이 늘어난 것일 수 있다(교란).
    #   before/after 상승분이 아니라 **절대 발화율(세션당)**로만 판단하라.
    ("규칙7-b '비유:' 라벨",           "2026-07-11", ("re", r"\*\*비유\s*[:：]")),
    # 규칙7 그릇 조항(2026-07-11): 데이터 모양에 그릇을 맞춘다 — 표 / 트리 / 목록.
    # 표는 지문화하지 않는다: 마크다운 표 문법(|---|)은 내가 늘 쓰던 것이라 baseline이
    # 높아 '규칙이 살아있다'는 거짓 신호가 된다(함정 ⓓ). 트리 문자는 드물어 지문이 된다.
    ("규칙7 트리(포함관계) 코드블록",     "2026-07-11", ("re", r"├──|└──")),
    # 버린 지문 2개(2026-07-11 실측) — 오염돼 '거짓 살아있음'을 만든다:
    #   ("re", r"\*\*\d+\.\s")  굵은 수동 번호 → 추가 前 이미 200회(평소 쓰는 굵은 번호 목록을 다 먹음)
    #   ("tool", "AskUserQuestion") 통째로 → 추가 前 이미 260회(아무 질문에나 쓰는 범용 도구)
    # 그래서 선택창은 질문 문구('지금 이어서')로 좁혀 10-b 전용 지문만 센다. 넓은 지문은
    # 규칙이 죽어도 높게 나와 '거짓 안심'을 만든다 — 함정 (1)과 같은 오염이다.
    # ── 기존 규칙(대조군)
    ("규칙11 self-review 자동실행",   "2026-06-24", ("skill", "self-review")),
    ("  └ 사용자 수동 /self-review",  "2026-06-24", ("cmd", "/self-review"), "goal_zero"),
    ("규칙3 '확인 필요'",             "2026-05-06", ("re", r"확인\s*필요")),
    ("규칙7 '추천:' 명시",            "2026-06-11", ("re", r"추천\s*:")),
    ("규칙11-c 프록시/실조건 표기",     "2026-06-11", ("re", r"프록시\s*검증|실조건\s*검증")),
    ("규칙4-b/4-c reference-repos",  "2026-06-24", ("skill", "reference-repos")),
    ("규칙10 doc-sync (훅)",          "2026-05-23", ("skill", "doc-sync")),
    # ── 삭제된 규칙(사문화 확인용 — 되살릴지 판단할 때 참고)
    ("[삭제] 규칙6-b pick-skill",     "2026-06-11", ("skill", "pick-skill")),
    ("[삭제] 규칙4 'No only way'",    "2026-05-06", ("re", r"다른 방법이 있을 수")),
]


def load():
    """세션 기록을 파싱해 (일자별 assistant 발언, 일자별 스킬 호출, 일자별 슬래시 명령,
    일자별 세션 집합)을 돌려준다. 시스템 프롬프트는 절대 섞이지 않는다 — 함정 (1)."""
    atext = collections.defaultdict(list)
    skills = collections.defaultdict(collections.Counter)
    cmds = collections.defaultdict(collections.Counter)
    sessions = collections.defaultdict(set)
    tools = collections.Counter()
    # 일자별 tool_use 이름. skills와 별개다 — skills는 name=="Skill"인 것만 담고
    # input.skill로 세는데, AskUserQuestion 같은 '도구 그 자체'는 거기 안 잡힌다.
    tools_day = collections.defaultdict(collections.Counter)

    for f in glob.glob(os.path.join(ROOT, "**", "*.jsonl"), recursive=True):
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                day = (d.get("timestamp") or "")[:10]
                if not day:
                    continue
                sessions[day].add(f)
                msg = d.get("message") or {}
                content = msg.get("content")

                if d.get("type") == "assistant" and isinstance(content, list):
                    for b in content:
                        if not isinstance(b, dict):
                            continue
                        if b.get("type") == "text":
                            atext[day].append(b.get("text", ""))
                        elif b.get("type") == "tool_use":
                            name = b.get("name", "")
                            tools[name] += 1
                            tools_day[day][name] += 1
                            if name == "Skill":
                                skills[day][(b.get("input") or {}).get("skill", "?")] += 1
                            elif name == "AskUserQuestion":
                                # 도구 이름만으로는 못 센다 — 아무 질문에나 쓰므로.
                                # 규칙 10-b 선택창은 질문 문구가 '지금 이어서 …'다. 그것만 센다.
                                q = json.dumps(b.get("input") or {}, ensure_ascii=False)
                                if "지금 이어서" in q:
                                    tools_day[day]["AskUserQuestion:이어서"] += 1

                elif d.get("type") == "user":
                    txt = ""
                    if isinstance(content, str):
                        txt = content
                    elif isinstance(content, list):
                        txt = " ".join(b.get("text", "") for b in content
                                       if isinstance(b, dict) and b.get("type") == "text")
                    for c in re.findall(r"<command-name>(/[a-z-]+)</command-name>", txt or ""):
                        cmds[day][c] += 1

    return atext, skills, cmds, sessions, tools, tools_day


def window(atext, skills, cmds, tools_day, sessions, start, end):
    days = [d for d in sessions if start <= d < end]
    txt = "\n".join(t for d in days for t in atext[d])
    sk, cm, tl = collections.Counter(), collections.Counter(), collections.Counter()
    for d in days:
        sk.update(skills[d])
        cm.update(cmds[d])
        tl.update(tools_day[d])
    return txt, sk, cm, tl, len({f for d in days for f in sessions[d]})


def value(metric, txt, sk, cm, tl):
    kind, arg = metric
    if kind == "re":
        return len(re.findall(arg, txt, re.M))
    if kind == "skill":
        return sk[arg]
    if kind == "cmd":
        return cm[arg]
    if kind == "tool":
        return tl[arg]
    raise ValueError(kind)


def main():
    atext, skills, cmds, sessions, tools, tools_day = load()
    total = len({f for d in sessions for f in sessions[d]})
    print(f"세션 {total}개 · 도구 호출 {sum(tools.values())}건\n")

    print("=== 규칙별 발화율: 추가 전 vs 추가 후 (괄호=세션당) ===")
    print(f"{'규칙':32s} {'추가일':11s} {'추가 前':>14s} {'추가 後':>14s}  변화")
    print("-" * 92)
    for label, added, metric, *rest in RULES:
        flag = rest[0] if rest else ""
        pre = window(atext, skills, cmds, tools_day, sessions, "2026-01-01", added)
        post = window(atext, skills, cmds, tools_day, sessions, added, TODAY)
        a, b = value(metric, *pre[:4]), value(metric, *post[:4])
        ra = a / pre[4] if pre[4] else 0
        rb = b / post[4] if post[4] else 0

        if flag == "goal_zero":
            # 0이 성공인 줄 — 사문화로 찍으면 정반대로 읽힌다.
            mark = "✓ 목표달성(0)" if b == 0 else f"⚠ 아직 {b}회 개입"
        elif post[4] < MIN_SESSIONS:
            # 갓 심은 규칙. 발화 0이어도 죽었다고 단정하면 멀쩡한 규칙을 자른다.
            mark = f"⏳ 판정보류 (도입 후 {post[4]}세션)"
        elif b == 0:
            mark = "✗ 사문화"
        elif rb > ra * 2:
            mark = "↑↑"
        elif rb > ra:
            mark = "↑"
        else:
            mark = "↓"
        print(f"{label:32s} {added}  {a:5d} ({ra:5.2f})  {b:5d} ({rb:5.2f})  {mark}")

    print("\n=== Skill 실제 호출 (시스템 프롬프트 언급 아님) ===")
    agg = collections.Counter()
    for d in skills:
        agg.update(skills[d])
    for k, v in agg.most_common():
        print(f"  {k:20s} {v}")

    print("\n=== self-review: 사용자가 손으로 시킨 것 vs Claude 자발 (겹치지 않음) ===")
    for d in sorted(set(skills) | set(cmds)):
        u, a = cmds[d]["/self-review"], skills[d]["self-review"]
        if u or a:
            print(f"  {d}  사용자{u:2d} {'U'*u:10s} 자동{a:2d} {'A'*a}")
    print("\n  ※ 가장 신뢰할 지표는 '사용자가 손으로 개입한 횟수'다 —")
    print("     규칙이 만든 어휘의 빈도는 어휘 채택만 증명할 뿐 판단 개선은 증명 못 한다.")


if __name__ == "__main__":
    main()
