"""Nautilus LM — CPU training loop + int8 export.

Usage:
  python models/lm/train.py --id kraken --data models/data/kraken --profile full --steps 500
  python models/lm/train.py --id coding --smoke   # tiny fast validation run
"""

import argparse
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import torch

from models.lm.bpe import BPETokenizer
from models.lm.model import DEFAULT_CONFIG, GPT

PROFILE_OVERRIDES = {
    "tiny": {"n_embd": 64, "n_layer": 2, "n_head": 4, "block_size": 64},
    "small": {"n_embd": 384, "n_layer": 6, "n_head": 6, "block_size": 1024},
    "full": {"n_embd": 512, "n_layer": 8, "n_head": 8, "block_size": 512},
}


def load_corpus(data_dir: str, max_bytes: int | None = None) -> str:
    parts = []
    total = 0
    for name in sorted(os.listdir(data_dir)):
        path = os.path.join(data_dir, name)
        if not name.endswith((".txt", ".py", ".md", ".json", ".qss", ".css")):
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            chunk = f.read(max_bytes - total) if max_bytes else f.read()
        if chunk:
            parts.append(chunk)
            total += len(chunk)
        if max_bytes and total >= max_bytes:
            break
    return "\n\n".join(parts)


def get_batch(ids, idx, block_size, batch_size, device):
    """Random windows from the token sequence."""
    n = len(ids) - 1
    if n < block_size + 1:
        raise ValueError("corpus too small for block_size")
    ix = torch.randint(0, n - block_size, (batch_size,))
    x = torch.stack([torch.from_numpy(ids[i : i + block_size]) for i in ix.tolist()])
    y = torch.stack([torch.from_numpy(ids[i + 1 : i + block_size + 1]) for i in ix.tolist()])
    return x.to(device), y.to(device)


@torch.no_grad()
def estimate_loss(model, ids, block_size, batch_size, device, eval_iters=30):
    model.eval()
    losses = []
    for _ in range(eval_iters):
        x, y = get_batch(ids, 0, block_size, batch_size, device)
        _, loss = model(x, y)
        losses.append(loss.item())
    model.train()
    return float(np.mean(losses))


def get_lr(step: int, warmup_steps: int, max_steps: int, base_lr: float) -> float:
    """Cosine LR schedule with linear warmup."""
    if step < warmup_steps:
        return base_lr * step / warmup_steps
    if step >= max_steps:
        return base_lr * 0.1
    progress = (step - warmup_steps) / (max_steps - warmup_steps)
    return base_lr * 0.5 * (1 + math.cos(math.pi * progress))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--data", required=True, help="dir of corpus .txt/.py/.md files")
    ap.add_argument("--out", default="models/trained")
    ap.add_argument("--profile", choices=list(PROFILE_OVERRIDES), default="small")
    ap.add_argument("--vocab", type=int, default=4096)
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--steps", type=int, default=0, help="limit total steps (0 = auto)")
    ap.add_argument("--target-tokens", type=int, default=2_500_000, help="total tokens to train on")
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--warmup", type=int, default=50, help="warmup steps")
    ap.add_argument("--patience", type=int, default=50, help="early stopping patience (val checks)")
    ap.add_argument("--bpe-bytes", type=int, default=1_500_000, help="corpus sample for BPE training")
    ap.add_argument("--max-tokens", type=int, default=2_000_000, help="corpus cap (tokens)")
    ap.add_argument("--smoke", action="store_true", help="tiny profile + 80 steps")
    args = ap.parse_args()

    if args.smoke:
        args.profile = "tiny"
        args.steps = 80
        args.max_tokens = 200_000

    torch.set_num_threads(16)
    torch.manual_seed(1337)
    np.random.seed(1337)

    cfg = dict(DEFAULT_CONFIG)
    cfg.update(PROFILE_OVERRIDES[args.profile])
    cfg["vocab_size"] = args.vocab

    t0 = time.time()
    corpus = load_corpus(args.data)
    print(f"[data] corpus {len(corpus):,} chars")

    # Train BPE on a representative sample, then encode full corpus once.
    sample = corpus[: args.bpe_bytes]
    tok = BPETokenizer().train(sample, vocab_size=cfg["vocab_size"])
    print(f"[bpe] vocab {tok.vocab_size} (sample {len(sample):,} chars)")

    ids = np.asarray(tok.encode(corpus[: 2_500_000]), dtype=np.int64)
    if len(ids) > args.max_tokens:
        ids = ids[: args.max_tokens]
    print(f"[bpe] corpus -> {len(ids):,} tokens ({(time.time()-t0):.0f}s)")

    model = GPT(cfg)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[model] {n_params/1e6:.1f}M params, int8 ~ {n_params/1e6:.0f}MB")

    device = torch.device("cpu")
    model.to(device)
    model.train()

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.1)
    tokens_per_step = args.batch * cfg["block_size"]

    # Calculate total steps
    if args.steps:
        total_steps = args.steps
    else:
        total_steps = max(1, args.target_tokens // tokens_per_step)
    max_steps = total_steps
    warmup_steps = min(args.warmup, total_steps // 4)

    print(f"[train] steps={total_steps} warmup={warmup_steps} batch={args.batch} lr={args.lr}")

    step = 0
    t_last = time.time()
    best_val_loss = float("inf")
    patience_counter = 0
    val_check_interval = max(10, total_steps // 20)  # Check ~20 times

    while True:
        # Apply cosine LR schedule
        lr = get_lr(step, warmup_steps, max_steps, args.lr)
        for pg in optimizer.param_groups:
            pg["lr"] = lr

        x, y = get_batch(ids, 0, cfg["block_size"], args.batch, device)
        _, loss = model(x, y)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        step += 1

        if step % 50 == 0:
            rate = 50 * tokens_per_step / (time.time() - t_last)
            print(f"step {step:>6} loss {loss.item():.4f} lr {lr:.2e} {rate:.0f} tok/s", flush=True)
            t_last = time.time()

        # Validation check + early stopping
        if step % val_check_interval == 0 and step > 0:
            val_loss = estimate_loss(model, ids, cfg["block_size"], args.batch, device)
            print(f"  [val] step {step} val_loss {val_loss:.4f} (best {best_val_loss:.4f})", flush=True)
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= args.patience and step >= warmup_steps * 2:
                    print(f"  [early stop] patience exhausted at step {step}")
                    break

        if args.steps and step >= args.steps:
            break
        if not args.steps and step * tokens_per_step >= args.target_tokens:
            break

    val_loss = estimate_loss(model, ids, cfg["block_size"], args.batch, device)
    elapsed = time.time() - t0
    print(f"[done] val_loss {val_loss:.4f} best_val {best_val_loss:.4f} steps {step} ({elapsed:.0f}s = {elapsed/60:.1f}min)")

    out_dir = os.path.join(args.out, args.id)
    os.makedirs(out_dir, exist_ok=True)
    model.export_int8(out_dir)
    tok.save(os.path.join(out_dir, "bpe.json"))
    with open(os.path.join(out_dir, "model.json"), "w") as f:
        json.dump(
            {
                "id": args.id,
                "profile": args.profile,
                "params": n_params,
                "int8_bytes": round(n_params, 0),
                "val_loss": val_loss,
                "best_val_loss": best_val_loss,
                "steps": step,
                "tokens": len(ids),
                "trained": time.strftime("%Y-%m-%d %H:%M:%S"),
                "wall_seconds": round(elapsed),
            },
            f,
            indent=2,
        )
    print(f"[save] {out_dir}")


if __name__ == "__main__":
    main()
