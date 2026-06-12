"""TTS 음성 생성 — POST /audio/speech/

응답은 헤더 없는 raw PCM(24kHz mono 16-bit LE)이므로 WAV 헤더를 씌워 저장한다.
그대로 .pcm 으로 저장하면 대부분의 플레이어에서 재생되지 않는다.

사용:
  python tts.py --text "안녕하세요" [--voice Aoede]
                [--model gemini-2.5-flash-preview-tts] [--out speech.wav]
"""
import argparse
import sys
import wave
from pathlib import Path

import _gw

SAMPLE_RATE = 24000
CHANNELS = 1
SAMPWIDTH = 2  # 16-bit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--voice", default="Aoede")
    ap.add_argument("--model", default="gemini-2.5-flash-preview-tts")
    ap.add_argument("--out", default="speech.wav")
    args = ap.parse_args()

    body = {"model": args.model, "input": args.text, "voice": args.voice}
    _, resp, headers = _gw.post_json("/audio/speech/", body)

    if isinstance(resp, dict):
        sys.exit(f"[예상외 응답] 오디오 대신 JSON 수신:\n{resp}")

    pcm = resp  # bytes
    out = Path(args.out)
    if out.suffix.lower() != ".wav":
        out = out.with_suffix(".wav")

    with wave.open(str(out), "wb") as w:
        w.setnchannels(CHANNELS)
        w.setsampwidth(SAMPWIDTH)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)

    secs = len(pcm) / (SAMPLE_RATE * CHANNELS * SAMPWIDTH)
    itok = headers.get("X-Input-Tokens", "?")
    otok = headers.get("X-Output-Tokens", "?")
    print(f"저장됨: {out}  ({secs:.1f}s, in={itok} out={otok} tokens)")


if __name__ == "__main__":
    main()
