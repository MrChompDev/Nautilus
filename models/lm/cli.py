"""Nautilus LM CLI.

  python3 models/lm/cli.py --model coding --prompt "def fibonacci"
  python3 models/lm/cli.py --model writing --prompt "Write a README for..." --stream
  python3 models/lm/cli.py --list
"""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TRAINED_DIR = os.path.join(ROOT, "models", "trained")


def list_models():
    if not os.path.isdir(TRAINED_DIR):
        print("no trained models yet")
        return
    for name in sorted(os.listdir(TRAINED_DIR)):
        path = os.path.join(TRAINED_DIR, name)
        if os.path.isfile(os.path.join(path, "weights.npz")):
            size = sum(
                os.path.getsize(os.path.join(path, f)) for f in os.listdir(path)
            ) // (1024 * 1024)
            print(f"  {name:<12} ~{size}MB")


def main():
    ap = argparse.ArgumentParser(prog="nautilus-lm")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--model", default="coding")
    ap.add_argument("--prompt", default=None)
    ap.add_argument("--max-new-tokens", type=int, default=200)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--top-k", type=int, default=40)
    ap.add_argument("--stream", action="store_true")
    args = ap.parse_args()

    if args.list:
        list_models()
        return

    model_dir = os.path.join(TRAINED_DIR, args.model)
    if not os.path.isdir(model_dir):
        print(f"model '{args.model}' not trained yet (run models/lm/train.py --id {args.model})")
        sys.exit(1)

    from models.lm.engine import LM

    lm = LM(model_dir)
    if args.prompt is None:
        args.prompt = sys.stdin.read()

    if args.stream:
        def sink(tok):
            print(lm.decode([tok]), end="", flush=True)
        res = lm.respond(args.prompt, args.max_new_tokens, args.temperature, args.top_k, stream=sink)
        print(f"\n[{res['tokens']} tok, {res['seconds']}s, {res['tok_s']} tok/s]")
    else:
        res = lm.respond(args.prompt, args.max_new_tokens, args.temperature, args.top_k)
        print(res["text"])
        print(f"[{res['tokens']} tok, {res['seconds']}s, {res['tok_s']} tok/s]")


if __name__ == "__main__":
    main()
