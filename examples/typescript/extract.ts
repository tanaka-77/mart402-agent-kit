// Pay-per-call web extraction via x402 (URL -> Markdown + metadata).
//
// Default target is the FREE sandbox on Base Sepolia
// (test USDC: https://faucet.circle.com). For production:
//   MART402_BASE=https://mart402.com
//
// npm install x402-fetch viem
import { privateKeyToAccount } from "viem/accounts";
import { wrapFetchWithPayment } from "x402-fetch";

const BASE = process.env.MART402_BASE ?? "https://mart402.dev";
const account = privateKeyToAccount(process.env.PRIVATE_KEY as `0x${string}`);
const fetchWithPay = wrapFetchWithPayment(fetch, account);

const res = await fetchWithPay(`${BASE}/v1/extract`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  // ttl: cached results are HALF PRICE and marked cache_hit: true
  body: JSON.stringify({ url: "https://en.wikipedia.org/wiki/HTTP_402", mode: "auto" }),
});

const data = await res.json();

// Billing is transparent per call; receipts allow free re-fetch of paid results.
console.log("billed USD:", res.headers.get("x-billed-usd"));
console.log("receipt:", res.headers.get("x-receipt-id"), "(GET /v1/receipts/<id> is free)");

// text_len lets an agent decide cheaply whether to fetch more pages.
console.log(data.title, "| text_len:", data.text_len, "| cache_hit:", data.cache_hit);
console.log(data.markdown?.slice(0, 300));
