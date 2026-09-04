import sys, json

# git clean 필터: settings.json이 git 인덱스로 들어갈 때(add/diff/commit)만
# PC마다 달라지는 모델 관련 키를 제거해서 보여준다. 워킹트리 파일 자체는 안
# 건드리므로 /model 은 평소처럼 정상 동작하고, git 쪽에서만 이 키들이 안 보인다.
#
# 벗기는 키(최상위):
#   model          — /model 이 고르는 모델 id
#   effortLevel    — /model 이 같이 쓰는 추론 강도
#   modelSettings  — 모델별 effortLevel 묶음 (2026-09-04 추가)
#
# 왜: ~/.claude/settings.json 은 여러 PC로 동기화되는데 /model 이 매번 이
# 필드들을 다시 써넣어 커밋이 재발한다(a2ac887, e36f505, 4f0dd17). 모델·강도는
# 그 PC에서 고르는 값이라 공유할 이유가 없다 — 훅·권한 등 나머지는 그대로 공유된다.
#
# 파싱 실패 시엔 입력을 그대로 흘려보낸다(필터가 설정을 망가뜨리지 않게).

STRIP_KEYS = ("model", "effortLevel", "modelSettings")


def main():
    text = sys.stdin.read()
    try:
        data = json.loads(text)
    except Exception:
        sys.stdout.write(text)
        return
    if not isinstance(data, dict):
        sys.stdout.write(text)
        return
    for key in STRIP_KEYS:
        data.pop(key, None)
    sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
