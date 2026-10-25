# Project 1 checks, 2026-10-25

Checks run on 2026-10-25 between 23:05 and 23:12 UTC from my laptop, with Claude
Code running the commands. These were run after the submission deadline to
replace or confirm evidence that wasn't saved at the time. The Azure restart
in section 3 happened on 2026-10-06; it is read **retrospectively** from the
VM's own logs. Nothing on the VM, Railway or Cloudflare was changed by these checks.

## 1. Domain and HTTPS (Railway)

```text
$ dig +short mjbukhadhour.com A
69.46.46.119
$ whois 69.46.46.119 | grep OrgName
OrgName:        Railway
$ dig +short TXT _railway-verify.mjbukhadhour.com
"railway-verify=…"            (value present; shortened here)

$ curl -s -o /dev/null -w "%{http_code}\n" https://mjbukhadhour.com/
200
$ curl -sI https://mjbukhadhour.com/healthz | grep -iE "^(HTTP|server)"
HTTP/2 200
server: railway-hikari
$ curl -s https://mjbukhadhour.com/healthz
{"status":"ok"}

$ echo | openssl s_client -connect mjbukhadhour.com:443 -servername mjbukhadhour.com \
    | openssl x509 -noout -subject -issuer -dates
subject= /CN=mjbukhadhour.com
issuer= /C=US/O=Let's Encrypt/CN=YR2
notBefore=Oct 15 21:29:44 2026 GMT
notAfter=Jan 13 21:29:43 2027 GMT
```

The bare domain resolves to a Railway address, the response comes from
Railway's edge (`server: railway-hikari`), and Railway's Let's Encrypt
certificate for `mjbukhadhour.com` is valid until 2027-01-13. The
`notBefore` time, 2026-10-15 21:29 UTC, is when Railway issued it. No other
record of the cutover time was saved.

### www redirect

```text
$ dig +short www.mjbukhadhour.com A
104.21.48.164
172.67.154.88                 (Cloudflare addresses: www is proxied)

$ curl -sI http://www.mjbukhadhour.com/ | grep -iE '^(HTTP|location|server)'
HTTP/1.1 301 Moved Permanently
Location: https://mjbukhadhour.com/
Server: cloudflare

$ curl -sI https://www.mjbukhadhour.com/ | grep -iE '^(HTTP|location|server)'
HTTP/2 301
location: https://mjbukhadhour.com/
server: cloudflare

$ curl -sL -o /dev/null -w "%{http_code} %{url_effective} ssl_verify=%{ssl_verify_result}\n" https://www.mjbukhadhour.com/
200 https://mjbukhadhour.com/ ssl_verify=0

$ echo | openssl s_client -connect www.mjbukhadhour.com:443 -servername www.mjbukhadhour.com \
    | openssl x509 -noout -subject -issuer -enddate
subject= /CN=mjbukhadhour.com
issuer= /C=US/O=Let's Encrypt/CN=YE1
notAfter=Dec 30 20:57:21 2026 GMT
```

Both `www` variants answer with one 301 to `https://mjbukhadhour.com/`.
The `https://www` certificate is Cloudflare's edge certificate (valid until
2026-12-30, renewed by Cloudflare), and following the redirect ends at 200
with certificate verification OK (`ssl_verify=0`).

### Live page reads the database

```text
$ curl -s https://mjbukhadhour.com/ | sed 's/<[^>]*>/ /g' | grep -i "profile source"
Profile source: database · Privacy · Cookie settings
```

The footer says `database`, not `snapshot`, so this request was served from
Railway PostgreSQL.

## 2. Railway deployments (from GitHub)

Railway reports each deployment to GitHub. Read with
`curl https://api.github.com/repos/mbukhadh/career-platform/deployments`
and each deployment's `statuses_url`:

