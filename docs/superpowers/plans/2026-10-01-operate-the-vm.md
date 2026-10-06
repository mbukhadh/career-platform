# Operate the VM Plan

**Goal:** Serve the site at `http://135.232.198.204` (no port), started by the
VM itself instead of by hand, restarted on a crash, with port 8000 closed to the
Internet and the app running as `azureuser`, not root.

**VM (read from the Azure CLI on 10/1, read only):**

| | |
| --- | --- |
| Subscription | Azure for Students |
| Resource group | `RG-CAREER-PLATFORM` |
| VM | `vm-career-platform`, Ubuntu 24.04 LTS, Standard_B2ats_v2 (2 vCPU, 1 GiB; 837 MB usable), North Central US |
| Power state | VM running |
| Public IP | `135.232.198.204` (no DNS name) |
| Private IP | `172.16.0.4` |
| Login | `azureuser`, SSH key only (password login off) |
| SSH | `ssh -i ~/.ssh/isba4775_azure azureuser@135.232.198.204` |
| NSG | `vm-career-platform-nsg`: only inbound rule is `Allow-SSH-Laptop` (TCP 22 from `LAPTOP-IP/32`, my current IP) |

**Uses what's already there:** code in `~/career-platform`, its `.venv`, `.env`,
`career_platform.db`, and `snapshots/`. No repo files change. The two new files
live outside the repo, in `/etc`.

**How the pieces fit (the beginner version):**

```
Internet ──port 80──▶ NSG rule Allow-HTTP-80 ──▶ nginx (port 80)
                                                   │ forwards to
                                                   ▼
                                     Uvicorn on 127.0.0.1:8000 (2 workers)
                                     started and watched by systemd,
                                     running as azureuser
```

- **systemd** is Linux's service manager. It starts programs at boot and
  restarts them when they die. We give it a small "unit" file describing the app.
- **nginx** is a web server that sits on port 80 and passes each request to the
  app. Only a root process can open ports below 1024, so nginx does that part;
  its request-handling workers run as `www-data`, and the app never needs root.
- **127.0.0.1** means "this machine only." The app listens there, so even if
  someone opened port 8000 in Azure by mistake, nothing would answer.
- **Two workers** means two copies of the app share the traffic. If one
  crashes, the other keeps serving while Uvicorn starts a replacement. If the
  whole service dies, systemd restarts it. nginx keeps running either way.

Each step lists where it runs, what runs, why, how it's checked, and how it's
undone. "VM" means in an SSH session as `azureuser`.

---

## 1. Preflight

- [x] **Connect and stop the hand-started app**
  - Where: laptop, then VM
  - What: `ssh -i ~/.ssh/isba4775_azure azureuser@135.232.198.204`, then
    `pkill -f "[u]vicorn app.main" || true`
  - Why: a hand-started Uvicorn would hold port 8000 and block the service.
    `|| true` keeps it from looking like an error if nothing was running.
    The brackets stop the pattern from matching the shell running `pkill`.
    (`[u]` still matches the letter u, but the shell's own command line
    contains `[u]`, not `u`.)
  - Check: `ss -ltnp | grep :8000` prints nothing; `free -m` shows enough free
    memory for two workers (roughly 300 MB).
  - Undo: nothing to undo; the service replaces it.
  - Result (10/1): The first run, sent as one `ssh '…'` command with the plain
    pattern `"uvicorn app.main"`, matched its own shell. `pkill` killed the SSH
    session (exit 255). Before that, nothing was listening on :8000, and the
    only match was that shell. The rerun with `"[u]vicorn app.main"` found no
    Uvicorn to stop (`pkill` exit 1 = nothing matched), and `ss` showed nothing
    on :8000. Memory: 837 MB total, 601 MB available, no swap. That's enough
    for two workers, but without swap there's no cushion if memory runs out.

## 2. App service (systemd)

