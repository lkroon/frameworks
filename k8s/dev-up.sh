#!/usr/bin/env bash
# Create (or update) the local kind cluster and deploy the frameworks stack.
# Idempotent: safe to re-run after code changes to rebuild + redeploy.
set -euo pipefail

cd "$(dirname "$0")/.."

CLUSTER=frameworks
INGRESS_NGINX_MANIFEST=https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

if ! kind get clusters 2>/dev/null | grep -qx "$CLUSTER"; then
  kind create cluster --config k8s/kind-config.yaml
fi

kubectl --context "kind-$CLUSTER" get deploy -n ingress-nginx ingress-nginx-controller >/dev/null 2>&1 || {
  kubectl --context "kind-$CLUSTER" apply -f "$INGRESS_NGINX_MANIFEST"
}
kubectl --context "kind-$CLUSTER" wait -n ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s

# metrics-server feeds the HPA; kind kubelets use self-signed certs
kubectl --context "kind-$CLUSTER" get deploy -n kube-system metrics-server >/dev/null 2>&1 || {
  kubectl --context "kind-$CLUSTER" apply -f \
    https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
  kubectl --context "kind-$CLUSTER" -n kube-system patch deploy metrics-server --type=json \
    -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
}

for app in fastapi pyramid base; do
  docker build -t "frameworks-$app:dev" "./$app"
done
# `kind load docker-image` breaks with snap-installed docker (private /tmp),
# so save via stdout (the shell writes the file) and load the archive.
images_tar=$(mktemp ./images-XXXXXX.tar)
trap 'rm -f "$images_tar"' EXIT
docker save frameworks-fastapi:dev frameworks-pyramid:dev frameworks-base:dev > "$images_tar"
kind load image-archive --name "$CLUSTER" "$images_tar"

kubectl --context "kind-$CLUSTER" apply -k k8s/overlays/local

# fastapi-auth is built from the untracked .env so real credentials never
# enter git. Keys must match the env vars the app reads.
if [[ ! -f .env ]]; then
  echo "ERROR: .env not found at repo root. Create it with SESSION_SECRET," >&2
  echo "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET (google values may be empty)." >&2
  exit 1
fi
kubectl --context "kind-$CLUSTER" -n frameworks create secret generic fastapi-auth \
  --from-env-file=.env --dry-run=client -o yaml \
  | kubectl --context "kind-$CLUSTER" apply -f -

kubectl --context "kind-$CLUSTER" -n frameworks rollout restart deploy fastapi pyramid base
kubectl --context "kind-$CLUSTER" -n frameworks rollout status statefulset/postgres --timeout=180s
for app in fastapi pyramid base; do
  kubectl --context "kind-$CLUSTER" -n frameworks rollout status "deploy/$app" --timeout=120s
done

echo
echo "Stack is up:"
echo "  http://fastapi.localtest.me/"
echo "  http://pyramid.localtest.me/"
echo "  http://base.localtest.me/"
