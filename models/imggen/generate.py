"""Nautilus ImageGen CLI — generate art (PNG) or animation (MP4) from a prompt.

Usage:
    python3 models/imggen/generate.py "abyss waves" --out art.png --size 512
    python3 models/imggen/generate.py "aurora glow" --video clip.mp4 --seconds 4
    python3 models/imggen/generate.py --list-models
"""

import argparse
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.imggen.engine import ImageGen, save_png

TRAINED = os.path.join(PROJECT_ROOT, "models", "trained")


def _resolve_model_dir(model: str) -> str:
    path = model if os.path.isdir(model) else os.path.join(TRAINED, model)
    if not os.path.isfile(os.path.join(path, "weights.npz")):
        raise SystemExit(f"imggen model not found at {path} — run models/imggen/train.py first")
    return path


def main():
    ap = argparse.ArgumentParser(description="Nautilus ImageGen")
    ap.add_argument("prompt", nargs="?", default=None, help="text prompt, e.g. 'abyss waves'")
    ap.add_argument("--model", default=os.path.join(TRAINED, "imggen"))
    ap.add_argument("-o", "--out", default=None, help="output PNG path")
    ap.add_argument("--video", default=None, help="output MP4 path instead of a still")
    ap.add_argument("-s", "--size", type=int, default=512, help="output size (default 512)")
    ap.add_argument("--steps", type=int, default=50, help="denoise steps (default 50)")
    ap.add_argument("--seconds", type=int, default=4, help="video length in seconds")
    ap.add_argument("--fps", type=int, default=12, help="video frame rate")
    ap.add_argument("--seed", type=int, default=None, help="random seed")
    ap.add_argument("--list-models", action="store_true", help="list trained imggen dirs")
    args = ap.parse_args()

    if args.list_models:
        for name in sorted(os.listdir(TRAINED)) if os.path.isdir(TRAINED) else []:
            if os.path.isfile(os.path.join(TRAINED, name, "weights.npz")):
                print(name)
        return

    if not args.prompt:
        ap.error("a prompt is required (or use --list-models)")

    gen = ImageGen(_resolve_model_dir(args.model))
    if args.video:
        out = gen.video(args.prompt, args.video, seconds=args.seconds, fps=args.fps,
                        size=args.size, seed=args.seed, steps=args.steps)
        print(f"[imggen] video -> {out}")
    else:
        out = args.out or "imggen.png"
        save_png(out, gen.generate(args.prompt, size=args.size, seed=args.seed, steps=args.steps))
        print(f"[imggen] image -> {out}")


if __name__ == "__main__":
    main()