- [x] **Create the unit file**
  - Where: VM
  - What:
    ```bash
    sudo tee /etc/systemd/system/career-platform.service > /dev/null <<'EOF'
    [Unit]
    Description=Career Platform (FastAPI on Uvicorn)
    After=network-online.target
    Wants=network-online.target

    [Service]
    User=azureuser
    Group=azureuser
    WorkingDirectory=/home/azureuser/career-platform
    ExecStart=/home/azureuser/career-platform/.venv/bin/uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --workers 2
    Restart=always
    RestartSec=2

    [Install]
    WantedBy=multi-user.target
    EOF
    ```
  - Why, line by line:
    - `User`/`Group`: run as `azureuser`, not root.
    - `WorkingDirectory`: `.env` and `DATABASE_URL=sqlite:///./career_platform.db`
      are relative paths, so the app must start in this folder.
    - `ExecStart`: calls the venv's `uvicorn` directly. systemd doesn't load
      my shell's PATH, so `uv` and `source .venv/bin/activate` aren't available.
    - `--workers 2`: one per vCPU, and the crash cushion described above.
    - `Restart=always`, `RestartSec=2`: if the service exits for any reason,
      start it again after 2 seconds.
    - `WantedBy=multi-user.target`: start it at normal boot.
  - Check: `systemd-analyze verify /etc/systemd/system/career-platform.service`
    prints no errors.
  - Undo: `sudo rm /etc/systemd/system/career-platform.service && sudo systemctl daemon-reload`
  - Result (10/1): First confirmed that `.venv/bin/uvicorn`, `.env`,
    `career_platform.db`, and a snapshot (`mj-bukhadhour-v4fc948b….json`)
    exist in `~/career-platform`. Wrote the unit exactly as above;
    `systemd-analyze verify` reported no errors.

- [x] **Enable and start it**
  - Where: VM
  - What: `sudo systemctl daemon-reload && sudo systemctl enable --now career-platform`
  - Why: `daemon-reload` makes systemd read the new file; `enable` means start
    at boot; `--now` also starts it right away.
  - Check:
    - `systemctl is-enabled career-platform` → `enabled`
    - `systemctl is-active career-platform` → `active`
    - `ss -ltnp | grep :8000` → `127.0.0.1:8000` (not `0.0.0.0`)
    - `ps -eo user,cmd | grep [u]vicorn` → every line starts with `azureuser`
      (a parent plus two workers)
    - `curl -s http://127.0.0.1:8000/healthz` → `{"status":"ok"}`
    - If anything fails: `journalctl -u career-platform -n 50` shows why.
  - Undo: `sudo systemctl disable --now career-platform`
  - Result (10/1): `enable --now` created the boot link
    (`multi-user.target.wants/career-platform.service`).
    - `is-enabled` → `enabled`; `is-active` → `active`
    - `ss` → `127.0.0.1:8000`, held by the parent `uvicorn` (pid 1711) and
      two worker processes (1714, 1715)
    - `ps` → all four processes (parent, two workers, and Python's
      multiprocessing resource tracker) run as `azureuser`. `ps` prints it
      shortened as `azureus+`.
    - `/healthz` → `{"status":"ok"}`; `/` → `<h1>Mohammad (MJ) Bukhadhour`
    - journal: started 22:24:38 UTC, both workers report "Application startup
      complete", both requests `200 OK`
    - Memory after start: 463 MB available (down from 601 MB). Each worker
      uses about 70 MB.

## 3. Front door (nginx)

- [x] **Install nginx**
  - Where: VM
  - What: `sudo apt-get update && sudo apt-get install -y nginx`
  - Why: puts a web server on port 80. Ubuntu enables and starts it on install.
  - Check: `systemctl is-enabled nginx` → `enabled`; `curl -sI http://127.0.0.1`
    returns the nginx welcome page headers.
  - Undo: `sudo apt-get purge -y nginx nginx-common`
  - Result (10/1): Before: nothing on :80, nginx not installed. Installed
    nginx 1.24.0 (Ubuntu). `is-enabled` → `enabled`, `is-active` → `active`;
    `curl -sI http://127.0.0.1` → `HTTP/1.1 200 OK`, title "Welcome to nginx!".

