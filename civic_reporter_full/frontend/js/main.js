/* GroundTruth -- shared page behaviour */

function requireAuthOrRedirect() {
  if (!auth.isLoggedIn()) window.location.href = "login.html";
}

function showMsg(el, text, type = "err") {
  el.textContent = text;
  el.className = `form-msg show ${type}`;
}

/* ---------- login page ---------- */
function initLoginPage() {
  const form = document.getElementById("login-form");
  if (!form) return;
  const msg = document.getElementById("login-msg");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = form.email.value.trim();
    const password = form.password.value;
    const submitBtn = form.querySelector("button[type=submit]");

    submitBtn.disabled = true;
    submitBtn.textContent = "Signing in…";
    try {
      const data = await Api.login({ email, password });
      auth.setTokens(data.access, data.refresh);
      window.location.href = "dashboard.html";
    } catch (err) {
      showMsg(msg, err.message || "Couldn't sign in. Check your details and try again.");
      submitBtn.disabled = false;
      submitBtn.textContent = "Sign in";
    }
  });
}

/* ---------- register page ---------- */
function initRegisterPage() {
  const form = document.getElementById("register-form");
  if (!form) return;
  const msg = document.getElementById("register-msg");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      name: form.name.value.trim(),
      email: form.email.value.trim(),
      phone: form.phone.value.trim(),
      password: form.password.value,
    };
    const submitBtn = form.querySelector("button[type=submit]");

    submitBtn.disabled = true;
    submitBtn.textContent = "Creating account…";
    try {
      const data = await Api.register(payload);
      auth.setTokens(data.access, data.refresh);
      window.location.href = "dashboard.html";
    } catch (err) {
      showMsg(msg, err.message || "Couldn't create that account. Check the details and try again.");
      submitBtn.disabled = false;
      submitBtn.textContent = "Create account";
    }
  });
}

