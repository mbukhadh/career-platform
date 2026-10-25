# Project 1 submission

| | |
| --- | --- |
| Repository | https://github.com/mbukhadh/career-platform |
| Live site | https://mjbukhadhour.com |
| Final commit | The newest commit on `main` (`git rev-parse origin/main`), entered in Brightspace. It is the commit right after `978ed493477d8252e271a8bc83cf4b7603746190` (last content commit) and only updates this line. A file can't contain its own commit's SHA. |

Updated 2026-10-25, after the deadline. Items marked **unverified** or
**not done** have no proof yet. The [README](../README.md) is a retrospective
record; the plans it links to were written before the work.

## 1. README, original spec and plans

- [README](../README.md)
- Original spec: [`2026-09-23-personal-resume-career-platform-design.md`](superpowers/specs/2026-09-23-personal-resume-career-platform-design.md)
- Original plan: [`2026-09-23-personal-resume-career-platform-plan.md`](superpowers/plans/2026-09-23-personal-resume-career-platform-plan.md)

## 2. Azure and Railway diagrams, with email and analytics flow

- [README › Architecture](../README.md#architecture): Railway, Azure, email (Zoho) and analytics (GA4) diagrams
- [Request path diagram](request-path-diagram.md), with [Railway PNG](images/request-path-railway.png) and [Azure PNG](images/request-path-azure.png)

## 3. Migration plans, data comparison, cutover, rollback

- Azure: [`2026-09-24-azure-vm-migration.md`](superpowers/plans/2026-09-24-azure-vm-migration.md), [`2026-10-01-operate-the-vm.md`](superpowers/plans/2026-10-01-operate-the-vm.md)
- Railway spec: [`2026-10-08-railway-postgres-migration-design.md`](superpowers/specs/2026-10-08-railway-postgres-migration-design.md)
- Railway plan, with cutover results: [`2026-10-08-railway-postgres-migration.md`](superpowers/plans/2026-10-08-railway-postgres-migration.md) (sections 3–5 filled in retrospectively on 2026-10-25)
- Source/target data comparison: [`railway-data-comparison.md`](evidence/railway-data-comparison.md) (commit `8550408`, 2026-10-13). **Not done:** a real data edit before the transfer.
- [README › Migration](../README.md#migration-azure-vm-to-railway), [Who manages what](../README.md#who-manages-what), [Rollback](../README.md#rollback)

## 4. Azure HTTP/restart evidence, final DNS/HTTPS

- Azure site served from the VM: [`ex03.md`](evidence/ex03.md)
- systemd, nginx and firewall setup: [operate-the-VM plan](superpowers/plans/2026-10-01-operate-the-vm.md)
- Ex04 HTTPS explanation (certificate, renewal, ports): [`how-this-site-is-secured.md`](how-this-site-is-secured.md)
- Restart (retrospective, from VM logs), NSG rules, services: [checks §3](evidence/project-1-checks-2026-10-25.md#3-azure-vm)
- Final DNS/HTTPS and `www` redirect: [checks §1](evidence/project-1-checks-2026-10-25.md#1-domain-and-https-railway); earlier `www` test (2026-10-13): [`dns-after-zoho.md`](evidence/dns-after-zoho.md#www-redirect-test)

## 5. Reviewed commit, Railway deployment, live change

- Commit [`10c43e3`](https://github.com/mbukhadh/career-platform/commit/10c43e3f3ebf077a41eb809541c5017497f72c15): keep the profile visible when the projects query fails. **Reviewed by me (MJ)** on 2026-10-25 from `git diff main...HEAD` before the merge (no GitHub pull request).
- Local checks before merge: 34 tests passed, and the failure and recovery were reproduced locally ([`db-failure-recovery.md`](evidence/db-failure-recovery.md)).
- Railway deployment `7320808074`, `success` at 2026-10-25 23:32:31 UTC.
- Live check, 2026-10-25 23:32:46 UTC: `https://mjbukhadhour.com` returned 200, and the footer changed from `Profile source: database` to `Projects source: database`. Details in [README › Verified website update](../README.md#verified-website-update-requirement-5).
- Recovery: [README › Rollback](../README.md#rollback), covering the revert for `10c43e3` (database impact: none).

## 6. Zoho email

- Send, receive and reply results, plus SPF/DKIM/DMARC: [`ex06.md`](evidence/ex06.md#1-email-tests). The before-MX message is **unverified**.
- Header analysis: [`zoho-header-check.md`](evidence/zoho-header-check.md)
- MX, SPF, DKIM and DMARC records against Zoho's values: [`dns-after-zoho.md`](evidence/dns-after-zoho.md)
- [README › Email](../README.md#email-zoho-same-for-both-hosts)

## 7. GA4

- `page_view` and outbound `click`: [`ex06.md` §3](evidence/ex06.md#3-live-site-and-ga4)
- After the consent banner: [`ga4-after-consent.png`](evidence/ga4-after-consent.png) (commit `8da68cc`, 2026-10-15)
- Tag and Measurement ID: [`ga4-tag.md`](evidence/ga4-tag.md)
- How collection works and why the click matters: [README › Analytics](../README.md#analytics-ga4)

## 8. Failures, decisions, reflection, costs, limitations

- [Investigated failures](../README.md#investigated-failures): [`ex03.md`](evidence/ex03.md) (real), [`ex05.md`](evidence/ex05.md) (deliberate lab simulation)
- [Decisions](../README.md#decisions)
- [Reflection](../README.md#reflection)
- [Costs, credits, expiration and cleanup](../README.md#costs-credits-expiration-and-cleanup)
- [Remaining limitations](../README.md#remaining-limitations)
