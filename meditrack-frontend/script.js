// ---- Backend connection --------------------------------------------------
// Change this if your Flask API runs somewhere else.
const API_BASE = "http://localhost:5000/api";

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || "Request failed");
  }
  return res.status === 204 ? null : res.json();
}

// In-memory copies of what's in the database (filled by loadAllData()).
let medicines = [];
let reminders = [];
let usageLog = [];
let profile = { name: "Admin", age: "", location: "" };

async function loadAllData() {
  const [med, rem, log, prof] = await Promise.all([
    fetchJSON(`${API_BASE}/medicines`),
    fetchJSON(`${API_BASE}/reminders`),
    fetchJSON(`${API_BASE}/usage`),
    fetchJSON(`${API_BASE}/profile`),
  ]);
  medicines = med;
  reminders = rem;
  usageLog = log;
  profile = prof;
}

function $(id){ return document.getElementById(id); }
function today(){ return new Date().toISOString().slice(0,10); }
function formatDate(value){
  if(!value) return "—";
  const d = new Date(value + "T00:00:00");
  return d.toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"numeric"});
}
function escapeHtml(value=""){
  return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
}
function daysUntil(date){
  const a = new Date(); a.setHours(0,0,0,0);
  const b = new Date(date+"T00:00:00");
  return Math.ceil((b-a)/86400000);
}
function expiryState(date){
  const d = daysUntil(date);
  if(d < 0) return ["Expired","expired"];
  if(d <= 30) return ["Expiring Soon","expiring"];
  return ["Safe","safe"];
}
function showToast(message){
  const t=$("toast"); t.textContent=message; t.classList.add("show");
  setTimeout(()=>t.classList.remove("show"),2500);
}

function showPage(page){
  document.querySelectorAll(".page").forEach(p=>p.classList.remove("active"));
  document.querySelectorAll(".nav-link").forEach(b=>b.classList.remove("active"));
  const target=$(page); if(!target) return;
  target.classList.add("active");
  const btn=document.querySelector(`.nav-link[data-page="${page}"]`);
  if(btn) btn.classList.add("active");
  const titles={dashboard:"Dashboard",medicines:"Medicines",reminders:"Reminders",expiry:"Expiry Alerts",reports:"Reports",profile:"Profile"};
  $("pageTitle").textContent=titles[page] || "Dashboard";
  if(page==="dashboard") renderDashboard();
  if(page==="medicines") renderMedicines();
  if(page==="reminders") renderReminders();
  if(page==="expiry") renderExpiry();
  if(page==="reports") renderReports();
}
document.querySelectorAll(".nav-link").forEach(b=>b.addEventListener("click",()=>showPage(b.dataset.page)));
document.querySelectorAll("[data-page-target]").forEach(b=>b.addEventListener("click",()=>showPage(b.dataset.pageTarget)));

function renderDashboard(){
  const expiring=medicines.filter(m=>daysUntil(m.expiry)<=30);
  $("totalMedicines").textContent=medicines.length;
  $("todayReminders").textContent=reminders.length;
  $("expiringSoon").textContent=expiring.length;
  $("usageRecords").textContent=usageLog.length;
  $("alertDot").style.display=expiring.length ? "block" : "none";

  const r=$("dashboardReminders");
  r.innerHTML=reminders.length ? reminders.slice().sort((a,b)=>a.time.localeCompare(b.time)).map(x=>`
    <div class="schedule-item">
      <div class="schedule-time">${formatTime(x.time)}</div>
      <div class="schedule-info"><strong>${escapeHtml(x.medicine)}</strong><small>${escapeHtml(x.dose)}</small></div>
      <span class="badge ${x.status.toLowerCase()}">${escapeHtml(x.status)}</span>
    </div>`).join("") : `<div class="empty">No reminders added yet.</div>`;

  $("dashboardExpiry").innerHTML=expiring.length ? expiring.slice().sort((a,b)=>a.expiry.localeCompare(b.expiry)).slice(0,4).map(m=>{
    const [label,cls]=expiryState(m.expiry);
    return `<div class="alert-item"><div class="alert-main"><h4>${escapeHtml(m.name)}</h4><p>Batch: ${escapeHtml(m.batch)} · Expiry: ${formatDate(m.expiry)}</p></div><span class="badge ${cls}">${label}</span></div>`;
  }).join("") : `<div class="empty">No medicines are close to expiry.</div>`;
}

