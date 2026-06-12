# Kubernetes deployment

Runs the frameworks stack (Postgres + fastapi/pyramid/base apps) on a local
[kind](https://kind.sigs.k8s.io/) cluster with nginx ingress.

## Quick start

```sh
./k8s/dev-up.sh
```

Creates the cluster if needed, installs ingress-nginx, builds and loads the
app images, and applies the manifests. Re-run it after code changes to
rebuild and redeploy. Then:

- http://fastapi.localtest.me/
- http://pyramid.localtest.me/
- http://base.localtest.me/

(`*.localtest.me` resolves to 127.0.0.1 via public DNS; ingress is mapped to
host ports 80/443 in `kind-config.yaml`.)

Tear down with `kind delete cluster --name frameworks`.

## Layout

```
k8s/
├── kind-config.yaml     # cluster definition (ingress-ready node, port 80/443 mappings)
├── dev-up.sh            # idempotent bootstrap/redeploy script
├── base/                # kustomize base: namespace, postgres, apps, ingress
│   └── schema.sql       # copy of ../database/schema.sql (kustomize can't leave its root)
└── overlays/
    └── local/           # what dev-up.sh applies; prod overlay slots in beside it
```

Notes:

- App images use bare names (`frameworks-fastapi:dev`) loaded into kind with
  `kind load docker-image`. A prod overlay would remap them to
  `ghcr.io/<owner>/frameworks-<app>:<tag>` via the kustomize `images:`
  transformer — that is the Argo CD integration point.
- `db-credentials` contains dev-only plaintext values. For a real
  deployment, replace with sealed-secrets or SOPS.
- The `fastapi-auth` Secret is not in the manifests: `dev-up.sh` creates it
  from the gitignored `.env` at the repo root (keys: `SESSION_SECRET`,
  `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`). To apply `.env` changes
  without a full dev-up run:
  `kubectl -n frameworks create secret generic fastapi-auth --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -`
  followed by `kubectl -n frameworks rollout restart deploy fastapi`.
- "Sign in with Google" uses an OAuth client (web application) from Google
  Cloud Console with redirect URI `http://localhost/auth/google/callback`.
  The SSO flow always runs on http://localhost/ (Google only allows
  plain-http redirects on localhost), which is why the ingress also routes
  that host to fastapi and the SSO button links there absolutely via
  `GOOGLE_AUTH_ORIGIN`.
- If you edit `database/schema.sql`, copy it to `k8s/base/schema.sql` too.
  The init script only runs on a fresh data volume; an existing database
  needs a migration (or delete the `pgdata` PVC to start over).
