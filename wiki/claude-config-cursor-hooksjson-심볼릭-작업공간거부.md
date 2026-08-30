---
repo: claude-global-config
remote: https://github.com/mw3love/claude-global-config_260502.git
stack: [Cursor, hooks, macOS]
tags: [Cursor, hooks.json, 심볼릭링크, symlink, workspace, Shell, Bash, pre-push, doc-sync]
used: []
---

# Cursor user hooks.json: 작업공간 안 심볼릭 링크는 안 읽힌다

## 함정
`~/.cursor/hooks.json` → `~/.claude/cursor-hooks/hooks.json` 심볼릭 링크를 달고 Cursor를 재시작해도, 에이전트 `git push`가 문지기를 우회했다. 초인종 스크립트는 한 번도 시작되지 않음(호출 로그 없음).

1차 가설은 훅 PATH에 python이 없다는 것. `.sh` 래퍼로 PATH를 채워도 동일. 같은 증상 두 번째.

실제 원인(Output → Hooks 로그):
- 작업공간이 `~/.cursor` 이면 `Refusing to load User hooks.json via symlink below workspace root`.
- 빈 창(작업공간 없음)에서는 같은 링크가 로드됨.
- Cursor는 그와 별개로 `~/.claude/settings.json` 훅을 **이미 실행**하고 있었다. 그런데 Claude PreToolUse는 `tool_name == "Bash"` 만 보고, Cursor는 `"Shell"` 을 넣는다 → 침묵 통과. 거부를 내도 Claude JSON(`hookSpecificOutput`)이라 Cursor는 "valid response 없음"으로 무시.

## 해법
- `hooks.json` 은 심볼릭 링크가 아니라 **실파일 복사**. `hooks/` 스크립트 폴더만 링크.
- Claude `pre-push-doc-sync-hook.py` 가 `Shell` 도 보고, `cursor_version` 있으면 Cursor 거부 JSON(`permission: deny`)을 낸다.

## 대가
- 복사본은 원본이 바뀌면 post-merge가 다시 덮어써야 한다. 링크처럼 즉시 따라오지 않음.
- 작업공간이 `~/.cursor`가 아닌 일반 프로젝트에서는 심볼릭 링크도 로드됐을 수 있다. 거부는 "workspace root 아래 링크" 조건.