function formatTime(t){
  const [h,m]=t.split(":").map(Number);
  const ap=h>=12?"PM":"AM", hh=(h%12)||12;
  return `${String(hh).padStart(2,"0")}:${String(m).padStart(2,"0")} ${ap}`;
}

function renderMedicines(){
  let data=[...medicines];
  const q=($("medicineSearch").value||"").toLowerCase().trim();
  if(q) data=data.filter(m=>[m.name,m.batch,m.id,m.manufacturer].join(" ").toLowerCase().includes(q));
  const sort=$("medicineSort").value;
  data.sort((a,b)=>sort==="expiry"?a.expiry.localeCompare(b.expiry):sort==="batch"?a.batch.localeCompare(b.batch):a.name.localeCompare(b.name));
  $("medicineTable").innerHTML=data.length ? data.map(m=>{
    const [label,cls]=expiryState(m.expiry);
    return `<tr>
      <td><strong>${escapeHtml(m.name)}</strong><div class="muted">${escapeHtml(m.generic||"")}</div></td>
      <td>${escapeHtml(m.manufacturer||"—")}</td>
      <td>${escapeHtml(m.batch)}</td>
      <td>${formatDate(m.manufacturing)}</td>
      <td>${formatDate(m.expiry)}</td>
      <td>${escapeHtml(m.quantity)}</td>
      <td><span class="badge ${cls}">${label}</span></td>
    </tr>`;
  }).join("") : `<tr><td colspan="7"><div class="empty">No medicines found.</div></td></tr>`;
}
$("medicineSearch").addEventListener("input",renderMedicines);
$("medicineSort").addEventListener("change",renderMedicines);

function renderReminders(){
  populateReminderMedicines();
  $("reminderGrid").innerHTML=reminders.length ? reminders.slice().sort((a,b)=>a.time.localeCompare(b.time)).map(r=>`
    <div class="reminder-card">
      <div class="time">${formatTime(r.time)}</div>
      <h4>${escapeHtml(r.medicine)}</h4>
      <p>${escapeHtml(r.dose)} · ${escapeHtml(r.frequency)}</p>
      <span class="badge ${r.status.toLowerCase()}">${escapeHtml(r.status)}</span>
      <div class="reminder-actions" style="margin-top:15px">
        <button class="small-btn take" onclick="markReminder(${r.id},'Taken')">✓ Taken</button>
        <button class="small-btn skip" onclick="markReminder(${r.id},'Skipped')">↷ Skipped</button>
      </div>
    </div>`).join("") : `<div class="empty">No reminders added yet.</div>`;
}
function populateReminderMedicines(){
  $("reminderMedicine").innerHTML=medicines.length ? medicines.map(m=>`<option value="${m.id}">${escapeHtml(m.name)}</option>`).join("") : `<option value="">Add a medicine first</option>`;
}

