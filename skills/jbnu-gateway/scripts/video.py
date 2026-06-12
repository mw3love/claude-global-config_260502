"""비디오 생성 — POST /video/generation/ (비동기)

워크플로:
  1) 제출 → operation_id
  2) 폴링 GET /video/generation/{id}/?model=<name>
  3) 다운로드 GET /video/generation/{id}/download/?model=<name>
     (또는 폴링 응답의 video_uri 직접 다운로드)

생성에 보통 30~120초 소요. 모델별 크레딧 차감 큼(veo-3.1는 최대 1,600).

사용:
  python video.py --prompt "..." [--model veo-3.1-fast-generate-preview]
                  [--image <url>] [--out video.mp4] [--timeout 240]
"""
import argparse
import sys
import time
import urllib.request
from pathlib import Path

import _gw


def fetch_to(uri: str, out: Path):
    """video_uri 저장. 절대 URL(서명된 외부 링크)은 직접, 게이트웨이
    상대경로(/v1/gateway/...)는 인증·UA를 태워 _gw.get으로 받는다."""
    if uri.startswith("http"):
        with urllib.request.urlopen(uri, timeout=300) as r:
            out.write_bytes(r.read())
        return
    prefix = "/v1/gateway"
    path = uri[len(prefix):] if uri.startswith(prefix) else uri
    _, data, _ = _gw.get(path)
    if isinstance(data, dict):
        sys.exit(f"[다운로드 실패] {data}")
    out.write_bytes(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--model", default="veo-3.1-fast-generate-preview")
    ap.add_argument("--image", default=None, help="image-to-video 입력 URL")
    ap.add_argument("--out", default="video.mp4")
    ap.add_argument("--timeout", type=int, default=240, help="폴링 최대 초")
    args = ap.parse_args()

    body = {"model": args.model, "prompt": args.prompt}
    if args.image:
        body["input_urls"] = [args.image]

    _, resp, _ = _gw.post_json("/video/generation/", body)
    op = resp.get("operation_id") if isinstance(resp, dict) else None
    if not op:
        sys.exit(f"[제출 실패] operation_id 없음:\n{resp}")
    print(f"[제출됨] operation_id={op} — 폴링 중(최대 {args.timeout}s)...", file=sys.stderr)

    deadline = time.time() + args.timeout
    video_uri = None
    while time.time() < deadline:
        time.sleep(5)
        _, st, _ = _gw.get(f"/video/generation/{op}/?model={args.model}")
        status = st.get("status") if isinstance(st, dict) else ""
        if status in ("failed", "error"):
            sys.exit(f"[실패] {st}")
        if isinstance(st, dict) and st.get("video_uri"):
            video_uri = st["video_uri"]
            break
        if status in ("succeeded", "completed", "done"):
            break
        print(f"  ...status={status or '진행중'}", file=sys.stderr)
    else:
        sys.exit(f"[시간초과] {args.timeout}s 내 미완료. 나중에 operation_id={op}로 재확인 가능.")

    out = Path(args.out)
    if video_uri:
        fetch_to(video_uri, out)
    else:
        # video_uri가 없으면 download 엔드포인트 직접 사용
        fetch_to(f"/video/generation/{op}/download/?model={args.model}", out)
    print(f"저장됨: {out}")


if __name__ == "__main__":
    main()
