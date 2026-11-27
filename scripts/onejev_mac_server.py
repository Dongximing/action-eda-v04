#!/usr/bin/env python3
"""Serve OneJev on a Mac (Apple GPU, "mps") with the System One API, for scripts/jev_places_offline.py.

Flide's own engine needs an NVIDIA GPU (Triton kernels). This server keeps Flide's OneJev format for
everything except the forward pass: the format plans each request exactly as `flide serve` does (prompt
onejev-labels-v2, one branch per question, the same token ids), the model runs in transformers, the
answer-slot logits of the last token go back to the format, and the format's own `finish` turns them into
answers (softmax with the checkpoint's calibration). Differences from `flide serve`: no batching, no fused
kernels, so the numbers can differ in the last bits.

Run it with the Python environment that has flide installed (flide, flide_onejev, transformers, torch):

  ~/Documents/Codex/2026-11-26/onejev1-6-4b-x20/.venv/bin/python scripts/onejev_mac_server.py \
      --model ~/Documents/Codex/2026-11-26/onejev1-6-4b-x20/outputs/OneJev1.6-4B

It listens on http://localhost:8000/v1/systemone (POST {"state", "questions"}).
"""
from __future__ import annotations

import argparse
import copy
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def load(model_dir: str, device: str, dtype: str):
    import torch
    import transformers
    from flide_onejev.format import OneJev

    fmt = OneJev(model_dir)
    model = transformers.AutoModelForImageTextToText.from_pretrained(
        model_dir, dtype=getattr(torch, dtype), local_files_only=True).to(device).eval()
    return fmt, model


class Runner:
    def __init__(self, fmt, model, device: str):
        import torch

        self.fmt, self.model, self.device, self.torch = fmt, model, device, torch
        self.slot_ids = torch.tensor(fmt.slot_ids, device=device)
        self.lock = threading.Lock()

    def _last_slot_logits(self, ids: list[int], past=None) -> tuple[list[float], object]:
        t = self.torch
        x = t.tensor([ids], device=self.device)
        out = self.model(input_ids=x, past_key_values=past, use_cache=True)
        logits = out.logits[0, -1].float().index_select(0, self.slot_ids)
        return logits.tolist(), out.past_key_values

    def answer(self, payload: dict) -> dict:
        from flide.api.schema import SystemOneRequest

        req = SystemOneRequest.model_validate({k: v for k, v in payload.items() if k in ("state", "questions", "model")})
        plan = self.fmt.plan(req)
        if plan.vision is not None:
            raise ValueError("media are not supported by this server")
        outputs = []
        with self.lock, self.torch.inference_mode():
            if len(plan.suffixes) == 1 or not plan.prefix:
                for s in plan.suffixes:
                    outputs.append([[self._last_slot_logits(plan.prefix + s)[0]]])
            else:  # run the shared prefix once, then each question from a copy of its cache
                _, past = self._last_slot_logits(plan.prefix)
                for s in plan.suffixes:
                    outputs.append([[self._last_slot_logits(s, copy.deepcopy(past))[0]]])
        response, meta = self.fmt.finish(req, plan, outputs)
        body = response.model_dump(mode="json", exclude_none=True)
        body["meta"] = meta
        return body


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="local OneJev checkpoint directory")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--dtype", default="bfloat16", help="bfloat16 (as flide serve) or float32")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()

    t = time.time()
    fmt, model = load(a.model, a.device, a.dtype)
    runner = Runner(fmt, model, a.device)
    print(f"loaded {a.model} on {a.device} ({a.dtype}) in {time.time() - t:.0f}s", flush=True)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, code: int, body: dict):
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            if self.path.rstrip("/") != "/v1/systemone":
                return self._send(404, {"error": "POST /v1/systemone"})
            try:
                payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                t0 = time.time()
                body = runner.answer(payload)
                print(f"{len(payload.get('questions', {}))} questions, {body['meta']['prefix_tokens']} prefix tokens, "
                      f"{time.time() - t0:.2f}s", flush=True)
                self._send(200, body)
            except Exception as e:  # a bad request gets a 400 with the reason; the server keeps running
                self._send(400, {"error": f"{type(e).__name__}: {e}"})

    print(f"serving http://{a.host}:{a.port}/v1/systemone", flush=True)
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