/* ---------- dashboard page ---------- */
function initDashboardPage() {
  const root = document.getElementById("dash-root");
  if (!root) return;
  requireAuthOrRedirect();
  const nameEl = document.getElementById("dash-name");
  const badgeEl = document.getElementById("dash-badge");
  const areasEl = document.getElementById("dash-areas");
  const categoriesEl = document.getElementById("dash-categories");
  const reportsEl = document.getElementById("dash-reports");
  const communityEl = document.getElementById("community-reports");
  const form = document.getElementById("report-form");
  const reportMsg = document.getElementById("report-msg");

  document.getElementById("logout-btn").addEventListener("click", () => {
    auth.clear(); window.location.href = "index.html";
  });

  Api.me().then((user) => {
    nameEl.textContent = user.name || user.email;
    if (user.is_authority) { badgeEl.textContent = "Authority"; badgeEl.style.display = "inline-flex"; }
  }).catch(() => { auth.clear(); window.location.href = "login.html"; });

  Promise.all([Api.areas(), Api.categories()]).then(([areas, categories]) => {
    renderList(areasEl, areas, (a) => a.name);
    renderList(categoriesEl, categories, (c) => c.name);
    fillSelect(form.elements.area, areas, "Choose an area");
    fillSelect(form.elements.category, categories, "Choose a category");
  }).catch(() => {
    renderEmpty(areasEl, "Couldn't load areas. Ask an administrator to add areas.");
    renderEmpty(categoriesEl, "Couldn't load categories. Ask an administrator to add categories.");
  });

  async function loadCommunityReports() {
    try {
      const reports = await Api.reports();
      const community = reports.filter(r => r.reporter !== undefined && String(r.reporter) !== "");
      if (!community.length) { renderEmpty(communityEl, "No community reports yet."); return; }
      communityEl.innerHTML = community.map(r => `
        <article class="report-item">
          <div class="report-item-head"><strong>${escapeHtml(r.title)}</strong><span class="badge">${escapeHtml((r.status || "submitted").replaceAll("_", " "))}</span></div>
          <p>${escapeHtml(r.description)}</p><small>Reported by ${escapeHtml(r.reporter_name || "Resident")} · ${escapeHtml(r.area_name)} · ${escapeHtml(r.category_name)} · ${escapeHtml(r.location)}</small>
          ${r.photo ? `<p><a href="${escapeHtml(r.photo)}" target="_blank" rel="noopener">View photo</a></p>` : ""}
          <p class="report-meta"><button class="btn btn-ghost btn-sm community-upvote" data-report-id="${r.id}" type="button">▲ ${Number(r.upvote_count || 0)} upvotes</button> · ${(r.comments || []).length} comments</p>
          <div class="comment-list">${(r.comments || []).map(c => `<p><strong>${escapeHtml(c.author_name || "Resident")}:</strong> ${escapeHtml(c.body)}</p>`).join("")}</div>
          <form class="community-comment-form comment-form" data-report-id="${r.id}"><input name="body" maxlength="1500" required placeholder="Add a comment" aria-label="Comment on community report"/><button class="btn btn-ghost btn-sm" type="submit">Comment</button></form>
        </article>`).join("");
      communityEl.querySelectorAll(".community-upvote").forEach(button => button.addEventListener("click", async () => {
        try { await Api.upvote(button.dataset.reportId); await loadCommunityReports(); await loadReports(); }
        catch (err) { alert(err.message || "Could not update upvote."); }
      }));
      communityEl.querySelectorAll(".community-comment-form").forEach(commentForm => commentForm.addEventListener("submit", async event => {
        event.preventDefault();
        try { await Api.comment(commentForm.dataset.reportId, {body: commentForm.elements.body.value.trim()}); await loadCommunityReports(); await loadReports(); }
        catch (err) { alert(err.message || "Could not post comment."); }
      }));
    } catch (err) { renderEmpty(communityEl, "Couldn't load community reports right now."); }
  }

  async function loadReports() {
    try {
      const reports = await Api.mine();
      if (!reports.length) { renderEmpty(reportsEl, "You haven't filed a report yet."); return; }
      reportsEl.innerHTML = reports.map((r) => `
        <article class="list-item report-item">
          <div class="report-item-head"><strong>${escapeHtml(r.title)}</strong><span class="badge">${escapeHtml((r.status || "submitted").replaceAll("_", " "))}</span></div>
          <p>${escapeHtml(r.description)}</p>
          <small>${escapeHtml(r.area_name)} · ${escapeHtml(r.category_name)} · ${escapeHtml(r.location)} · ${new Date(r.created_at).toLocaleDateString()}</small>
          ${r.photo ? `<p><a href="${escapeHtml(r.photo)}" target="_blank" rel="noopener">View attached photo</a></p>` : ""}
          ${r.resolution_photo ? `<p><a href="${escapeHtml(r.resolution_photo)}" target="_blank" rel="noopener">View resolution evidence</a></p>` : ""}
          <p class="report-meta"><button class="btn btn-ghost btn-sm upvote-btn" type="button" data-report-id="${r.id}">▲ ${Number(r.upvote_count || 0)} upvotes</button> · ${(r.comments || []).length} comments</p>
          <div class="comment-list">${(r.comments || []).map(c => `<p><strong>${escapeHtml(c.author_name || "User")}:</strong> ${escapeHtml(c.body)}</p>`).join("")}</div>
          <form class="comment-form" data-report-id="${r.id}"><input name="body" maxlength="1500" required placeholder="Add a useful comment" aria-label="Comment"/><button class="btn btn-ghost btn-sm" type="submit">Comment</button></form>
          ${r.status_history && r.status_history.length ? `<details><summary>Status history</summary>${r.status_history.map(h => `<p><small>${escapeHtml(h.new_status.replaceAll("_", " "))} · ${new Date(h.created_at).toLocaleString()} ${h.note ? "— " + escapeHtml(h.note) : ""}</small></p>`).join("")}</details>` : ""}
        </article>`).join("");
      reportsEl.querySelectorAll(".upvote-btn").forEach((button) => button.addEventListener("click", async () => {
        try { await Api.upvote(button.dataset.reportId); await loadReports(); }
        catch (err) { alert(err.message || "Could not update upvote."); }
      }));
      reportsEl.querySelectorAll(".comment-form").forEach((commentForm) => commentForm.addEventListener("submit", async (event) => {
        event.preventDefault(); const id = commentForm.dataset.reportId; const input = commentForm.elements.body;
        try { await Api.comment(id, { body: input.value.trim() }); await loadReports(); }
        catch (err) { alert(err.message || "Couldn't post comment."); }
      }));
    } catch (err) { renderEmpty(reportsEl, "Couldn't load reports. Please refresh or sign in again."); }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector("button[type=submit]");
    const file = form.elements.photo.files[0];
    if (file && (!/^image\/(jpeg|png|webp)$/.test(file.type) || file.size > 5 * 1024 * 1024)) {
      showMsg(reportMsg, "Choose a JPG, PNG, or WebP image no larger than 5 MB."); return;
    }
    const payload = new FormData();
    ["title", "description", "area", "category", "location"].forEach((key) => payload.append(key, form.elements[key].value.trim()));
    if (file) payload.append("photo", file);
    submit.disabled = true; submit.textContent = "Submitting…";
    try {
      await Api.createReport(payload); form.reset();
      showMsg(reportMsg, "Your report was submitted successfully.", "ok"); await loadReports();
    } catch (err) { showMsg(reportMsg, err.message || "Couldn't submit the report. Check your fields and try again."); }
    finally { submit.disabled = false; submit.textContent = "Submit report"; }
  });
  loadReports();
  loadCommunityReports();
}

function fillSelect(select, items, placeholder) {
  select.replaceChildren(new Option(placeholder, ""));
  items.forEach(item => select.add(new Option(item.name, item.id)));
}

function renderList(el, items, labelFn) {
  if (!items || !items.length) return renderEmpty(el, "None added yet.");
  el.innerHTML = items
    .map((item) => `<div class="list-item"><span>${escapeHtml(labelFn(item))}</span></div>`)
    .join("");
}

function renderEmpty(el, text) {
  el.innerHTML = `<div class="empty-note">${escapeHtml(text)}</div>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

document.addEventListener("DOMContentLoaded", () => {
  initLoginPage();
  initRegisterPage();
  initDashboardPage();
});
