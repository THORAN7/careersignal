const $ = (id) => document.getElementById(id);
let state;
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c]));

function applyTheme(theme) {
  const isDark = theme === "dark";
  document.documentElement.dataset.theme = isDark ? "dark" : "light";
  const toggle = $("themeToggle");
  toggle.setAttribute("aria-pressed", String(isDark));
  toggle.setAttribute("aria-label", isDark ? "Switch to light theme" : "Switch to dark theme");
  toggle.querySelector(".theme-icon").textContent = isDark ? "☀" : "☾";
}

applyTheme(localStorage.getItem("careersignal-theme") === "dark" ? "dark" : "light");
$("themeToggle").addEventListener("click", () => {
  const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  localStorage.setItem("careersignal-theme", nextTheme);
  applyTheme(nextTheme);
});

async function api(path, options) {
  const result = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const data = await result.json();
  if (!result.ok) throw new Error(data.error || data.detail || "Request failed.");
  return data;
}
function render(data) {
  state = data;
  const { profile, report } = data;
  const displayName = profile.name || "Your profile";
  $("name").textContent = displayName; $("meta").textContent = profile.degree ? `${profile.degree} · ${profile.year} · ${profile.school}` : "Add your details or upload evidence to begin";
  $("avatar").textContent = profile.name ? profile.name.split(/\s+/).map((part) => part[0]).slice(0, 2).join("").toUpperCase() : "?";
  $("chips").innerHTML = report.strengths.map((item) => `<span>${escapeHtml(item)}</span>`).join("");
  $("score").textContent = report.score ? `${report.score}/100` : "—"; $("headline").textContent = report.score ? report.headline : "Your career signal starts here."; $("summary").textContent = report.professional_summary;
  $("strengths").innerHTML = report.strengths.map((item) => `<span>✦ ${escapeHtml(item)}</span>`).join("");
  $("gaps").innerHTML = report.skill_gap_report.map((item) => `<article class="gap panel"><div><span class="priority">${escapeHtml(item.priority)}</span><h3>${escapeHtml(item.skill)}</h3></div><p>${escapeHtml(item.why)}</p><small>Next action: ${escapeHtml(item.action)}</small></article>`).join("");
  $("learning").innerHTML = report.learning_recommendations.map((item, index) => `<button class="learning-step ${item.completed ? "done" : ""}" data-index="${index}"><b>${item.completed ? "✓" : item.week}</b><span><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.detail)}</small><em>${escapeHtml(item.outcome)}</em></span><i>→</i></button>`).join("");
  $("pitch").textContent = `“${report.interview_preparation.pitch}”`;
  $("questions").innerHTML = report.interview_preparation.questions.map((question, index) => `<div class="question"><b>0${index + 1}</b><span>${escapeHtml(question)}</span></div>`).join("");
  renderFiles(report.evidence_files || []);
  renderAnalysis(report.resume_analysis);
  document.querySelectorAll(".learning-step").forEach((button) => button.addEventListener("click", async () => render(await api("/api/learning/toggle", { method: "POST", body: JSON.stringify({ index: Number(button.dataset.index) }) }))));
}
function renderAnalysis(analysis) {
  const panel = $("analysisPanel");
  if (!analysis) { panel.innerHTML = `<p class="eyebrow">EXTRACTION ENGINE</p><h2>Upload a resume to unlock evidence analysis.</h2><p>CareerSignal will extract selectable text, detect skills and sections, then use those signals to improve your profile.</p>`; return; }
  const statusClass = analysis.status === "extracted" ? "analysis-good" : "analysis-warn";
  const contact = analysis.contact || {};
  panel.innerHTML = `<div class="analysis-heading"><div><p class="eyebrow">EXTRACTION ENGINE</p><h2>Resume intelligence</h2></div><strong class="${statusClass}">${analysis.completeness_score}% complete</strong></div><p>${escapeHtml(analysis.message || "Evidence analysis completed.")}</p><div class="analysis-progress"><span style="width:${analysis.completeness_score}%"></span></div><div class="analysis-grid"><div><small>DETECTED SKILLS</small><strong>${analysis.detected_skills.length ? analysis.detected_skills.map(escapeHtml).join(" · ") : "None detected"}</strong></div><div><small>SECTIONS FOUND</small><strong>${analysis.sections.length ? analysis.sections.map(escapeHtml).join(" · ") : "None detected"}</strong></div><div><small>CONTACT SIGNAL</small><strong>${escapeHtml(contact.email || contact.phone || "No contact detected")}</strong></div><div><small>TEXT SIGNAL</small><strong>${analysis.word_count || 0} words · ${analysis.status === "extracted" ? "evaluated" : "needs text"}</strong></div></div>${analysis.text_preview ? `<details><summary>View extracted text preview</summary><p class="preview">${escapeHtml(analysis.text_preview)}</p></details>` : ""}`;
}
function renderFiles(files) {
  $("fileList").innerHTML = files.length ? files.map((file) => `<div class="file-item"><span class="file-icon">↗</span><span><strong>${escapeHtml(file.name)}</strong><small>${(file.size / 1024).toFixed(1)} KB</small></span><button data-delete-file="${escapeHtml(file.name)}" aria-label="Remove file">×</button></div>`).join("") : `<p class="empty-files">No evidence uploaded yet.</p>`;
  document.querySelectorAll("[data-delete-file]").forEach((button) => button.addEventListener("click", async () => render(await api("/api/uploads/delete", { method: "POST", body: JSON.stringify({ name: button.dataset.deleteFile }) }))));
}
function openEditor() {
  const form = $("profileForm");
  Object.entries(state.profile).forEach(([key, value]) => { if (form.elements[key]) form.elements[key].value = Array.isArray(value) ? value.join(", ") : value; });
  $("backdrop").classList.add("open");
}
$("editButton").addEventListener("click", openEditor); $("close").addEventListener("click", () => $("backdrop").classList.remove("open"));
$("backdrop").addEventListener("click", (event) => { if (event.target === $("backdrop")) $("backdrop").classList.remove("open"); });
$("profileForm").addEventListener("submit", async (event) => { event.preventDefault(); const button = event.target.querySelector("button"); button.disabled = true; button.textContent = "Generating..."; try { render(await api("/api/profile", { method: "POST", body: JSON.stringify(Object.fromEntries(new FormData(event.target))) })); $("backdrop").classList.remove("open"); $("saveState").textContent = "Profile generated just now"; } finally { button.disabled = false; button.innerHTML = "Generate my profile <span>→</span>"; } });
$("downloadButton").addEventListener("click", () => { const report = { ...state, generated_for: state.profile.name }; const link = document.createElement("a"); link.href = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: "application/json" })); link.download = `${state.profile.name.replace(/\s+/g, "-").toLowerCase()}-career-profile.json`; link.click(); URL.revokeObjectURL(link.href); });
document.getElementById("fileInput").addEventListener("change", async (event) => {
  for (const file of event.target.files) {
    if (file.size > 6 * 1024 * 1024) { alert(`${file.name} is larger than 6 MB.`); continue; }
    $("saveState").textContent = `Analyzing ${file.name}…`;
    $("analysisPanel").classList.add("is-processing");
    const encoded = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result).split(",")[1]); reader.onerror = reject; reader.readAsDataURL(file); });
    try { render(await api("/api/uploads", { method: "POST", body: JSON.stringify({ name: file.name, content: encoded }) })); $("saveState").textContent = "Evidence evaluated just now"; } catch (error) { alert(error.message); $("saveState").textContent = "Analysis failed"; } finally { $("analysisPanel").classList.remove("is-processing"); }
  }
  event.target.value = "";
});
api("/api/profile").then(render).catch((error) => { $("headline").textContent = error.message; });
api("/api/profile").then((data) => {
  if (!data.profile.name && !data.profile.uploads.length) openEditor();
});