async function markReminder(id,status){
  try{
    await fetchJSON(`${API_BASE}/reminders/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    // Refresh reminders + usage log from the server so times/logs stay accurate.
    [reminders, usageLog] = await Promise.all([
      fetchJSON(`${API_BASE}/reminders`),
      fetchJSON(`${API_BASE}/usage`),
    ]);
    renderReminders(); renderDashboard(); renderReports();
    const r = reminders.find(x=>x.id===id);
    showToast(`${r ? r.medicine : "Reminder"} marked ${status.toLowerCase()}.`);
  }catch(err){
    showToast("Could not update reminder: " + err.message);
  }
}

function renderExpiry(){
  const data=[...medicines].sort((a,b)=>a.expiry.localeCompare(b.expiry));
  $("expiryList").innerHTML=data.length ? data.map(m=>{
    const [label,cls]=expiryState(m.expiry);
    return `<div class="alert-item">
      <div class="alert-main"><h4>${escapeHtml(m.name)}</h4><p>Batch No.: ${escapeHtml(m.batch)} · Expiry Date: ${formatDate(m.expiry)} · Quantity: ${escapeHtml(m.quantity)}</p></div>
      <span class="badge ${cls}">${label}</span>
    </div>`;
  }).join("") : `<div class="empty">No medicine records available.</div>`;
}

function renderReports(){
  $("takenCount").textContent=usageLog.filter(x=>x.status==="Taken").length;
  $("skippedCount").textContent=usageLog.filter(x=>x.status==="Skipped").length;
  $("reportMedicineCount").textContent=medicines.length;
  $("usageTable").innerHTML=usageLog.length ? usageLog.slice(0,30).map(x=>`<tr><td><strong>${escapeHtml(x.medicine)}</strong></td><td>${formatDate(x.date)}</td><td>${formatTime(x.time)}</td><td><span class="badge ${x.status==="Taken"?"taken":"expired"}">${escapeHtml(x.status)}</span></td></tr>`).join("") : `<tr><td colspan="4"><div class="empty">No usage records yet. Mark a reminder as Taken or Skipped.</div></td></tr>`;
}

function openModal(id){ $(id).classList.remove("hidden"); }
function closeModal(id){ $(id).classList.add("hidden"); }
document.querySelectorAll("[data-close]").forEach(b=>b.addEventListener("click",()=>closeModal(b.dataset.close)));

function openMedicineModal(){ $("medicineForm").reset(); openModal("medicineModal"); }
$("addBtn").addEventListener("click",openMedicineModal);
$("dashboardAddBtn").addEventListener("click",openMedicineModal);

$("medicineForm").addEventListener("submit", async e=>{
  e.preventDefault();
  const f=new FormData(e.target);
  const payload={
    name:f.get("name"),generic:f.get("generic"),manufacturer:f.get("manufacturer"),
    strength:f.get("strength"),form:f.get("form"),batch:f.get("batch"),
    manufacturing:f.get("manufacturing"),expiry:f.get("expiry"),
    quantity:Number(f.get("quantity")||0),storage:f.get("storage"),
    uses:f.get("uses"),precautions:f.get("precautions"),sideEffects:f.get("sideEffects")
  };
  try{
    const created = await fetchJSON(`${API_BASE}/medicines`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    medicines.push(created);
    closeModal("medicineModal"); renderAll(); showToast("Medicine added successfully.");
  }catch(err){
    showToast("Could not save medicine: " + err.message);
  }
});

$("addReminderBtn").addEventListener("click",()=>{populateReminderMedicines(); $("reminderForm").reset(); openModal("reminderModal");});
$("reminderForm").addEventListener("submit", async e=>{
  e.preventDefault();
  const f=new FormData(e.target);
  const payload={
    medicineId: Number(f.get("medicine")), dose:f.get("dose"),
    frequency:f.get("frequency"), time:f.get("time"), startDate:f.get("startDate"),
    endDate:f.get("endDate"), status:"Pending"
  };
  try{
    const created = await fetchJSON(`${API_BASE}/reminders`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    reminders.push(created);
    closeModal("reminderModal"); renderAll(); showToast("Reminder added successfully.");
  }catch(err){
    showToast("Could not save reminder: " + err.message);
  }
});

function openScan(){openModal("scanModal")}
$("scanBtn").addEventListener("click",openScan);
$("dashboardScanBtn").addEventListener("click",openScan);
$("notificationBtn").addEventListener("click",()=>showPage("expiry"));
$("scanManualBtn").addEventListener("click",()=>{closeModal("scanModal");showPage("medicines");setTimeout(openMedicineModal,150);});

$("saveProfile").addEventListener("click", async ()=>{
  const payload={name:$("profileName").value,age:$("profileAge").value,location:$("profileLocation").value};
  try{
    profile = await fetchJSON(`${API_BASE}/profile`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    showToast("Profile saved.");
  }catch(err){
    showToast("Could not save profile: " + err.message);
  }
});
function loadProfileFields(){
  $("profileName").value=profile.name||"Admin";
  $("profileAge").value=profile.age||"";
  $("profileLocation").value=profile.location||"";
}
function renderAll(){renderDashboard();renderMedicines();renderReminders();renderExpiry();renderReports();loadProfileFields();}

async function init(){
  try{
    await loadAllData();
    renderAll();
  }catch(err){
    showToast("Could not connect to the backend. Is the Flask server running on port 5000?");
    console.error(err);
  }
}
init();
