"""
API Evaluation Script

Runs an automated evaluation against the running backend:
- Performs Kyber handshake to obtain a session token
- Submits N synthetic claims
- Optionally generates a checkpoint
- Queries claim status, verifies AI score, proves inclusion
- Records timings and results to a CSV file

Usage (from repo root):
  uv run python scripts/evaluate_api.py --backend http://localhost:8000 --out evaluation/results.csv --num 10 --gen-checkpoint --summary-out evaluation/summary.txt
  # Large test targeting ~1000 entries in checkpoint timing
  uv run python scripts/evaluate_api.py --backend http://localhost:8000 --out evaluation/results.csv --num 200 --gen-checkpoint --target-checkpoint-entries 1000 --summary-out evaluation/summary.txt

Dependencies: httpx (declared in pyproject)
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import csv
import os
import random
import string
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx


def _rand_id(prefix: str = "claim") -> str:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    tail = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{ts}_{tail}"


def _random_claim() -> Dict[str, Any]:
    # Matches trained model features: claim_am, time_of_c, location_r
    return {
        "claim_id": _rand_id(),
        "claim_am": round(random.uniform(50.0, 5000.0), 2),
        "time_of_c": random.randint(0, 23),
        "location_r": round(random.uniform(0.0, 1.0), 2),
    }


async def handshake(client: httpx.AsyncClient, backend: str) -> str:
    t0 = time.perf_counter()
    # Let server generate a valid client key for demo purposes (per backend behavior)
    resp = await client.post(f"{backend}/handshake", json={})
    resp.raise_for_status()
    data = resp.json()
    token = data["session_token"]
    dt_ms = (time.perf_counter() - t0) * 1000
    return token, dt_ms


async def submit_claim(client: httpx.AsyncClient, backend: str, token: str, claim: Dict[str, Any]):
    t0 = time.perf_counter()
    resp = await client.post(
        f"{backend}/claim/submit",
        headers={"X-Session-Token": token},
        json={"claim_data": claim},
        timeout=30.0,
    )
    resp.raise_for_status()
    dt_ms = (time.perf_counter() - t0) * 1000
    return resp.json(), dt_ms


async def claim_status(client: httpx.AsyncClient, backend: str, token: str, log_entry_id: int):
    t0 = time.perf_counter()
    resp = await client.get(f"{backend}/claim/status/{log_entry_id}", headers={"X-Session-Token": token})
    resp.raise_for_status()
    dt_ms = (time.perf_counter() - t0) * 1000
    return resp.json(), dt_ms


async def verify_ai_score(client: httpx.AsyncClient, backend: str, log_entry_id: int):
    t0 = time.perf_counter()
    resp = await client.get(f"{backend}/audit/verify-ai-score/{log_entry_id}")
    resp.raise_for_status()
    dt_ms = (time.perf_counter() - t0) * 1000
    return resp.json(), dt_ms


async def prove_inclusion(client: httpx.AsyncClient, backend: str, log_entry_id: int):
    t0 = time.perf_counter()
    resp = await client.get(f"{backend}/audit/prove-inclusion/{log_entry_id}")
    resp.raise_for_status()
    dt_ms = (time.perf_counter() - t0) * 1000
    return resp.json(), dt_ms


async def generate_checkpoint(client: httpx.AsyncClient, backend: str, admin_key: Optional[str]):
    t0 = time.perf_counter()
    params = {}
    if admin_key:
        params["admin_key"] = admin_key
    resp = await client.post(f"{backend}/admin/generate-checkpoint", params=params)
    if resp.status_code == 400:
        # No new entries; treat as non-fatal
        return {"success": False, "detail": resp.json().get("detail", "no entries")}, (time.perf_counter() - t0) * 1000
    resp.raise_for_status()
    dt_ms = (time.perf_counter() - t0) * 1000
    return resp.json(), dt_ms


async def get_merkle_tree(client: httpx.AsyncClient, backend: str, scope: str = "since_last_checkpoint") -> Dict[str, Any]:
    resp = await client.get(f"{backend}/audit/merkle-tree", params={"scope": scope})
    resp.raise_for_status()
    return resp.json()


def _avg(values: List[float]) -> Optional[float]:
    vals = [v for v in values if isinstance(v, (int, float))]
    if not vals:
        return None
    return sum(vals) / len(vals)


async def run_eval(
    backend: str,
    out_csv: str,
    num: int,
    do_checkpoint: bool,
    admin_key: Optional[str],
    summary_out: Optional[str],
    target_checkpoint_entries: Optional[int],
):
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)

    async with httpx.AsyncClient(timeout=30.0) as client:
        token, handshake_ms = await handshake(client, backend)

        rows: List[Dict[str, Any]] = []
        # If we want to hit a target number of entries for checkpoint, compute how many we should submit
        planned = num
        initial_leaf_count = None
        if do_checkpoint and target_checkpoint_entries and target_checkpoint_entries > 0:
            try:
                mt = await get_merkle_tree(client, backend, scope="since_last_checkpoint")
                initial_leaf_count = int(mt.get("leaf_count", 0))
                remaining = max(0, target_checkpoint_entries - initial_leaf_count)
                if remaining > planned:
                    planned = remaining
            except Exception:
                pass

        for i in range(planned):
            claim = _random_claim()
            submit_res, submit_ms = await submit_claim(client, backend, token, claim)
            log_entry_id = submit_res.get("log_entry_id")

            status_res, status_ms = await claim_status(client, backend, token, log_entry_id)
            ai_res, ai_ms = await verify_ai_score(client, backend, log_entry_id)
            # prove inclusion may require a checkpoint; handle errors gracefully
            incl_ok = None
            incl_path_len = None
            incl_ms = None
            try:
                incl_res, incl_ms = await prove_inclusion(client, backend, log_entry_id)
                incl_ok = bool(incl_res.get("included", False))
                path = incl_res.get("merkle_path")
                incl_path_len = len(path) if isinstance(path, list) else None
            except httpx.HTTPStatusError as e:
                incl_ok = False

            rows.append({
                "iteration": i + 1,
                "handshake_ms": round(handshake_ms, 2) if i == 0 else "",
                "log_entry_id": log_entry_id,
                "claim_id": status_res.get("claim_id"),
                "fraud_score": submit_res.get("fraud_score"),
                "model_version": submit_res.get("model_version"),
                "status_tamper_verified": status_res.get("tamper_verified"),
                "verify_ai_verified": ai_res.get("verified"),
                "verify_ai_model_version": ai_res.get("model_version"),
                "verify_ai_feature_hash_match": ai_res.get("feature_hash_match"),
                "submit_ms": round(submit_ms, 2),
                "status_ms": round(status_ms, 2),
                "verify_ai_ms": round(ai_ms, 2),
                "prove_inclusion_ms": round(incl_ms, 2) if incl_ms is not None else "",
                "prove_inclusion_ok": incl_ok,
                "prove_inclusion_path_len": incl_path_len,
                "timestamp": datetime.utcnow().isoformat(),
            })

        chk_id = None
        chk_root = None
        chk_ms = None
        chk_entries = None
        if do_checkpoint:
            chk_res, chk_ms = await generate_checkpoint(client, backend, admin_key)
            if chk_res and chk_res.get("success"):
                chk_id = chk_res.get("checkpoint_id")
                chk_root = chk_res.get("merkle_root")
                # find how many entries were included by comparing counts
                try:
                    # After checkpoint, since_last_checkpoint leaf_count should be 0
                    # So approximate entries included by planned or initial + planned
                    if initial_leaf_count is not None:
                        chk_entries = initial_leaf_count + planned
                    else:
                        chk_entries = planned
                except Exception:
                    chk_entries = planned

        # write CSV
        fieldnames = [
            "iteration",
            "timestamp",
            "handshake_ms",
            "log_entry_id",
            "claim_id",
            "fraud_score",
            "model_version",
            "status_tamper_verified",
            "verify_ai_verified",
            "verify_ai_model_version",
            "verify_ai_feature_hash_match",
            "submit_ms",
            "status_ms",
            "verify_ai_ms",
            "prove_inclusion_ms",
            "prove_inclusion_ok",
            "prove_inclusion_path_len",
            "checkpoint_id",
            "checkpoint_merkle_root",
            "checkpoint_ms",
        ]

        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                r_copy = dict(r)
                r_copy["checkpoint_id"] = chk_id if do_checkpoint else ""
                r_copy["checkpoint_merkle_root"] = chk_root if do_checkpoint else ""
                r_copy["checkpoint_ms"] = round(chk_ms, 2) if (do_checkpoint and chk_ms is not None) else ""
                writer.writerow(r_copy)

        # Summaries
        submit_times = [float(r["submit_ms"]) for r in rows if isinstance(r.get("submit_ms"), (int, float)) or (isinstance(r.get("submit_ms"), str) and str(r.get("submit_ms")).strip() != "")]
        avg_submit = _avg(submit_times)
        avg_handshake = float(handshake_ms) if isinstance(handshake_ms, (int, float)) else None

        # Build textual summary
        lines = []
        if avg_handshake is not None:
            lines.append(f"PQC Handshake (Kyber): The POST /handshake endpoint completed in an average of {avg_handshake:.2f} ms.")
        if avg_submit is not None:
            lines.append(f"Claim Submission: The POST /claim/submit, including AI scoring and hash-chain logging, took an average of {avg_submit:.2f} ms.")
        if do_checkpoint and chk_ms is not None:
            z_entries = chk_entries if chk_entries is not None else planned
            lines.append(
                f"Checkpoint Generation: Generating a checkpoint for {z_entries} log entries, including Merkle tree generation and a Dilithium signature, took {chk_ms:.2f} ms."
            )

        summary_text = "\n\n".join(lines) + ("\n" if lines else "")
        if summary_out:
            os.makedirs(os.path.dirname(summary_out) or ".", exist_ok=True)
            with open(summary_out, "w", encoding="utf-8") as sf:
                sf.write(summary_text)

        print(f"✓ Evaluation complete. Wrote {len(rows)} rows to {out_csv}")
        if lines:
            print("\nSummary:\n" + summary_text)


def main():
    parser = argparse.ArgumentParser(description="Evaluate backend API and export CSV")
    parser.add_argument("--backend", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--out", default="evaluation/results.csv", help="Output CSV path")
    parser.add_argument("--num", type=int, default=5, help="Number of claims to submit")
    parser.add_argument("--gen-checkpoint", action="store_true", help="Generate a checkpoint at the end")
    parser.add_argument("--admin-key", default=None, help="Admin API key if required")
    parser.add_argument("--summary-out", default=None, help="Optional summary text output file path")
    parser.add_argument("--target-checkpoint-entries", type=int, default=None, help="Target number of entries included in checkpoint timing (submits additional claims if needed)")
    args = parser.parse_args()

    asyncio.run(
        run_eval(
            args.backend,
            args.out,
            args.num,
            args.gen_checkpoint,
            args.admin_key,
            args.summary_out,
            args.target_checkpoint_entries,
        )
    )


if __name__ == "__main__":
    main()


