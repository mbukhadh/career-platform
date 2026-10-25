# DNS After Zoho Setup

> Written on 2026-10-13 outside the repo and moved into `docs/evidence/` on 2026-10-25. The only change is that Cloudflare's NEL reporting tokens in the `curl` output were replaced with `[redacted]`. The apex A record shown here is from before the Railway cutover.

Mail-related DNS records for `mjbukhadhour.com`, compared with what Zoho Mail expects.

- **Checked:** 2026-10-13 22:06 UTC
- **Resolver:** Google Public DNS (`8.8.8.8`), cross-checked against the authoritative nameserver `piper.ns.cloudflare.com`
- **Nameservers:** `graham.ns.cloudflare.com`, `piper.ns.cloudflare.com` (registrar: Namecheap)

## Method and limits

Records were read with `dig @8.8.8.8` and again directly from the authoritative Cloudflare nameserver. Both returned identical answers.

The Cloudflare CLI part was **not done**: no Cloudflare CLI (`flarectl`, `wrangler`, `cloudflared`) is installed on this machine and no Cloudflare API token is set. The zone was therefore not listed from the Cloudflare side. DNS lookups can only answer for names that are asked about, so a record at an unusual name would not show up here.

## Comparison with Zoho's expected values

| Record | Name | Expected | Found | Status |
|--------|------|----------|-------|--------|
| MX | `@` | `mx.zoho.com` (10) | `mx.zoho.com` (10) | Match |
| MX | `@` | `mx2.zoho.com` (20) | `mx2.zoho.com` (20) | Match |
| MX | `@` | `mx3.zoho.com` (50) | `mx3.zoho.com` (50) | Match |
| SPF | `@` | `v=spf1 include:zohomail.com ~all` | `v=spf1 include:zohomail.com ~all` | Match |
| DKIM | `zmail._domainkey` | starts with `v=DKIM1` | `v=DKIM1; k=rsa; p=MIGfMA0G…` | Match |
| DMARC | `_dmarc` | `v=DMARC1; p=none; rua=mailto:mohammad@mjbukhadhour.com` | `v=DMARC1; p=none; rua=mailto:mohammad@mjbukhadhour.com` | Match |

All four record types match. There are exactly three MX records and no others.

## Flags

| Check | Result |
|-------|--------|
| Duplicate SPF records | None. The apex has exactly one `v=spf1` TXT record. |
| Leftover `registrar-servers.com` records | None found. No MX, TXT, NS, A or CNAME answer at the apex references `registrar-servers.com`, `efwd` or `namecheap`. |

The leftover check also probed these subdomains for A, CNAME, MX and TXT records: `mail`, `webmail`, `autodiscover`, `autoconfig`, `ftp`, `cpanel`, `smtp`, `imap`, `pop`, `email`, `mx`, and the wildcard `*`. None returned a record.

## Raw records (from 8.8.8.8)

```
mjbukhadhour.com.                  300   IN MX   10 mx.zoho.com.
mjbukhadhour.com.                  300   IN MX   20 mx2.zoho.com.
mjbukhadhour.com.                  300   IN MX   50 mx3.zoho.com.

mjbukhadhour.com.                  300   IN TXT  "v=spf1 include:zohomail.com ~all"
mjbukhadhour.com.                  300   IN TXT  "zoho-verification=zb68579034.zmverify.zoho.com"

zmail._domainkey.mjbukhadhour.com. 300   IN TXT  "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC6+7wVv9DwY508GMNgKtZzORqcCZ+d/IwvocjVi2wmOrBWpytRqc3jolHjvQbO7t7fbTONOPL2y9VYpS6umc4U82zsk6VpwBiVPvI7igfgcTVAPKtc55aJqtb9h219j6lSQYT7EM4VKhJYpaTfSvN+XVjrD37Md5k3r/qU9PmcCQIDAQAB"

_dmarc.mjbukhadhour.com.           300   IN TXT  "v=DMARC1; p=none; rua=mailto:mohammad@mjbukhadhour.com"

mjbukhadhour.com.                  21600 IN NS   graham.ns.cloudflare.com.
mjbukhadhour.com.                  21600 IN NS   piper.ns.cloudflare.com.
```

## Other records seen

