DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Pod Dashboard</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
  fieldset { margin-bottom: 1rem; }
  button { margin: 0.25rem 0; padding: 0.3rem 0.8rem; }
  pre { background: #f4f4f4; padding: 1rem; }
  code { background: #f4f4f4; padding: 0.1rem 0.3rem; }
  .topbar { display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid #ddd; padding-bottom: 0.5rem; }
  .topbar form { margin: 0; }
  .bar { background: #4a90d9; color: #fff; padding: 2px 8px; margin: 2px 0;
         white-space: nowrap; font-size: 0.85rem; }
  .hint { color: #666; font-size: 0.9rem; }
</style>
</head>
<body>
<div class="topbar">
  <span>Signed in as <strong>__ACCOUNT_NAME__</strong></span>
  <form method="post" action="/logout"><button type="submit">Log out</button></form>
</div>
<h1>Pod Dashboard</h1>

<fieldset>
  <legend>This response served by</legend>
  <pre id="me">loading…</pre>
  <button onclick="loadMe()">Refresh</button>
</fieldset>

<fieldset>
  <legend>Replicas</legend>
  <input type="range" id="replicaSlider" min="1" max="5" step="1" value="1"
         oninput="document.getElementById('replicaVal').textContent = this.value"
         onchange="setReplicas(this.value)">
  <strong id="replicaVal">?</strong>
  <span id="scaleStatus" class="hint"></span>
  <p class="hint">Patches the deployment's scale subresource through the
  Kubernetes API (pod ServiceAccount, RBAC-scoped to exactly this). Note the
  HPA also manages this deployment &mdash; when idle it pulls the count back
  to its own target within a minute or two.</p>
</fieldset>

<fieldset>
  <legend>Load balancing</legend>
  <p class="hint">Each request may land on a different pod. Raise the
  replica count above and try again.</p>
  <button onclick="ping(30)">Send 30 requests</button>
  <div id="pingTally"></div>
</fieldset>

<fieldset>
  <legend>CPU load (autoscaler demo)</legend>
  <p class="hint">Runs 6 parallel loops against <code>/work</code>, each request burning
  300&nbsp;ms of CPU. Watch the HPA react:
  <code>kubectl -n frameworks get hpa,pods -w</code></p>
  <button id="loadBtn" onclick="toggleLoad()">Start load</button>
  <span id="loadStats"></span>
  <div id="loadTally"></div>
</fieldset>

<script>
async function whoami() {
  const r = await fetch('/whoami', {cache: 'no-store'});
  return r.json();
}

async function loadMe() {
  document.getElementById('me').textContent = JSON.stringify(await whoami(), null, 2);
}

function renderTally(el, counts) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
  el.innerHTML = Object.entries(counts).sort()
    .map(([pod, n]) =>
      `<div class="bar" style="width:${Math.round(300 * n / total) + 80}px">${pod}: ${n}</div>`)
    .join('');
}

async function ping(n) {
  const counts = {};
  for (let i = 0; i < n; i++) {
    const j = await whoami();
    counts[j.pod] = (counts[j.pod] || 0) + 1;
    renderTally(document.getElementById('pingTally'), counts);
  }
}

let running = false, done = 0;
const loadCounts = {};

async function workLoop() {
  while (running) {
    try {
      const r = await fetch('/work?ms=300', {cache: 'no-store'});
      const j = await r.json();
      loadCounts[j.pod] = (loadCounts[j.pod] || 0) + 1;
      done++;
      document.getElementById('loadStats').textContent = ` ${done} requests completed`;
      renderTally(document.getElementById('loadTally'), loadCounts);
    } catch (e) { /* pod may be cycling during scale events; keep going */ }
  }
}

function toggleLoad() {
  running = !running;
  document.getElementById('loadBtn').textContent = running ? 'Stop load' : 'Start load';
  if (running) for (let i = 0; i < 6; i++) workLoop();
}

async function refreshScale() {
  try {
    const r = await fetch('/scale', {cache: 'no-store'});
    if (!r.ok) return;
    const s = await r.json();
    document.getElementById('scaleStatus').textContent =
      ` desired: ${s.desired}, running: ${s.running}`;
    const slider = document.getElementById('replicaSlider');
    // Keep the slider honest (HPA may change replicas) unless being dragged
    if (document.activeElement !== slider) {
      slider.value = s.desired;
      document.getElementById('replicaVal').textContent = s.desired;
    }
  } catch (e) { /* transient during pod cycling */ }
}

async function setReplicas(n) {
  await fetch('/scale', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({replicas: Number(n)})
  });
  refreshScale();
}

loadMe();
refreshScale();
setInterval(refreshScale, 3000);
</script>
</body>
</html>
"""

_AUTH_STYLE = """
<style>
  body { font-family: system-ui, sans-serif; max-width: 360px; margin: 4rem auto; padding: 0 1rem; }
  label { display: block; margin-top: 0.75rem; }
  input { width: 100%; padding: 0.4rem; box-sizing: border-box; }
  button { margin-top: 1rem; padding: 0.4rem 1rem; }
  .error { color: #b00020; background: #fde7e9; padding: 0.5rem; }
  .google { display: inline-block; margin-top: 1rem; padding: 0.4rem 1rem;
            border: 1px solid #ccc; text-decoration: none; color: inherit; }
  hr { margin: 1.5rem 0; border: 0; border-top: 1px solid #ddd; }
</style>
"""

GOOGLE_BUTTON_HTML = """<hr>
<a class="google" href="__GOOGLE_AUTH_URL__">Sign in with Google</a>"""

LOGIN_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Sign in</title>
{_AUTH_STYLE}
</head>
<body>
<h1>Sign in</h1>
__ERROR__
<form method="post" action="/login">
  <label for="email">Email</label>
  <input id="email" name="email" type="email" required>
  <label for="password">Password</label>
  <input id="password" name="password" type="password" required>
  <button type="submit">Sign in</button>
</form>
__GOOGLE__
<p>No account? <a href="/register">Register</a></p>
</body>
</html>
"""

REGISTER_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Register</title>
{_AUTH_STYLE}
</head>
<body>
<h1>Register</h1>
__ERROR__
<form method="post" action="/register">
  <label for="display_name">Name</label>
  <input id="display_name" name="display_name">
  <label for="email">Email</label>
  <input id="email" name="email" type="email" required>
  <label for="password">Password</label>
  <input id="password" name="password" type="password" required>
  <button type="submit">Create account</button>
</form>
__GOOGLE__
<p>Already have an account? <a href="/login">Sign in</a></p>
</body>
</html>
"""
