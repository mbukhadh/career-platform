# Request path: mjbukhadhour.com

Study diagram for the midterm whiteboard interview. Items marked "check" or
"unknown" aren't in the repo; confirm them on your own network.

Assumptions: new HTTPS connection over TCP, no cached DNS answer, http
redirected to https.

## Railway: full request path

![Railway request path](images/request-path-railway.png)

Mermaid source:

```mermaid
flowchart LR
  subgraph HOME["Home network: private side"]
    L["Laptop browser<br/>Wi-Fi network interface<br/>private IP, subnet, gateway, DNS server<br/>all supplied by DHCP, check ipconfig"]
    R["Home router box<br/>roles: access point + switch + router<br/>+ DHCP + NAT + stateful firewall<br/>unknown: confirm which roles yours combines"]
    M["Modem or ONT<br/>unknown: separate box or built in?"]
  end

  ISP["ISP<br/>assigns the router its public IP"]
  NET(("Internet routers"))

  subgraph DNS["DNS: separate exchange"]
    RES["DNS resolver<br/>check: ISP or 8.8.8.8?"]
    AUTH["Cloudflare nameservers<br/>graham + piper<br/>root CNAME flattened to A 69.46.46.119"]
  end

  subgraph RW["Railway"]
    EDGE["Railway edge<br/>TLS ENDS HERE<br/>Let's Encrypt cert CN=mjbukhadhour.com"]
    APP["Uvicorn app<br/>0.0.0.0:$PORT<br/>--proxy-headers trusts X-Forwarded-Proto"]
    PG[("PostgreSQL<br/>reached via DATABASE_URL")]
  end

  L -- "Wi-Fi link" --- R
  R -- "NAT: private source IP rewritten to public IP" --- M
  M --- ISP --- NET

  L -. "1 DNS query, UDP 53<br/>client: laptop, server: resolver<br/>crosses the same hardware" .-> RES
  RES -. "recursive lookup" .-> AUTH
  RES -. "answer: 69.46.46.119" .-> L

  NET == "2 TCP connect to port 443<br/>3 TLS handshake: check name, dates, chain<br/>4 HTTPS GET /<br/>client: browser, server: Railway edge" ==> EDGE
  EDGE -- "5 plain HTTP on Railway's private network<br/>client: edge, server: app" --> APP
  APP -- "6 SQL query over private network<br/>client: app, server: Postgres" --> PG
  EDGE -. "7 response HTML returns the same path<br/>8 browser requests CSS, JS, GA4 tag separately" .-> L
```

## Azure: what replaces the Railway box

![Azure host side](images/request-path-azure.png)

Mermaid source:

```mermaid
flowchart LR
  NET(("Internet routers"))
  AUTHA["Cloudflare DNS<br/>A record: 135.232.198.204<br/>DNS only, not proxied"]

  subgraph AZ["Azure VM: vm-career-platform, Ubuntu 24.04"]
    NSG["NSG: vm-career-platform-nsg<br/>allow 80 + 443 from Any<br/>allow 22 from laptop /32 only<br/>deny everything else, including 8000"]
    NGX["Nginx on 443<br/>TLS ENDS HERE<br/>certbot Let's Encrypt, auto-renew<br/>port 80 redirects to https"]
    UV["Uvicorn, 2 workers<br/>127.0.0.1:8000<br/>run and restarted by systemd"]
    DB[("SQLite file<br/>career_platform.db<br/>file read, no network hop")]
  end

  AUTHA -. "DNS answer to laptop" .-> NET
  NET == "TCP 443, TLS, HTTPS<br/>client: browser, server: Nginx" ==> NSG
  NSG --> NGX
  NGX -- "plain HTTP over loopback<br/>client: Nginx, server: Uvicorn" --> UV
  UV -- "file access" --> DB
```

## What changes between the two hosts

| | Azure | Railway |
| --- | --- | --- |
| DNS answer | A record to the VM, `135.232.198.204` | CNAME, flattened to `69.46.46.119` |
| Firewall | Your NSG rules | Railway's edge; you don't own it |
| Where TLS ends | Nginx on your VM | Railway's edge |
| Certificate | certbot on the VM (you renew it) | Railway (they renew it) |
| App listens on | `127.0.0.1:8000` | `0.0.0.0:$PORT` |
| Database | SQLite file on the same disk | PostgreSQL as a separate service |
| Who fixes it at 2 AM | You: OS, Nginx, certificate, app, database | Railway: servers, proxy, certificate. You: app and data |

## Say out loud while drawing

- The DNS lookup physically travels over the same Wi-Fi, router and ISP as
  the web request. It's drawn as a dotted side loop only to show it's a
  separate exchange.
- The host's logs show the router's public IP as the client, not the laptop's
  private IP, because of NAT.