| Commit | Environment | Created (UTC) | Latest status |
| --- | --- | --- | --- |
| `81403ba` | wholesome-solace / production | 2026-10-16 00:18 | success (00:19) |
| `8da68cc` | wholesome-solace / production | 2026-10-16 00:15 | inactive |
| `e7caa8c` | wholesome-solace / production | 2026-10-16 00:02 | inactive |
| `b198f61` | wholesome-solace / production | 2026-10-15 23:42 | inactive |
| `533a75c` | wholesome-solace / production | 2026-10-15 23:34 | inactive |
| `4cb9270` | wholesome-solace / production | 2026-10-15 22:56 | inactive |
| `6bfa632` | wholesome-solace / production | 2026-10-15 21:45 | inactive |
| `5edf39a` | wholesome-solace / production | 2026-10-13 18:09 | inactive |
| `8550408` | wholesome-solace / production | 2026-10-13 17:59 | inactive |
| `034c890` | wholesome-solace / production | 2026-10-13 17:44 | inactive |

"Inactive" means a later deployment replaced it. GitHub has no deployment
record for the commits before `034c890` (including `d4bee5f`, the Railway
code changes) or for `6dd6af4` and `14df95e` (2026-10-20). Railway's own build
and deploy logs were not saved and I can't read them from this machine (no
Railway CLI), so they are **unverified**.

The running code matches `main`. These files are byte-identical on the live
site and in the repo (SHA-256 prefix):

| File | Live | `main` |
| --- | --- | --- |
| `static/js/consent.js` | `97fde8e7da61` | `97fde8e7da61` |
| `static/css/site.css` | `ab623ad69fc5` | `ab623ad69fc5` |

## 3. Azure VM

```text
$ az vm show -d -g rg-career-platform -n vm-career-platform --query "{state:powerState,ip:publicIps,size:hardwareProfile.vmSize}"
{ "ip": "135.232.198.204", "size": "Standard_B2ats_v2", "state": "VM running" }

$ az network nsg rule list -g rg-career-platform --nsg-name vm-career-platform-nsg -o table
Name              Prio    Port    Src                Access
Allow-SSH-Laptop  300     22      <my laptop IP>/32  Allow
Allow-HTTP-80     310     80      *                  Allow
Allow-HTTPS-443   320     443     *                  Allow
```

No rule opens port 8000. The auto-shutdown schedule
(`shutdown-computevm-vm-career-platform`, 19:00 Pacific) is **Disabled**.

On the VM:

```text
$ systemctl is-enabled career-platform nginx
enabled
enabled
$ systemctl is-active career-platform nginx
active
active
$ curl -s http://127.0.0.1:8000/healthz
{"status":"ok"}
$ curl -sk -o /dev/null -w "%{http_code}\n" https://135.232.198.204/
200
$ sudo certbot certificates | grep -E "Domains|Expiry"
    Domains: mjbukhadhour.com www.mjbukhadhour.com
    Expiry Date: 2027-01-04 21:08:22+00:00 (VALID: 70 days)
$ systemctl list-timers certbot.timer
NEXT Mon 2026-10-26 03:02:46 UTC   LAST Sun 2026-10-25 12:33:27 UTC
```

### Restart evidence (retrospective, read from the VM's logs)

```text
$ last -x reboot shutdown | head -2
reboot   system boot  7.0.0-1014-azure Tue Oct  6 20:58   still running
shutdown system down  7.0.0-1014-azure Fri Oct  2 02:01 - 20:58 (4+18:57)

$ journalctl -b 0 -u career-platform -u nginx -o short-iso | head
2026-10-06T20:58:58 systemd[1]: Started career-platform.service - Career Platform (FastAPI on Uvicorn).
2026-10-06T20:58:59 systemd[1]: Started nginx.service - A high performance web server and a reverse proxy server.
2026-10-06T20:59:00 uvicorn[665]: INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
2026-10-06T20:59:03 uvicorn[868]: INFO:     Application startup complete.
2026-10-06T20:59:03 uvicorn[866]: INFO:     Application startup complete.
2026-10-06T21:43:40 uvicorn[868]: INFO:     127.0.0.1:47240 - "GET /healthz HTTP/1.1" 200 OK
```

