#!/usr/bin/env python3
# UserPromptSubmit hook: 전역 CLAUDE.md 규칙 11-b(스턱루프 트립와이어)의 트리거를 외부화한다.
#
# 왜 훅인가 — 2026-07-11 규칙 감사(173세션): "같은 증상을 두 번째로 보고하는 순간"이라는
# 트리거를 Claude가 판정하게 두었더니 실제 스턱루프 35건에 발화 1건이었다. 카운팅을
# 훅으로 옮겨(transcript_path를 직접 파싱) "두 번째인가"를 기계가 세게 한다.
# 남는 판정("같은 증상인가")은 어휘로 판별 불가라 Claude에게 되돌려주되, 스킵 경로에도
# 산출물(한 줄)을 강제해 조용한 무시를 막는다.
#
# 발화 조건(둘 다):
#   1. 이번 프롬프트가 좌절 패턴(A군 반복부사 × B군 실패어휘, 같은 문장)에 매치
#   2. 리셋 앵커 이후 좌절 매치가 이번 것 포함 2회 이상  (첫 좌절엔 완전 침묵)
# 리셋 앵커: assistant가 이미 '🔁 스턱루프' 블록을 낸 지점 — 접근을 전환했으면 새로 센다.
#
# UserPromptSubmit은 exit 0 + 평문 stdout이 그대로 컨텍스트로 주입된다(이 이벤트의 특례).
# 미발화 시엔 아무것도 출력하지 않는다.
import sys, os, json, re

THRESHOLD = 2          # 좌절 발화 2회째에 발화 (규칙 11-b 원문)
MAX_QUOTE = 160        # 주입문에 인용할 이전 프롬프트 길이 상한
# 리셋 앵커는 이모지 하나(🔁)로 통일한다. 규칙 11-b는 🔁를 스턱루프 관련(접근 전환/스킵)에만
# 쓰므로, 내가 그 신호에 반응한(접근 전환했든, 다른 증상으로 스킵했든) 시점 이후로 새로 센다.
# '🔁 스턱루프'만 앵커로 잡으면 '🔁 스킵'이 카운터를 못 비워 오탐 1건이 세션을 오염시킨다(S3).
RESET_ANCHOR = "🔁"

# TIER1(단독 발화): "고쳤는데 여전히 안 풀렸다"를 거의 모호함 없이 가리키는 강한 신호.
#   한국어 좌절은 대개 부정어 없이 이 어휘만으로 끝난다("그대로인데?", "여전히 느려").
#   지시문 오해 방지: 그대로/똑같은 '좌절 어미'(그대로인데/똑같아…)만 잡고
#   '그대로 둬'·'똑같이 만들어'는 제외한다.
RE_STRONG = re.compile(
    r"여전히|아직도|변함\s*없|변함이\s*없|변한\s*게\s*없|바뀐\s*게\s*없|바뀌지\s*않"
    r"|나아지지\s*않|고쳐지지\s*않|안\s*고쳐지|안\s*고쳐졌|해결\s*(이\s*)?안|변화\s*(가|는)?\s*없"
    r"|그대로(인데|네|야|임|이야|이네|던데|더라|고)|똑같(아|은데|네|음|던데|더라|은\s*결과)"
    r"|still\s+(not|no\b|broken|fail|doesn|does\s+not|the\s+same|same)"
    r"|same\s+(error|issue|problem|result|thing|bug|behavior)"
    r"|no\s+change|no\s+difference|not\s+fixed|isn'?t\s+fixed"
    r"|didn'?t\s+(help|work|change|fix)|doesn'?t\s+(help|work|fix)|nope",
    re.IGNORECASE,
)
# TIER2(반복어 × 부정어, 같은 문장): 반복/동일을 가리키는 흔한 말은 진짜 부정어와
#   결합할 때만 좌절로 본다. 반복어 단독(계속·다시·또 추가)·명사(에러·실패·버그)는 발화하지 않는다.
RE_REPEAT = re.compile(r"그대로|똑같|동일|마찬가지|또(?![\s]*(다른|한|는))|역시|재차|again", re.IGNORECASE)
RE_NEG = re.compile(
    r"안\s*(되|돼|됨|난다|나온|나와|나옴|먹|뜨|열|보여|보이|바뀌|생겨|생김|고쳐|잡)|안돼|안됨|안된"
    r"|못\s*(하|해|함|나|열|보|잡)|작동\s*(안|하지\s*않|못)|동작\s*(안|하지\s*않|못)"
    r"|실행\s*(이\s*)?안|반응\s*(이\s*)?없|먹통|튕기|깨지"
    r"|not\s+work|doesn'?t\s+work|does\s+not\s+work|won'?t\s+work|fail(s|ed|ing)?|broken|no\s+luck",
    re.IGNORECASE,
)


