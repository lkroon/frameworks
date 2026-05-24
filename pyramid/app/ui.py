INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Users Admin</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; }
  fieldset { margin-bottom: 1rem; }
  label { display: inline-block; min-width: 4rem; }
  input, select, button { margin: 0.25rem 0; padding: 0.3rem; }
  #output { background: #f4f4f4; padding: 1rem; white-space: pre-wrap; word-break: break-word; }
  .row { margin: 0.25rem 0; }
</style>
</head>
<body>
<h1>Users Admin</h1>

<fieldset>
  <legend>All users</legend>
  <button onclick="location.href='/users'">View all users (raw JSON)</button>
  <button onclick="loadUsers()">Refresh dropdown</button>
</fieldset>

<fieldset>
  <legend>Create user</legend>
  <div class="row"><label for="c_name">Name</label><input id="c_name"></div>
  <div class="row"><label for="c_email">Email</label><input id="c_email"></div>
  <button onclick="createUser()">Create</button>
</fieldset>

<fieldset>
  <legend>Select a user</legend>
  <select id="userSelect"></select>
  <div class="row">
    <button onclick="viewUser()">View (A)</button>
    <button onclick="showUpdate()">Update (B)</button>
    <button onclick="deleteUser()">Delete (C)</button>
  </div>
</fieldset>

<fieldset id="updateBox" style="display:none">
  <legend>Update user <span id="u_id"></span></legend>
  <div class="row"><label for="u_name">Name</label><input id="u_name"></div>
  <div class="row"><label for="u_email">Email</label><input id="u_email"></div>
  <button onclick="submitUpdate()">Save</button>
  <button onclick="document.getElementById('updateBox').style.display='none'">Cancel</button>
</fieldset>

<h3>Output</h3>
<pre id="output">Ready.</pre>

<script>
const out = document.getElementById('output');
const sel = document.getElementById('userSelect');

function show(data, status) {
  out.textContent = (status ? `[${status}] ` : '') +
    (typeof data === 'string' ? data : JSON.stringify(data, null, 2));
}

async function loadUsers() {
  const r = await fetch('/users');
  const users = await r.json();
  sel.innerHTML = '';
  if (users.length === 0) {
    const o = document.createElement('option');
    o.value = ''; o.textContent = '(no users)';
    sel.appendChild(o);
  }
  for (const u of users) {
    const o = document.createElement('option');
    o.value = u.id;
    o.textContent = `${u.id} - ${u.name} (${u.email})`;
    sel.appendChild(o);
  }
  show(users, r.status);
}

async function createUser() {
  const name = document.getElementById('c_name').value;
  const email = document.getElementById('c_email').value;
  const r = await fetch('/users', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name, email})
  });
  show(await r.json(), r.status);
  document.getElementById('c_name').value = '';
  document.getElementById('c_email').value = '';
  loadUsers();
}

async function viewUser() {
  if (!sel.value) return show('No user selected.');
  const r = await fetch('/users/' + sel.value);
  show(await r.json(), r.status);
}

async function showUpdate() {
  if (!sel.value) return show('No user selected.');
  const r = await fetch('/users/' + sel.value);
  const u = await r.json();
  document.getElementById('u_id').textContent = u.id;
  document.getElementById('u_name').value = u.name;
  document.getElementById('u_email').value = u.email;
  document.getElementById('updateBox').dataset.id = u.id;
  document.getElementById('updateBox').style.display = 'block';
}

async function submitUpdate() {
  const id = document.getElementById('updateBox').dataset.id;
  const name = document.getElementById('u_name').value;
  const email = document.getElementById('u_email').value;
  const r = await fetch('/users/' + id, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name, email})
  });
  show(await r.json(), r.status);
  document.getElementById('updateBox').style.display = 'none';
  loadUsers();
}

async function deleteUser() {
  if (!sel.value) return show('No user selected.');
  const id = sel.value;
  const r = await fetch('/users/' + id, {method: 'DELETE'});
  show(r.status === 204 ? `Deleted user ${id}` : `Status ${r.status}`, r.status);
  loadUsers();
}

loadUsers();
</script>
</body>
</html>
"""