The VM shut down on 2026-10-02 at 02:01 UTC (the time matches the 19:00
Pacific auto-shutdown schedule) and was started again on 2026-10-06 at 20:58 UTC. This was
the first boot after systemd was set up on 2026-10-01
([operate-the-VM plan](../superpowers/plans/2026-10-01-operate-the-vm.md)).
systemd started the app with two workers and nginx 7 seconds after boot, and
nobody started them by hand. This was a stop and start, not a deliberate
`sudo reboot` test, and no outside HTTP check was saved right after it.

## 4. Local tests

```text
$ uv run pytest -q
33 passed, 202 warnings in 0.94s
```

Run on `main` at `cdd89c6`. Test coverage includes
`tests/routes/test_database_down.py`. That test checks the current failure
behaviour (a 503 "Temporarily unavailable" page), **not** the assignment's
"profile visible, Projects temporarily unavailable" behaviour, which the app
does not implement yet.

## 5. Final push and Railway deployment

Pushed `8281f58` (docs only) to `main` at 2026-10-25 23:17:00 UTC.

```text
$ curl -s "https://api.github.com/repos/mbukhadh/career-platform/deployments?sha=8281f58b167a490bbe61a364f878b13bd1524d96"
id 7320646074, environment "wholesome-solace / production", created 2026-10-25T23:17:04Z
$ curl -s https://api.github.com/repos/mbukhadh/career-platform/deployments/7320646074/statuses
in_progress 2026-10-25T23:17:04Z
success     2026-10-25T23:17:56Z
$ curl -s -o /dev/null -w "%{http_code}\n" https://mjbukhadhour.com/    # 23:18 UTC
200
$ curl -s https://mjbukhadhour.com/healthz
{"status":"ok"}
```

Railway deployed a docs-only commit 4 seconds after the push, so it does
not skip docs-only commits. Why `6dd6af4` and `14df95e` (2026-10-20) have no
deployment record is still **unverified**. The commit that adds this section
was pushed afterwards; its deployment was checked in the terminal and is
not recorded here, because recording it would need another commit.

## 6. Public database access and live site

**What the dashboard shows (read by MJ):** 2026-10-25 about 16:41 PT
(23:41 UTC). Railway › Postgres service › Settings › Networking shows "Add
Public Access" and no `DATABASE_PUBLIC_URL`.

**What this machine sees:** the old proxy address saved in the local `.env`
as `RAILWAY_DATABASE_URL`, a `*.rlwy.net` host and port. Neither value is
printed. No login was attempted and no data was read in these checks.

```text
2026-10-25 23:42:06 UTC
DNS: resolves to 1 address
TCP try 1: OPEN (connection accepted)
TCP try 2: OPEN (connection accepted)
TCP try 3: OPEN (connection accepted)

2026-10-25 23:42:17 UTC
sent PostgreSQL SSLRequest (8 bytes, no user, no password)
reply byte: b'S'  -> a PostgreSQL server answered (accepts SSL)
```

Earlier the same day, at 23:13, 23:28 and 23:37 UTC, logins with the saved
`.env` credentials reached a PostgreSQL server there and failed with
`password authentication failed`.

**Result:** these two observations conflict. The `.env` address still leads
to a PostgreSQL server that accepts connections from the internet, one
minute after the dashboard showed no public access on the service MJ checked.
I did not change the record to "no proxy". Still to settle: which Railway
service, environment or project owns that address.

**Live site:**

```text
2026-10-25 23:42:34 UTC
$ curl -s -o l.html -w "HTTP %{http_code}\n" https://mjbukhadhour.com/
HTTP 200
$ grep -oE '<h1>[^<]*</h1>|<h3>Career Platform</h3>|Projects source: database|Projects temporarily unavailable' l.html
<h1>Mohammad (MJ) Bukhadhour</h1>
<h3>Career Platform</h3>
Projects source: database
server: railway-hikari
```

The site is up and reads projects from its database.

**Railway trial (read by MJ from the dashboard):** 2026-10-25 16:39 PT,
"13 days or $4.28 left". That puts the end at about 2026-11-07.
