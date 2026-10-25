# Zoho Header Check

> Messages sent 2026-10-13 (PT; times below are PT). This file was written on 2026-10-13 outside the repo and moved into `docs/evidence/` on 2026-10-25 without changes to its results.

Authentication results for two messages sent from `mohammad@mjbukhadhour.com` via Zoho Mail to Gmail. Message bodies are intentionally omitted.

## Messages tested

| Test | Subject | Type | Sent |
|------|---------|------|------|
| 01 | Re: Test 01: inbound | Reply | 2:53 PM |
| 02 | Test 02 | New outbound | 2:56 PM |

## Results

Both messages produced identical results.

| Check | Result | Detail |
|-------|--------|--------|
| SPF | PASS | Sending IP `165.173.180.52` |
| DKIM | PASS | Domain `mjbukhadhour.com` |
| DMARC | PASS | |
| Delivery time | 3 seconds | |
| Placement | Inbox | |

## What each check validated

### SPF: the envelope sender

SPF is evaluated against the envelope sender (the SMTP `MAIL FROM`, recorded as `Return-Path`), not the address shown to the recipient. Gmail looked up the SPF record of the envelope sender's domain and confirmed that the connecting IP, `165.173.180.52`, is authorised to send for it.

### DKIM: the zmail selector

DKIM is evaluated against the signing domain and selector named in the `DKIM-Signature` header (`d=mjbukhadhour.com`, `s=zmail`). Gmail fetched the public key published at `zmail._domainkey.mjbukhadhour.com` and verified the signature Zoho applied, confirming the signed headers and body were not altered in transit.

### DMARC: the From header

DMARC is evaluated against the domain in the visible `From` header, `mjbukhadhour.com`. It passes when SPF or DKIM passes with a domain that aligns with the From domain. Here the DKIM signing domain, `mjbukhadhour.com`, matches the From domain exactly, so DMARC passed.

## Conclusion

Outbound mail from `mjbukhadhour.com` through Zoho authenticates on all three checks at Gmail, for both replies and new messages, and lands in the Inbox within seconds.
