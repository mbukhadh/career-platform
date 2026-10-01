# Azure VM Migration Plan

**Goal:** Run the career-platform app on the Azure VM `vm-career-platform`,
rebuilt from GitHub `main`, and prove it serves the same site as the source.

**Source:** GitHub Codespace (`career-platform`), where the app ran on 9/23–9/24.
**Target:** Azure VM, Ubuntu 24.04 LTS, reached over SSH as `azureuser`.
**Runs from:** my laptop, with Claude Code, the Azure CLI, and the SSH key
`~/.ssh/isba4775_azure`.

**Data decision:** No SQLite file exists in the Codespace to migrate. A
search of the whole Codespace filesystem on 9/29 found no `career_platform.db`,
and `.worktrees/` is empty. The database lived in the feature-branch worktree,
which was removed after the merge on 9/24, and `*.db` is ignored by Git, so no
copy survived. Following the guide's fallback, the VM builds a fresh database
from the migrations and `app/seed.py`. The seed script holds my real profile
content, so the site content should match, but the result is **seed data, not
migrated data**.

**Comparison source:** Because the Codespace has no database either, Verify
compares the VM against a local run on my laptop at the same commit, built the
same way.

Each step lists where it runs, what runs, why, how it's checked, and how it's
undone.

---

## 1. Server

Status: **done before this plan**, recorded here so someone else could repeat it.

- [x] **Create the VM**
  - Where: Azure portal
  - What: resource group `rg-career-platform`, VM `vm-career-platform`,
    Ubuntu Server 24.04 LTS x64 Gen2, user `azureuser`, SSH public key auth,
    public inbound ports None, Standard SSD, delete public IP and NIC with VM.
    Region **North Central US**, size **Standard_B2ats_v2** (2 vCPU, 1 GiB),
    instead of the guide's West US 2 / Standard_B2ts_v2.
  - Why: a Linux server to host the app, with no ports open by default.
  - Check: `az vm show -d` reports the VM, its size, region, and public IP.
  - Undo: delete the resource group (removes every resource in it).

- [x] **Allow SSH from my laptop only**
  - Where: laptop, Azure CLI
  - What: NSG rule `Allow-SSH-Laptop`, priority 300, TCP 22, source
    `LAPTOP-IP/32`, Allow.
  - Why: the key decides who gets in; the rule decides who gets to try.
  - Check: `az network nsg show` lists the rule at 300 ahead of
    `DenyAllInBound` at 65500; a TCP probe to port 22 succeeds.
  - Undo: `az network nsg rule delete -n Allow-SSH-Laptop`.
  - Note (10/1): my laptop's public address changed on a different network and
    SSH would have been dropped. I updated the rule's source to the new `/32`
    with `az network nsg rule update` rather than widening it.

- [x] **Confirm SSH works**
  - Where: laptop
  - What: `ssh -i ~/.ssh/isba4775_azure azureuser@135.232.198.204`, then
    `whoami`, `hostname`, `pwd`, `cat /etc/os-release`,
    `cat ~/.ssh/authorized_keys`
  - Why: every later step runs over this connection.
  - Check: `azureuser`, `vm-career-platform`, `/home/azureuser`,
    Ubuntu 24.04.4 LTS, and the `isba4775_azure` public key line.
  - Undo: nothing to undo; read only.

## 2. Packages

- [x] **Install OS packages**
  - Where: VM, over SSH
  - What: `sudo apt-get update && sudo apt-get install -y git sqlite3`
  - Why: `git` to clone the code; `sqlite3` to inspect and integrity-check the
    database. Installing system software needs `sudo`.
  - Check: `git --version` and `sqlite3 --version` both print versions.
  - Undo: `sudo apt-get remove -y sqlite3` (git ships with the image).
  - Result (10/1): git 2.43.0, sqlite3 3.45.1.

## 3. Code

- [x] **Clone the repository**
  - Where: VM
  - What: `git clone https://github.com/mbukhadh/career-platform.git ~/career-platform`
  - Why: `main` holds the merged app and `uv.lock`. The repo is public, so an
    anonymous, read-only clone needs no credential on the server.
  - Check: `git -C ~/career-platform rev-parse HEAD` on the VM equals
    `git rev-parse HEAD` on my laptop, and `uv.lock` is present.
  - Undo: `rm -rf ~/career-platform`
  - Result (10/1): VM and laptop both at `05103f8`; `uv.lock` present.

## 4. Python

- [x] **Install uv**
  - Where: VM
  - What: `curl -LsSf https://astral.sh/uv/install.sh | sh`, then
    `source ~/.local/bin/env`
  - Why: the lock file is a uv lock file, and uv installs it exactly.
  - Check: `uv --version`
  - Undo: `rm ~/.local/bin/uv ~/.local/bin/uvx`
  - Result (10/1): uv 0.12.21.

- [x] **Build the environment from the lock file**
  - Where: VM, in `~/career-platform`
  - What: `uv sync --locked --no-dev`
  - Why: installs the exact versions tested on my laptop (all 12 tests passed
    against this lock). `--locked` fails rather than re-resolving; `--no-dev`
    skips pytest and ruff, which the server doesn't need.
  - Check: `.venv/` exists and `uv run python -c "import fastapi, uvicorn, sqlalchemy"`
    succeeds.
  - Undo: `rm -rf .venv`
  - Result (10/1): `uv sync --locked --no-dev` succeeded; imports ok on Python 3.12.3.

