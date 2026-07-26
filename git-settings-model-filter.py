import sys, re

# git clean 필터: settings.json이 git 인덱스로 들어갈 때(add/diff/commit)만
# 최상위 "model" 키를 제거해서 보여준다. 워킹트리 파일 자체는 안 건드리므로
# /model 은 평소처럼 정상 동작하고, git 쪽에서만 이 키가 영원히 안 보인다.
# (참고: ~/.claude/settings.json 은 여러 PC로 동기화되는데 /model 이 매번
#  이 필드를 다시 써넣어 커밋이 세 번 재발했다 — a2ac887, e36f505 참고)

MODEL_RE = re.compile(r'^\s*"model"\s*:\s*".*?"\s*,?\s*$')

def main():
    text = sys.stdin.read()
    lines = text.split("\n")
    idxs = [i for i, l in enumerate(lines) if MODEL_RE.match(l)]
    for i in reversed(idxs):
        j = i + 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j < len(lines) and lines[j].strip().startswith("}"):
            k = i - 1
            while k >= 0 and lines[k].strip() == "":
                k -= 1
            if k >= 0:
                lines[k] = re.sub(r",\s*$", "", lines[k])
        del lines[i]
    sys.stdout.write("\n".join(lines))

if __name__ == "__main__":
    main()
