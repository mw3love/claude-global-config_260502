"""이미지 생성 — POST /images/generate/

사용:
  python image.py --prompt "..." [--model gpt-image-2] [--aspect 16:9]
                  [--n 1] [--out out.png]

동기 모델(gpt-image-2, gemini-2.5-flash-image)은 즉시 b64/URL 반환.
비동기 모델(flux, grok-imagine 등)은 operation_id를 반환 → 폴링 시도.
"""
import argparse
import base64
import sys
import time
import urllib.request
from pathlib import Path

import _gw


def save_b64(b64: str, out: Path):
    out.write_bytes(base64.b64decode(b64))


def save_url(url: str, out: Path):
    # data URI (data:image/png;base64,...) 도 지원
    if url.startswith("data:"):
        b64 = url.split(",", 1)[1]
        out.write_bytes(base64.b64decode(b64))
        return
    with urllib.request.urlopen(url, timeout=120) as r:
        out.write_bytes(r.read())


def extract_images(obj):
    """응답에서 (b64 또는 url) 리스트를 최대한 유연하게 추출."""
    items = []
    data = obj.get("data") or obj.get("images") or obj.get("results") or []
    if isinstance(data, dict):
        data = [data]
    for d in data:
        if isinstance(d, str):
            items.append(("url" if d.startswith("http") else "b64", d))
            continue
        if d.get("b64_json"):
            items.append(("b64", d["b64_json"]))
        elif d.get("url"):
            items.append(("url", d["url"]))
        elif d.get("image"):
            v = d["image"]
            items.append(("url" if str(v).startswith("http") else "b64", v))
    # 최상위에 직접 들어오는 경우
    if not items:
        if obj.get("b64_json"):
            items.append(("b64", obj["b64_json"]))
        elif obj.get("url"):
            items.append(("url", obj["url"]))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--model", default="gpt-image-2")
    ap.add_argument("--aspect", default=None, help='gemini 등: 1:1, 16:9, 9:16, 4:3')
    ap.add_argument("--size", default=None, help='gpt-image-2 등 OpenAI 계열: 1024x1024 등')
    ap.add_argument("--quality", default=None, help='standard/hd 또는 low/medium/high')
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--out", default="image.png")
    args = ap.parse_args()

    body = {"model": args.model, "prompt": args.prompt, "number_of_images": args.n}
    if args.aspect:
        body["aspect_ratio"] = args.aspect
    if args.size:
        body["size"] = args.size
    if args.quality:
        body["quality"] = args.quality

    _, resp, _ = _gw.post_json("/images/generate/", body)

    # 비동기: operation_id 폴링
    if isinstance(resp, dict) and resp.get("operation_id") and not extract_images(resp):
        op = resp["operation_id"]
        print(f"[비동기] operation_id={op} 폴링 중...", file=sys.stderr)
        for _ in range(60):
            time.sleep(3)
            _, st, _ = _gw.get(f"/images/generate/{op}/?model={args.model}")
            if isinstance(st, dict) and extract_images(st):
                resp = st
                break
            status = st.get("status") if isinstance(st, dict) else ""
            if status in ("failed", "error"):
                sys.exit(f"[실패] {st}")
        else:
            sys.exit("[시간초과] 이미지 생성이 끝나지 않았습니다.")

    imgs = extract_images(resp)
    if not imgs:
        sys.exit(f"[응답 파싱 실패] 이미지 데이터를 못 찾음:\n{resp}")

    out = Path(args.out)
    saved = []
    for i, (kind, val) in enumerate(imgs):
        p = out if len(imgs) == 1 else out.with_stem(f"{out.stem}_{i+1}")
        (save_b64 if kind == "b64" else save_url)(val, p)
        saved.append(str(p))
    print("저장됨: " + ", ".join(saved))


if __name__ == "__main__":
    main()
