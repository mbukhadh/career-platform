# How this site is secured

my data sent to your site is encrypted?

## Certificate evidence

```
subject=CN = mjbukhadhour.com
issuer=C = US, O = Let's Encrypt, CN = YE1
notBefore=Oct  6 21:08:23 2026 GMT
notAfter=Jan  4 21:08:22 2027 GMT
```

## Certificate

The certificate comes from Let’s Encrypt and covers mjbukhadhour.com and www.mjbukhadhour.com. It expires January 4, 2027, which is 88 days out as of October 8, 2026.

Renewal is automatic. The dry run succeeded, and certbot.timer is set to run next on October 9 at 02:25 UTC. Certbot checks twice a day and only renews once the cert is within 30 days of expiring.

## Open ports

Only three ports are open to the internet. Port 22 allows SSH admin access, and only from one IP address: the public IP of my laptop's network. If that IP changes, SSH stops working until the rule is updated. Port 80 is open to anyone, but only so HTTP requests can be redirected to HTTPS. Port 443 is open to anyone and serves the encrypted site. Everything else is denied by default, including port 8000, where the app itself listens.

## Where encryption starts and ends

Traffic is encrypted from the visitor's browser to Nginx on port 443. Nginx then passes each request to the app over `127.0.0.1:8000`, inside the VM. That last hop is not encrypted, but it never leaves the machine, and port 8000 is not reachable from outside.

## Checking in Chrome

Click the icon to the left of the address bar, then **Connection is secure**, then **Certificate is valid**. The issuer, name and expiry shown there match the `openssl` output above.