## 5. Config

- [x] **Create `.env` from the example**
  - Where: VM, in `~/career-platform`
  - What: `cp .env.example .env`, then set `ENVIRONMENT=staging`
  - Why: `.env` is ignored by Git, so it never left the Codespace. The example
    sets `DATABASE_URL=sqlite:///./career_platform.db`, which is a path relative
    to where the app starts, so the app must always start from this folder.
    Resend keys stay blank; the contact form isn't part of today's migration.
  - Check: `grep -E '^(DATABASE_URL|ENVIRONMENT)=' .env` shows the expected
    values, and `.env` doesn't appear in `git status`.
  - Undo: `rm .env`
  - Result (10/1): `DATABASE_URL=sqlite:///./career_platform.db`, `ENVIRONMENT=staging`; `.env` not tracked by Git.

## 6. Data

Changed from the board plan: there is no `.db` file to `scp`, so the database
is built on the VM. See "Data decision" at the top.

- [x] **Create the schema and seed the profile**
  - Where: VM, in `~/career-platform`
  - What: `uv run alembic upgrade head`, then `uv run python -m app.seed`
  - Why: builds `career_platform.db` at the exact path `DATABASE_URL` names.
    The seed script contains my real profile content.
  - Check: `ls -l career_platform.db` exists;
    `sqlite3 career_platform.db "PRAGMA integrity_check;"` prints `ok`;
    `sqlite3 career_platform.db "SELECT slug, name FROM profiles;"` shows
    `mj-bukhadhour`.
  - Undo: `rm career_platform.db` and rerun this step. Nothing reads the file
  - Result (10/1): `career_platform.db` 155,648 bytes; integrity `ok`; `mj-bukhadhour | Mohammad (MJ) Bukhadhour | published`; 1 project.
    yet, so replacing it is safe.

- [x] **Generate the fallback snapshot**
  - Where: VM, in `~/career-platform`
  - What: `uv run python -m app.generate_snapshot --slug mj-bukhadhour`
  - Why: the app serves the latest snapshot if SQLite is unavailable. Without
    one, a database failure becomes a 503 with nothing to fall back on.
  - Check: prints `snapshot generated: mj-bukhadhour (...)` and `snapshots/`
    has a file.
  - Undo: `rm -rf snapshots`
  - Result (10/1): `snapshot generated: mj-bukhadhour`.

## 7. Processes

Replaced by the section 6 detour in the migration guide, which starts the app
itself.

- [ ] **Start Uvicorn reachable from outside, briefly**
  - Where: VM, in `~/career-platform`
  - What: `nohup uv run uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 > ~/uvicorn.log 2>&1 &`
  - Why: `0.0.0.0` accepts connections on every VM address, for one public
    demonstration. `nohup` and `&` keep it running after SSH exits. It won't
    restart on a crash or reboot; systemd takes that over next week.
  - Check: `ss -ltnp | grep 8000` shows `0.0.0.0:8000`.
  - Undo: `pkill -f "uvicorn app.main"`

- [ ] **Open port 8000 temporarily**
  - Where: **portal** (my step)
  - What: inbound rule `Temp-HTTP-8000`, priority 310, source Any, TCP 8000, Allow
  - Why: shows that one firewall rule is the whole difference between private
    and public.
  - Check: `http://135.232.198.204:8000` loads in a browser; screenshot saved as
    `docs/evidence/ex03-site.png`.
  - Undo: delete `Temp-HTTP-8000`.

## 8. Verify

- [ ] **Compare source and target**
  - Where: laptop (source, local run at the same commit) and VM (target)
  - What: record each row below.
  - Why: a page can load and still be wrong.
  - Check: every row matches. Any row that doesn't is recorded as a difference,
    not explained away.
  - Undo: nothing; read only.

| Check | Source (laptop) | Target (VM) | Match |
| --- | --- | --- | --- |
| Commit ID | | | |
| Database integrity | | | |
| Profile row | | | |
| `/healthz` | | | |
| Page content (name, headline, projects) | | | |
| Data origin | seed | seed | — |

- [ ] **Close the public path**
  - Where: portal, then VM
  - What: delete `Temp-HTTP-8000`; restart Uvicorn with `--host 127.0.0.1`
  - Why: two independent locks — no firewall rule for 8000, and an app that
    only answers the VM itself.
  - Check: the public URL times out; `ss -ltnp` shows `127.0.0.1:8000`;
    `curl -s http://127.0.0.1:8000/healthz` over SSH returns `{"status":"ok"}`.
  - Undo: not needed; this is the safe state.

## 9. Shutdown

- [ ] **Stop the app and deallocate**
  - Where: VM, then laptop (Azure CLI)
  - What: `pkill -f "uvicorn app.main"` on the VM; list NSG inbound rules to
    confirm `Temp-HTTP-8000` is gone; then
    `az vm deallocate -g rg-career-platform -n vm-career-platform`
  - Why: stopped still bills for compute; deallocated doesn't. The disk and
    public IP still cost a little.
  - Check: `az vm get-instance-view` reports `VM deallocated`, not
    `VM stopped`.
  - Undo: `az vm start -g rg-career-platform -n vm-career-platform`

**Rollback for the whole migration:** the Codespace still has the code at the
same commit, and the site can be rebuilt there with the same seed. Nothing on
the source side is changed by this plan.
