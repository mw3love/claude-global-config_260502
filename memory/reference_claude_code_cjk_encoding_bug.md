---
name: reference-claude-code-cjk-encoding-bug
description: "AskUserQuestion 등에서 한글이 다른 글자로 바뀌어 보이면 폰트가 아니라 Claude Code 자체의 미해결 Windows CJK 디코딩 버그 — GitHub #65394/#42899"
metadata:
  node_type: memory
  type: reference
  originSessionId: 56a06508-19c9-4a47-a824-c7958e152963
  modified: 2026-08-10T00:00:34.544Z
---

**증상 구분이 핵심**: [[reference-terminal-font-d2coding]]이 고치는 건 "정렬만 어긋남"(글자는 맞는데 테두리가 안 맞음)이다. **글자 자체가 다른 글자로 바뀌는 것**(예: `뒤바뀌지`→`뒤바끈지`, `안녕하세요`→`안녕핐세요`)은 완전히 다른 버그이고 폰트로 고칠 수 없다.

**원인(2026-08-10 확인)**: Windows용 Claude Code CLI의 fullscreen TUI 렌더러가 UTF-8 멀티바이트 문자를 **바이트 단위로 Latin-1/CP1252로 오독**하는 알려진 미해결 버그. `chcp 65001`(콘솔 코드페이지를 UTF-8로 맞춤)을 적용해도 변화 없음 — 콘솔 코드페이지 문제가 아니라 Claude Code 앱 내부 디코딩 문제라는 게 이슈 작성자에 의해 직접 검증됨. `~/.claude` 설정 파일로는 고칠 수 없는, Anthropic 쪽 업스트림 버그.

**실제 재현(이 세션)**: AskUserQuestion 옵션에 "뒤바뀌지"를 정확히 작성해 호출했는데, 도구로 돌아온 answer 텍스트엔 "뒤바끈지"로 바뀌어 있었다. 선택한 옵션 **번호(인덱스)는 정확히 인식**됐다 — 깨지는 건 라벨 텍스트 왕복 쪽. 이 정확한 케이스(AskUserQuestion 왕복)는 아래 이슈들에 명시적으로 보고돼 있진 않지만, 같은 렌더러의 같은 바이트 오독 계열로 보인다.

**확인된 GitHub 이슈** (둘 다 URL 직접 열어서 실존 확인함, 둘 다 Closed):
- [#65394](https://github.com/anthropics/claude-code/issues/65394) — fullscreen renderer(기본값)가 붙여넣기 시 UTF-8을 Latin-1로 오독. `chcp 65001` 무효 확인. 우회법으로 `/tui default`가 언급됐으나 이 세션에선 `claude --help`에 해당 옵션이 없어 **미검증**.
- [#42899](https://github.com/anthropics/claude-code/issues/42899) — `CLAUDE_CODE_NO_FLICKER=1`이 Windows에서 한글 붙여넣기를 깨뜨림(WSL 미재현). 이 PC는 해당 env var 미설정 상태에서도 재현됐으므로 NO_FLICKER가 유일한 트리거는 아님.

**대응 원칙**: 한글이 다른 글자로 바뀌어 보인다는 보고를 받으면 먼저 이 메모리부터 확인 — 폰트 재설치나 코드페이지 조정으로 시간 쓰지 말 것(이미 무효로 확인됨). 업스트림 수정 전까지는 재현 조건 기록·우회법 시도 정도가 할 수 있는 전부.

관련: [[reference-terminal-font-d2coding]]
