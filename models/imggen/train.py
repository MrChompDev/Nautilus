"""Nautilus ImageGen — CPU training loop.

Usage (ComfyUI venv has torch):
  python3 models/imggen/train.py --steps 3000 --out models/trained/imggen
  python3 models/imggen/train.py --smoke
"""

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np
import torch

from models.imggen.data import make_dataset
from models.imggen.model import TinyUNet, betas_for_alpha_bar, export_int8


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--n-steps", type=int, default=200, help="diffusion schedule length")
    ap.add_argument("--out", default="models/trained/imggen")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        args.steps, args.batch = 60, 32

    os.makedirs(args.out, exist_ok=True)
    torch.set_num_threads(16)
    torch.manual_seed(7)
    np.random.seed(7)

    imgs, styles, _ = make_dataset(2048, 32)
    X = torch.from_numpy(imgs.transpose(0, 3, 1, 2))
    S = torch.from_numpy(styles)
    n = X.size(0)
    betas = torch.from_numpy(betas_for_alpha_bar(args.n_steps).astype(np.float32))
    alphas = 1 - betas
    alpha_bar = torch.cumprod(alphas, 0)

    model = TinyUNet()
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[model] {n_params/1e3:.0f}K params, int8 ~ {n_params/1e6:.1f}MB")

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    t0 = time.time()
    for step in range(1, args.steps + 1):
        ix = torch.randint(0, n, (args.batch,))
        x0 = X[ix]
        style = S[ix]
        t = torch.randint(0, args.n_steps, (args.batch,)).float() / args.n_steps
        noise = torch.randn_like(x0)
        ab = alpha_bar[(t * (args.n_steps - 1)).long().clamp(0, args.n_steps - 1)][:, None, None, None]
        x_t = torch.sqrt(ab) * x0 + torch.sqrt(1 - ab) * noise
        pred = model(x_t, t.unsqueeze(1), style)
        loss = torch.nn.functional.mse_loss(pred, noise)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % 100 == 0 or step == args.steps:
            rate = step * args.batch / (time.time() - t0)
            print(f"step {step:>5} loss {loss.item():.5f}  {rate:.0f} img/s", flush=True)

    torch.save(model.state_dict(), os.path.join(args.out, "torch.pt"))
    export_int8(model, args.out)
    with open(os.path.join(args.out, "model.json"), "w") as f:
        json.dump({"id": "imggen", "params": n_params, "steps": args.steps,
                   "n_steps": args.n_steps, "trained": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=2)
    print(f"[save] {args.out} ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