- [x] **Point nginx at the app**
  - Where: VM
  - What:
    ```bash
    sudo tee /etc/nginx/sites-available/career-platform > /dev/null <<'EOF'
    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    EOF
    sudo ln -s /etc/nginx/sites-available/career-platform /etc/nginx/sites-enabled/career-platform
    sudo rm /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl reload nginx
    ```
  - Why: `default_server` and `server_name _` answer any request to port 80,
    including one addressed by bare IP. `proxy_pass` forwards to the app. The
    `proxy_set_header` lines pass along the original host and visitor address.
    Removing `sites-enabled/default` only removes a link; the welcome page
    config stays in `sites-available`. `nginx -t` checks the syntax before the
    reload, so a typo can't take nginx down.
  - Check: `curl -s http://127.0.0.1/healthz` (port 80, through nginx) →
    `{"status":"ok"}`; `curl -s http://127.0.0.1/ | grep -o '<h1>[^<]*'` shows
    my name.
  - Undo: `sudo rm /etc/nginx/sites-enabled/career-platform && sudo ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default && sudo systemctl reload nginx`
  - Result (10/1): Wrote the site file exactly as above. `sites-enabled` now
    holds only the `career-platform` link; `default` is still in
    `sites-available`. `nginx -t` → syntax ok, test successful; reloaded.
    - `http://127.0.0.1/healthz` (port 80) → `{"status":"ok"}`
    - `http://127.0.0.1/` → `200`, `<h1>Mohammad (MJ) Bukhadhour`
    - `/static/css/site.css` through nginx → `200 text/css`, 624 bytes. My
      first try printed `000`. That was a bug in my check, which put the host
      in front of an href that was already absolute, not a site problem.
    - The page builds absolute asset links from the `Host` header. With
      `Host: 135.232.198.204`, the stylesheet link is
      `http://135.232.198.204/static/css/site.css`, which is why
      `proxy_set_header Host $host` matters.
    - Listeners: nginx on `0.0.0.0:80` and `[::]:80`; app still only on
      `127.0.0.1:8000`.
    - nginx processes: master runs as `root` (to open port 80), workers as
      `www-data`. The app's log shows the proxied requests (`HTTP/1.0`, from
      `127.0.0.1`) answered `200 OK`.

## 4. Firewall

- [ ] **Open port 80**
  - Where: **Azure portal (my step)**
  - What: inbound rule on `vm-career-platform-nsg`: name `Allow-HTTP-80`,
    priority 320, source Any, TCP 80, Allow
  - Why: the NSG blocks everything not explicitly allowed. This opens port 80
    only. There is no rule for 8000, and none is added.
  - Check (laptop, read only):
    `az network nsg rule list -g RG-CAREER-PLATFORM --nsg-name vm-career-platform-nsg -o table`
    lists `Allow-SSH-Laptop` (300) and `Allow-HTTP-80` (320) and nothing for 8000.
  - Undo: delete `Allow-HTTP-80` in the portal.

## 5. Verify

- [ ] **Check every requirement from outside**
  - Where: laptop
  - What and expected result:

| Requirement | Check (laptop) | Expected |
| --- | --- | --- |
| Reachable with no port | `curl -s -o /dev/null -w "%{http_code}\n" http://135.232.198.204/` | `200` |
| Same app, healthy | `curl -s http://135.232.198.204/healthz` | `{"status":"ok"}` |
| Right page | open `http://135.232.198.204` in a browser | my profile, name in the heading |
| 8000 closed | `curl -sS --max-time 5 http://135.232.198.204:8000/healthz` | timeout, no response |
| Starts at boot | `ssh … systemctl is-enabled career-platform nginx` | `enabled` twice |
| Not root | `ssh … "ps -eo user,cmd \| grep [u]vicorn"` | only `azureuser` |
| Listens locally only | `ssh … "ss -ltnp \| grep :8000"` | `127.0.0.1:8000` |

  - Why: each row maps to one line of the goal, checked the way a visitor or an
    attacker would see it, not just from inside the VM.
  - Undo: nothing; read only.

**Left for me to run myself:** crash tests (killing a worker, killing the
service) and the reboot test.

**Rollback for the whole plan:** remove `Allow-HTTP-80`, then on the VM run
`sudo systemctl disable --now career-platform nginx`, delete the two files
added under `/etc`, and `sudo systemctl daemon-reload`. The repo, `.venv`,
`.env`, and database are untouched, so the hand-start command from the
migration plan still works.
