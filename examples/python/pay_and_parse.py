#!/usr/bin/env python3
"""Pay-per-call PDF parsing with hallucination-guarded OCR via x402.

Flow: free quote -> pay per page (402 -> sign -> retry, handled by the client)
-> read machine-actionable quality signals before trusting the text.

Default target is the FREE sandbox on Base Sepolia (test USDC from
https://faucet.circle.com). For production set:
  MART402_BASE=https://mart402.com  NETWORK=base

pip install x402 eth-account httpx
"""
import asyncio
import json
import os

from eth_account import Account
from x402.client import x402Client
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact import register_exact_evm_client

BASE = os.environ.get("MART402_BASE", "https://mart402.dev")
NETWORK = os.environ.get("NETWORK", "eip155:84532")
PDF_URL = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"


async def main():
    signer = EthAccountSigner(Account.from_key(os.environ["PRIVATE_KEY"]))
    client = x402Client()
    register_exact_evm_client(client, signer, networks=[NETWORK])

    async with x402HttpxClient(client, timeout=120) as c:
        # 1) Quote is free: know pages and price BEFORE paying.
        r = await c.post(BASE + "/v1/parse/quote", json={"url": PDF_URL})
        quote = json.loads(await r.aread())
        print(f"quote: {quote['pages']} page(s) for ${quote['price_usd']} "
              f"(free, expires in {quote['expires_sec']}s)")

        # 2) Pay and parse. The x402 client handles 402 -> sign -> retry.
        r = await c.post(BASE + "/v1/parse", json={"quote_id": quote["quote_id"]})
        result = json.loads(await r.aread())
        print("billed:", r.headers.get("x-billed-usd"),
              "receipt:", r.headers.get("x-receipt-id"),
              "(re-fetch the paid result for free at /v1/receipts/<id>)")

        # 3) Trust gate: never act on OCR output without reading the signals.
        q = result.get("ocr_quality") or {}
        if q.get("hallucination_suspected"):
            raise SystemExit(f"OCR hallucination suspected {q.get('flags')} "
                             "- do not trust this text")

        cons = result.get("consensus") or {}
        weak = (cons.get("segment_support") or {}).get("weak_segments") or []
        if weak:
            print("weakly corroborated segments - "
                  "verify before acting on numbers or legal text:")
            for w in weak:
                print(f"  support={w['support']}: {w['text'][:60]}")

        print(result["markdown"][:400])


if __name__ == "__main__":
    asyncio.run(main())
