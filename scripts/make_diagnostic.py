"""Generate a labelled diagnostic set with controlled history structure (doc v0.4 §5.4).

All samples are SYNTHETIC (template-built); labels carry synthetic=true and must be
reported separately from natural trajectories.

Cells (one claim per sample):
  est              establish (+ distractors)                          -> SUPPORTED
  inv              establish, invalidate                              -> CONTRADICTED
  reest            establish, invalidate, re-establish                -> SUPPORTED   order_sensitive
  reest_inv        establish, invalidate, re-establish, invalidate    -> CONTRADICTED order_sensitive
  comp             establish, part A, part B (only jointly invalidating) -> CONTRADICTED composition
  comp_ctrl        establish, part A only                             -> SUPPORTED   (matched control)
  def_none         default claim, no withdrawal                       -> SUPPORTED
  def_withdraw     default claim, withdrawal                          -> CONTRADICTED
  def_resume       default claim, withdrawal, resume                  -> SUPPORTED   order_sensitive

Factors crossed per cell: number of same-entity distractors between events, and
whether invalidating / re-establishing records name the entity ("explicit") or
only refer to it ("anaphoric", label indirect=true).

  python scripts/make_diagnostic.py --out data/diag --n-per-cell 8 --lang zh,en
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aeda.schema import write_jsonl  # noqa: E402

# Each domain: text templates per language. {e} = entity id.
# inv/reest have explicit (mentions {e}) and anaphoric variants.
DOMAINS = {
    "reservation": {
        "kind": "state", "cells": ["est", "inv", "reest", "reest_inv"],
        "id": lambda rng: f"R{rng.randint(100, 999)}",
        "zh": {
            "task": "处理用户关于预订 {e} 的请求", "action": "cancel_reservation({e})", "reversible": False,
            "claim": "用户当前要求取消预订 {e}",
            "est": [("user", "帮我取消预订 {e}。")],
            "inv": {"explicit": ("user", "等等，先别取消 {e}，我再想想。"), "anaphoric": ("user", "等等，先别取消，我再想想。")},
            "reest": {"explicit": ("user", "想好了，还是把 {e} 取消吧。"), "anaphoric": ("user", "想好了，还是取消吧。")},
            "distract": [("user", "{e} 是几点出发？"), ("tool", "get_reservation({e}) -> departure: 09:40, seat: 12C"),
                         ("user", "{e} 的行李额度是多少？"), ("tool", "get_baggage({e}) -> 23kg x 1"),
                         ("agent", "我查一下 {e} 的详情。"), ("user", "{e} 能选靠窗的座位吗？")],
        },
        "en": {
            "task": "Handle the user's request about reservation {e}", "action": "cancel_reservation({e})", "reversible": False,
            "claim": "The user currently asks to cancel reservation {e}",
            "est": [("user", "Please cancel my reservation {e}.")],
            "inv": {"explicit": ("user", "Wait, don't cancel {e} yet, let me think."), "anaphoric": ("user", "Wait, don't do it yet, let me think.")},
            "reest": {"explicit": ("user", "OK, go ahead and cancel {e}."), "anaphoric": ("user", "OK, go ahead with it.")},
            "distract": [("user", "What time does {e} depart?"), ("tool", "get_reservation({e}) -> departure: 09:40, seat: 12C"),
                         ("user", "What's the baggage allowance on {e}?"), ("tool", "get_baggage({e}) -> 23kg x 1"),
                         ("agent", "Let me look up {e}."), ("user", "Can I get a window seat on {e}?")],
        },
    },
    "file": {
        "kind": "state", "cells": ["est", "inv", "reest", "reest_inv", "comp", "comp_ctrl"],
        "id": lambda rng: f"report_{rng.randint(10, 99)}.pdf",
        "zh": {
            "task": "把 /tmp 下的 {e} 上传到共享盘", "action": "upload_file('/tmp/{e}')", "reversible": False,
            "claim": "{e} 当前在 /tmp 目录下",
            "est": [("tool", "list_dir(/tmp) -> {e}, notes.txt")],
            "inv": {"explicit": ("tool", "move_file(/tmp/{e}, /archive) -> ok"), "anaphoric": ("env", "上一步选中的文件已移到 /archive。")},
            "reest": {"explicit": ("tool", "move_file(/archive/{e}, /tmp) -> ok"), "anaphoric": ("env", "刚归档的文件已恢复到原目录。")},
            "comp": [("tool", "get_tags({e}) -> [draft]"), ("env", "夜间清理任务已完成：删除了所有带 draft 标签的文件。")],
            "distract": [("tool", "get_size({e}) -> 2.1MB"), ("tool", "read_file({e}, page=1) -> 'Q3 summary ...'"),
                         ("agent", "{e} 第一页是季度总结。"), ("tool", "get_owner({e}) -> alice"),
                         ("tool", "get_modified({e}) -> 2026-11-20"), ("agent", "确认一下 {e} 的大小。")],
        },
        "en": {
            "task": "Upload {e} from /tmp to the shared drive", "action": "upload_file('/tmp/{e}')", "reversible": False,
            "claim": "{e} is currently in /tmp",
            "est": [("tool", "list_dir(/tmp) -> {e}, notes.txt")],
            "inv": {"explicit": ("tool", "move_file(/tmp/{e}, /archive) -> ok"), "anaphoric": ("env", "The selected file was moved to /archive.")},
            "reest": {"explicit": ("tool", "move_file(/archive/{e}, /tmp) -> ok"), "anaphoric": ("env", "The archived file was restored to its original folder.")},
            "comp": [("tool", "get_tags({e}) -> [draft]"), ("env", "Nightly cleanup finished: removed every file tagged draft.")],
            "distract": [("tool", "get_size({e}) -> 2.1MB"), ("tool", "read_file({e}, page=1) -> 'Q3 summary ...'"),
                         ("agent", "Page 1 of {e} is the quarterly summary."), ("tool", "get_owner({e}) -> alice"),
                         ("tool", "get_modified({e}) -> 2026-11-20"), ("agent", "Let me check the size of {e}.")],
        },
    },
    "order": {
        "kind": "state", "cells": ["est", "inv", "reest", "reest_inv", "comp", "comp_ctrl"],
        "id": lambda rng: f"O{rng.randint(10, 99)}",
        "zh": {
            "task": "修改订单 {e} 的商品", "action": "update_items({e})", "reversible": True,
            "claim": "订单 {e} 当前尚未发货",
            "est": [("tool", "get_order({e}) -> status: pending_shipment")],
            "inv": {"explicit": ("tool", "get_order({e}) -> status: shipped"), "anaphoric": ("env", "通知：该订单已交给快递。")},
            "reest": {"explicit": ("tool", "recall_shipment({e}) -> ok, status: pending_shipment"), "anaphoric": ("env", "通知：快递已退回，订单恢复为待发货。")},
            "comp": [("tool", "get_order_warehouse({e}) -> W3"), ("env", "仓库 W3 今天已完成全部待发订单的出库。")],
            "distract": [("user", "{e} 的收货地址能改成公司吗？"), ("tool", "update_address({e}) -> ok"),
                         ("user", "{e} 用哪张卡付的款？"), ("tool", "get_payment({e}) -> card ending 4411"),
                         ("agent", "我来处理 {e}。"), ("tool", "get_invoice({e}) -> INV-2231")],
        },
        "en": {
            "task": "Change the items of order {e}", "action": "update_items({e})", "reversible": True,
            "claim": "Order {e} has not been shipped yet",
            "est": [("tool", "get_order({e}) -> status: pending_shipment")],
            "inv": {"explicit": ("tool", "get_order({e}) -> status: shipped"), "anaphoric": ("env", "Notice: the parcel was handed to the courier.")},
            "reest": {"explicit": ("tool", "recall_shipment({e}) -> ok, status: pending_shipment"), "anaphoric": ("env", "Notice: the parcel was returned; the order is pending shipment again.")},
            "comp": [("tool", "get_order_warehouse({e}) -> W3"), ("env", "Warehouse W3 dispatched all pending orders today.")],
            "distract": [("user", "Can {e} be delivered to my office?"), ("tool", "update_address({e}) -> ok"),
                         ("user", "Which card paid for {e}?"), ("tool", "get_payment({e}) -> card ending 4411"),
                         ("agent", "I'll handle {e}."), ("tool", "get_invoice({e}) -> INV-2231")],
        },
    },
    "account": {
        "kind": "default", "cells": ["def_none", "def_withdraw", "def_resume"],
        "id": lambda rng: f"A{rng.randint(10, 99)}",
        "zh": {
            "task": "为账户 {e} 升级套餐", "action": "change_plan({e}, premium)", "reversible": True,
            "claim": "用户没有要求暂停账户 {e} 的变更",
            "est": [("user", "请把账户 {e} 升级为高级版。")],
            "inv": {"explicit": ("user", "先暂停 {e} 的所有变更，我要和家人商量。"), "anaphoric": ("user", "先暂停，别改了，我要和家人商量。")},
            "reest": {"explicit": ("user", "商量好了，{e} 可以继续改。"), "anaphoric": ("user", "商量好了，继续吧。")},
            "distract": [("tool", "get_plans({e}) -> basic, premium"), ("user", "{e} 高级版每月多少钱？"),
                         ("tool", "get_price({e}, premium) -> 30/month"), ("agent", "我查一下 {e} 的套餐。"),
                         ("user", "{e} 现在是什么套餐？"), ("tool", "get_account({e}) -> plan: basic")],
        },
        "en": {
            "task": "Upgrade the plan of account {e}", "action": "change_plan({e}, premium)", "reversible": True,
            "claim": "The user has not asked to pause changes to account {e}",
            "est": [("user", "Please upgrade account {e} to premium.")],
            "inv": {"explicit": ("user", "Pause all changes to {e} for now, I need to ask my family."), "anaphoric": ("user", "Hold on, stop for now, I need to ask my family.")},
            "reest": {"explicit": ("user", "OK, you can continue changing {e}."), "anaphoric": ("user", "OK, go ahead and continue.")},
            "distract": [("tool", "get_plans({e}) -> basic, premium"), ("user", "How much is premium for {e}?"),
                         ("tool", "get_price({e}, premium) -> 30/month"), ("agent", "Let me check the plans for {e}."),
                         ("user", "What plan is {e} on now?"), ("tool", "get_account({e}) -> plan: basic")],
        },
    },
}

# event skeleton per cell: (event, gold, order_sensitive, composition)
CELLS = {
    "est": (["est"], "SUPPORTED", False, False),
    "inv": (["est", "inv"], "CONTRADICTED", False, False),
    "reest": (["est", "inv", "reest"], "SUPPORTED", True, False),
    "reest_inv": (["est", "inv", "reest", "inv"], "CONTRADICTED", True, False),
    "comp": (["est", "compA", "compB"], "CONTRADICTED", False, True),
    "comp_ctrl": (["est", "compA"], "SUPPORTED", False, False),
    "def_none": (["est"], "SUPPORTED", False, False),
    "def_withdraw": (["est", "inv"], "CONTRADICTED", False, False),
    "def_resume": (["est", "inv", "reest"], "SUPPORTED", True, False),
}


def build(domain: str, lang: str, cell: str, n_distract: int, ref: str, rng: random.Random, idx: int):
    D, T = DOMAINS[domain], DOMAINS[domain][lang]
    e = D["id"](rng)
    events, gold, order_sens, comp = CELLS[cell]
    # spread distractors across the gaps after each event
    gaps = [0] * len(events)
    for _ in range(n_distract):
        gaps[rng.randrange(len(events))] += 1
    pool = list(T["distract"])
    texts: list[tuple[str, str, bool]] = []  # (source, text, mentions_entity)
    for ev, g in zip(events, gaps):
        if ev == "est":
            src, t = T["est"][0]
        elif ev in ("inv", "reest"):
            src, t = T[ev][ref]
        elif ev == "compA":
            src, t = T["comp"][0]
        else:  # compB
            src, t = T["comp"][1]
        texts.append((src, t, "{e}" in t))
        for _ in range(g):
            src, t = pool[rng.randrange(len(pool))]
            texts.append((src, t, "{e}" in t))
    records = [{"rid": i + 1, "source": src, "text": t.format(e=e), "entities": [e] if m else []}
               for i, (src, t, m) in enumerate(texts)]
    sid = f"{domain}-{lang}-{cell}-d{n_distract}-{ref}-{idx}"
    sample = {
        "sid": sid, "episode_id": sid, "task": T["task"].format(e=e), "proposed_action": T["action"].format(e=e),
        "action_reversible": T["reversible"], "window_complete": True, "records": records,
        "claims": [{"cid": f"{sid}/c", "text": T["claim"].format(e=e), "kind": D["kind"],
                    "origin": "fixed", "entities": [e]}],
    }
    uses_ref = any(ev in ("inv", "reest") for ev in events)
    label = {"sid": sid, "cid": f"{sid}/c", "gold": gold, "order_sensitive": order_sens,
             "composition": comp, "indirect": (ref == "anaphoric" and uses_ref) or comp,
             "implicit_order": False, "synthetic": True,
             "extra": {"domain": domain, "lang": lang, "cell": cell, "n_distract": n_distract,
                       "ref": ref if uses_ref else "n/a", "n_records": len(records)}}
    return sample, label


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-per-cell", type=int, default=8)
    ap.add_argument("--lang", default="zh,en")
    ap.add_argument("--distract", default="0,3,8", help="numbers of distractor records")
    ap.add_argument("--domains", default=",".join(DOMAINS))
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    samples, labels = [], []
    for domain in a.domains.split(","):
        for lang in a.lang.split(","):
            for cell in DOMAINS[domain]["cells"]:
                refs = ["explicit", "anaphoric"] if any(ev in ("inv", "reest") for ev in CELLS[cell][0]) else ["explicit"]
                for nd in [int(x) for x in a.distract.split(",")]:
                    for ref in refs:
                        for i in range(a.n_per_cell):
                            s, l = build(domain, lang, cell, nd, ref, rng, i)
                            samples.append(s)
                            labels.append(l)
    out = Path(a.out)
    write_jsonl(out / "samples.jsonl", samples)
    write_jsonl(out / "labels.jsonl", labels)
    (out / "meta.json").write_text(json.dumps(vars(a), indent=2), encoding="utf-8")
    print(f"{len(samples)} samples -> {out}")


if __name__ == "__main__":
    main()
