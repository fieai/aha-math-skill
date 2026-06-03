#!/usr/bin/env python3
"""tts.py —— 可选旁白配音（MiMo-V2.5-TTS）。

设计为「可选」：
  - 设置了环境变量 MIMO_API_KEY → 给 scene.py 里每句 caption(...) 合成语音，
    输出 <scene 同目录>/narration/NN.wav 和 narration.json 清单；mathviz 的
    caption() 会自动读清单、按音频时长停留并配音。
  - 没设 MIMO_API_KEY → 打印提示、退出 0（不报错），视频照常无声渲染。

用法:
    MIMO_API_KEY=sk-xxx python3 tts.py <scene.py> [--voice 茉莉] [--style "亲切清晰，语速稍慢"]

环境变量:
    MIMO_API_KEY   必需（缺失则跳过）
    MIMO_TTS_VOICE 可选，默认 茉莉（预置音色：mimo_default/冰糖/茉莉/苏打/白桦/Mia/Chloe/Milo/Dean）
    MIMO_TTS_BASE  可选，默认 https://api.xiaomimimo.com/v1

纯标准库 + ffprobe（取音频时长）。
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://api.xiaomimimo.com/v1"
DEFAULT_VOICE = "茉莉"
DEFAULT_STYLE = "亲切、清晰、有耐心，像老师给小学生讲题，语速稍慢。"
MODEL = "mimo-v2.5-tts"


def _ssl_context():
    """优先用 certifi 的 CA 包，绕开 macOS 系统 python 常见的 CERTIFICATE_VERIFY_FAILED。"""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


_SSL_CTX = _ssl_context()


def load_env_files(*extra_dirs):
    """把 cwd（及可选目录）下的 .env 读进 os.environ；真实环境变量优先，不覆盖。"""
    paths = [Path(".env")] + [Path(d) / ".env" for d in extra_dirs]
    for p in paths:
        try:
            if p.is_file():
                for ln in p.read_text(encoding="utf-8").splitlines():
                    ln = ln.strip()
                    if not ln or ln.startswith("#") or "=" not in ln:
                        continue
                    k, v = ln.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception:
            pass


def extract_captions(scene_path: Path) -> list[str]:
    """从 scene.py 抽取 caption("...") / caption('...') 的文本（保序去重）。"""
    src = scene_path.read_text(encoding="utf-8")
    texts: list[str] = []
    seen = set()
    for m in re.finditer(r'caption\(\s*(["\'])(.*?)\1', src, flags=re.S):
        t = m.group(2)
        if t and t not in seen:
            seen.add(t)
            texts.append(t)
    return texts


def synth(text: str, base: str, key: str, voice: str, style: str) -> bytes:
    body = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": style},
            {"role": "assistant", "content": text},
        ],
        "audio": {"format": "wav", "voice": voice},
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"api-key": key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90, context=_SSL_CTX) as r:
        resp = json.load(r)
    try:
        data_b64 = resp["choices"][0]["message"]["audio"]["data"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"返回里找不到 message.audio.data：{json.dumps(resp, ensure_ascii=False)[:400]}") from e
    return base64.b64decode(data_b64)


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return round(float(out.stdout.strip()), 3)
    except ValueError:
        return 0.0


def main() -> int:
    load_env_files()  # 先读 cwd 的 .env，让下面的音色默认值也能从 .env 取
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--voice", default=os.environ.get("MIMO_TTS_VOICE", DEFAULT_VOICE))
    ap.add_argument("--style", default=DEFAULT_STYLE)
    args = ap.parse_args()

    scene_path = Path(args.scene)
    if not scene_path.exists():
        print(f"[tts] 找不到 scene 文件: {scene_path}")
        return 2

    # 读取 .env（cwd + scene 目录），真实环境变量优先
    load_env_files(str(scene_path.parent))
    key = os.environ.get("MIMO_API_KEY", "").strip()
    if not key:
        print("[tts] 未配置 MIMO_API_KEY → 跳过配音，视频将无声渲染（这是可选项，非错误）。")
        print("[tts] 如需配音：在项目根建 .env 写 MIMO_API_KEY=你的key（见 templates/.env.example），或临时 MIMO_API_KEY=... 前缀运行。")
        return 0

    base = os.environ.get("MIMO_TTS_BASE", DEFAULT_BASE)
    texts = extract_captions(scene_path)
    if not texts:
        print("[tts] scene 里没找到 caption(...) 文本，无需配音。")
        return 0

    out_dir = scene_path.parent / "narration"
    out_dir.mkdir(exist_ok=True)
    items = []
    print(f"[tts] 音色={args.voice}，共 {len(texts)} 句，开始合成…")
    for i, text in enumerate(texts):
        wav = out_dir / f"{i:02d}.wav"
        try:
            audio = synth(text, base, key, args.voice, args.style)
        except Exception as e:
            print(f"[tts][FAIL] 第 {i} 句合成失败：{e}")
            if "CERTIFICATE" in str(e) or "SSL" in str(e):
                print("[tts] 提示：SSL 证书问题 → pip install certifi（或用系统 python3 跑本脚本）。")
            print("[tts] 已中止；修正后重试，或不设 key 出无声视频。")
            return 1
        wav.write_bytes(audio)
        dur = duration(wav)
        items.append({"text": text, "audio": f"narration/{wav.name}", "duration": dur})
        print(f"  [{i:02d}] {dur:>5.2f}s  {text[:24]}")

    manifest = scene_path.parent / "narration.json"
    manifest.write_text(
        json.dumps({"voice": args.voice, "model": MODEL, "items": items},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    total = sum(it["duration"] for it in items)
    print(f"[tts] 完成：{len(items)} 句，合计 {total:.1f}s → {manifest}")
    print("[tts] 重新渲染即可带配音（mathviz 的 caption 会自动读 narration.json）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
