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
#
# stdout은 반드시 LF로만 쓴다 — Windows 네이티브 python은 텍스트모드 stdout이
# \n을 \r\n으로 바꿔써서, 커밋된 LF-only blob과 매번 달라져 git status가
# settings.json을 상시 modified로 잘못 표시하게 만든다(2026-09-04 실측: 이 PC의
# `python3`가 WindowsApps 스텁이라 항상 즉시 실패해 `python`(CRLF 변환) 폴백으로
# 떨어짐). sys.stdout.buffer로 직접 바이트를 써서 플랫폼 텍스트모드 변환을 우회.

STRIP_KEYS = ("model", "effortLevel", "modelSettings")


def _write(s):
    sys.stdout.buffer.write(s.encode("utf-8"))


def main():
    text = sys.stdin.read()
    try:
        data = json.loads(text)
    except Exception:
        _write(text)
        return
    if not isinstance(data, dict):
        _write(text)
        return
    for key in STRIP_KEYS:
        data.pop(key, None)
    _write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