def strip_noise(text):
    """코드블록·인라인코드·인용줄·시스템 태그 제거 — 붙여넣은 로그의 'still failing' 오탐 차단."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " ", text)
    # 알려진 래퍼 태그만 통째 제거. 일반 <tag>…</tag>를 DOTALL로 지우면 그 사이에 낀
    # 좌절 문장까지 먹으므로(S7), 태그명을 특정한다. system-reminder는 user_text가 이미 처리.
    text = re.sub(r"<(command-name|command-message|command-args|local-command-stdout)>.*?</\1>",
                  " ", text, flags=re.S)
    text = re.sub(r"</?[a-zA-Z][^>]*>", " ", text)  # 남은 홑따옴표 태그만 제거(부등호 수식 <30초 보존)
    text = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith(">"))
    return text


def is_frustration(text):
    """강한 좌절어(TIER1)가 단독으로 나오거나, 반복어와 부정어가 '같은 문장'에 함께 나오면 좌절."""
    if not text:
        return False
    clean = strip_noise(text)
    for sent in re.split(r"[.!?…;\n]+", clean):
        if RE_STRONG.search(sent):
            return True
        if RE_REPEAT.search(sent) and RE_NEG.search(sent):
            return True
    return False


def user_text(entry):
    """실제 사용자 발화만 추출. tool_result·슬래시명령·훅주입 턴은 제외."""
    msg = entry.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        parts = [content]
    elif isinstance(content, list):
        parts = [b.get("text", "") for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
    else:
        return ""
    text = "\n".join(p for p in parts if p)
    if not text.strip():
        return ""
    if "<command-name>" in text or "<local-command-stdout>" in text:
        return ""
    return re.sub(r"<system-reminder>.*?</system-reminder>", " ", text, flags=re.S)


def assistant_text(entry):
    msg = entry.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text")
    return ""


def prior_hits(transcript_path):
    """리셋 앵커 이후의 좌절 발화 목록(오래된 것부터)."""
    hits = []
    if not transcript_path or not os.path.isfile(transcript_path):
        return hits
    with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            t = entry.get("type")
            if t == "assistant":
                if RESET_ANCHOR in assistant_text(entry):
                    hits = []          # 접근을 전환했으므로 카운터 리셋
            elif t == "user":
                text = user_text(entry)
                if text and is_frustration(text):
                    hits.append(text.strip())
    return hits


def clip(s, n=MAX_QUOTE):
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n] + "…"


def main():
    # stdin을 바이너리로 읽어 UTF-8로 명시 디코딩한다. sys.stdin.read()는 Windows에서
    # 로케일(cp949)로 디코딩해 한글 프롬프트가 깨지고, 그러면 패턴이 영영 매치되지 않는다.
    raw = sys.stdin.buffer.read().decode("utf-8", "replace")
    if not raw.strip():
        return
    try:
        payload = json.loads(raw)
    except Exception:
        return

    prompt = str(payload.get("prompt") or "")
    if not is_frustration(prompt):
        return                                   # 좌절 어휘 없음 — 침묵

    hits = prior_hits(str(payload.get("transcript_path") or ""))
    # 훅 실행 시점에 이번 프롬프트가 이미 transcript에 적혔을 수 있다 — 중복 카운트 방지
    if not (hits and hits[-1] == prompt.strip()):
        hits.append(prompt.strip())

    if len(hits) < THRESHOLD:
        return                                   # 첫 좌절 보고는 정상 버그 리포트 — 침묵

    previous = "\n".join("  %d) %s" % (i + 1, clip(h)) for i, h in enumerate(hits[:-1]))

    sys.stdout.write(
        "[stuck-loop hook] 이 세션에서 좌절 어휘가 담긴 사용자 보고가 %d번째입니다. "
        "전역 CLAUDE.md 규칙 11-b(스턱루프 트립와이어)의 트리거 조건입니다.\n\n"
        "이전 좌절 보고:\n%s\n\n"
        "이번 보고:\n  %s\n\n"
        "훅은 '몇 번째인가'만 셌을 뿐, '같은 증상인가'는 판정하지 못합니다. "
        "그 판정은 당신이 하되 **조용히 넘어갈 수 없습니다** — 답변 맨 위에 아래 둘 중 "
        "정확히 하나를 반드시 출력하세요.\n\n"
        "(가) 같은 증상의 반복이면 — 같은 메커니즘에 3번째 패치를 제안하지 말고:\n"
        "  🔁 스턱루프 — 접근 전환\n"
        "  구조적 한계: {지금 메커니즘이 왜 이 증상을 원리적으로 못 잡는가, 한 줄}\n"
        "  다른 메커니즘: {A / B / C — 트레이드오프 한 줄씩}\n"
        "  → 사용자와 방향을 정한 뒤 진행합니다. 정말 대안이 없으면 '대안 없음'을 "
        "근거와 함께 명시하고 계속하는 이유를 대세요. '거의 됐다'는 느낌은 트리거를 "
        "무효화하지 못합니다.\n\n"
        "(나) 서로 다른 증상이면 (훅의 오탐) — 한 줄만 남기고 평소대로 진행:\n"
        "  🔁 스킵 — 다른 증상: {이전 증상} vs {이번 증상}\n"
        % (len(hits), previous, clip(hits[-1], 300))
    )


try:
    sys.stdout.reconfigure(encoding="utf-8")
    main()
except Exception as e:
    sys.stderr.write("[stuck-loop-hook] error: %s\n" % e)
sys.exit(0)
