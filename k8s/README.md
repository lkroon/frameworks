# Kubernetes (local cluster bootstrap)

The apps in this repo are deployed by **Argo CD** from the Helm chart in
[lkroon/charts](https://github.com/lkroon/charts) — manifests no longer live
here. This directory only bootstraps the local
[kind](https://kind.sigs.k8s.io/) cluster that Argo CD runs in.

## The GitOps loop

1. Commit and push code changes, then tag: `git tag v0.x.y && git push origin main v0.x.y`
2. GitHub Actions (`.github/workflows/release.yaml`) builds the three images
   to `ghcr.io/lkroon/frameworks-<app>:v0.x.y` and commits the new
   `imageTag` to the charts repo (needs the `CHARTS_REPO_TOKEN` secret).
3. Argo CD notices the charts commit and syncs the cluster (~3 min poll).

Nothing is built or applied from this machine. For quick local iteration
without the cluster, use `docker compose up` at the repo root.

## Bootstrap

```sh
./k8s/cluster-up.sh
```

Idempotent. Creates the kind cluster (`k8s/kind-config.yaml`: host ports
80/443 → ingress) and installs ingress-nginx, metrics-server, Argo CD, and
the `fastapi-auth` Secret from the untracked `.env` (keys `SESSION_SECRET`,
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, values unquoted), then applies
the Argo CD Application. Argo CD does the rest.

- apps: http://fastapi.localtest.me/ — http://pyramid.localtest.me/ —
  http://base.localtest.me/ — fastapi also at http://localhost/ (Google SSO)
- Argo CD UI: http://argocd.localtest.me/ (user `admin`, password printed by
  the script)

Tear down with `kind delete cluster --name frameworks` — this deletes the
Postgres volume too; the bootstrap restores the platform, not the data.

After editing `.env`, refresh the secret with:
`kubectl -n frameworks create secret generic fastapi-auth --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -`
then `kubectl -n frameworks rollout restart deploy fastapi`.

## Notes

- Argo CD has self-heal enabled: anything applied by hand to the
  `frameworks` namespace that conflicts with the chart gets reverted within
  minutes. To test unreleased code in-cluster, pause auto-sync on the
  Application in the Argo CD UI first (or just cut a pre-release tag).
- The platform demos (pod dashboard, replica slider, HPA load test) are
  documented in the chart repo; HPA scale-down starts ~1 min after load
  stops.
- The original kustomize manifests and `dev-up.sh` live in git history
  (removed when Argo CD took over).