| Name | Type | Value | Note |
|------|------|-------|------|
| `@` | TXT | `zoho-verification=zb68579034.zmverify.zoho.com` | Zoho domain ownership record, expected |
| `@` | A | `135.232.198.204` | Website, not mail-related |
| `www` | A | `135.232.198.204` | Website, not mail-related. Value at 22:06 UTC; changed since, see "www lookup and redirect test" below |
| `_domainconnect` | TXT | `api.cloudflare.com/client/v4/dns/domainconnect` | Added by Cloudflare |

## Notes

- The DKIM public key is 1024-bit RSA. It is valid and passes, but 2048-bit is the current recommendation.
- DMARC is at `p=none`, which reports but does not enforce.

## Conclusion

Public DNS for `mjbukhadhour.com` matches Zoho's expected MX, SPF, DKIM and DMARC values, with no duplicate SPF record and no `registrar-servers.com` leftovers in anything that could be queried. A Cloudflare-side zone listing is still outstanding.

## www lookup and redirect test

- **Checked:** 2026-10-13 22:20 UTC, `dig @8.8.8.8`, confirmed against `piper.ns.cloudflare.com`

### What DNS returns for `www.mjbukhadhour.com`

| Type | Address | Owner |
|------|---------|-------|
| A | `104.21.48.164` | Cloudflare, Inc. (`104.16.0.0/12`, CLOUDFLARENET) |
| A | `172.67.154.88` | Cloudflare, Inc. (`172.64.0.0/13`, CLOUDFLARENET) |
| AAAA | `2606:4700:3031::6815:30a4` | Cloudflare, Inc. (`2606:4700::/32`, CLOUDFLARENET) |
| AAAA | `2606:4700:3034::ac43:9a58` | Cloudflare, Inc. (`2606:4700::/32`, CLOUDFLARENET) |

There is no CNAME answer for `www`.

### Comparison with the VM IP

| Name | Address returned | Matches VM IP `135.232.198.204` |
|------|------------------|---------------------------------|
| `www.mjbukhadhour.com` | Cloudflare addresses above | No |
| `mjbukhadhour.com` | `135.232.198.204` | Yes |

The VM IP `135.232.198.204` belongs to Microsoft (range `135.232.0.0/16`, maintained by `MICROSOFT-MAINT`, announced by AS8075).

DNS for `www` does not return the VM IP. It returns Cloudflare edge addresses, which is what a proxied (orange-cloud) record looks like from outside: visitors connect to Cloudflare, and the address Cloudflare forwards to is not visible in public DNS. The apex `mjbukhadhour.com` still returns the VM IP directly, so it is not proxied.

This is a change from the 22:06 UTC lookup above, when `www` returned `135.232.198.204`.

### www redirect test

Tested in an Incognito window, reported by the site owner. Confirmed with `curl -I` below.

| Start URL | Final URL | Status |
|-----------|-----------|--------|
| `http://www.mjbukhadhour.com` | `https://mjbukhadhour.com` | 301 |
| `https://www.mjbukhadhour.com` | `https://mjbukhadhour.com` | 301 |

Both `www` variants redirect permanently to the HTTPS apex.

### curl -I output

Run 2026-10-13 22:21 UTC. Both commands exited 0. `curl -I` does not follow redirects, so each block is the first response only.

```
$ curl -I http://www.mjbukhadhour.com
HTTP/1.1 301 Moved Permanently
Date: Tue, 13 Oct 2026 22:21:53 GMT
Content-Type: text/html; charset=UTF-8
Connection: keep-alive
Location: https://mjbukhadhour.com/
Report-To: [redacted: Cloudflare NEL reporting token]
Nel: {"report_to":"cf-nel","success_fraction":0.0,"max_age":604800}
Server: cloudflare
CF-RAY: a4a1bd6879da08ac-LAX
```

```
$ curl -I https://www.mjbukhadhour.com
HTTP/2 301
date: Tue, 13 Oct 2026 22:21:53 GMT
content-type: text/html; charset=UTF-8
location: https://mjbukhadhour.com/
report-to: [redacted: Cloudflare NEL reporting token]
nel: {"report_to":"cf-nel","success_fraction":0.0,"max_age":604800}
server: cloudflare
cf-ray: a4a1bd6b2ab4bdf2-DUB
```

Both URLs answer `301` with `Location: https://mjbukhadhour.com/` in a single hop, and both responses come from Cloudflare (`Server: cloudflare`), consistent with the proxied `www` record.
