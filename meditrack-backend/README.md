# MediTrack Backend (Flask + SQLite)

A REST API that mirrors the data your frontend already keeps in `localStorage`
(medicines, reminders, usage log, profile) — swap the `localStorage` calls in
`script.js` for `fetch()` calls to this API and you have a real backend.

## 1. Setup

```bash
cd meditrack-backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

python seed.py                # creates meditrack.db + loads sample data (run once)
python app.py                 # starts the API on http://localhost:5000
```

SQLite needs no server — `meditrack.db` is just a file created next to `app.py`.
When you're ready for something more production-like, change one line in
`app.py`:

```python
# MySQL:
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://user:password@localhost/meditrack"
# PostgreSQL:
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://user:password@localhost/meditrack"
```
(then `pip install pymysql` or `psycopg2-binary`, and create the database itself
first — `CREATE DATABASE meditrack;` — SQLAlchemy creates the tables, not the DB).

## 2. Database schema

| Table         | Purpose                                             |
|---------------|------------------------------------------------------|
| `medicines`   | name, batch, manufacturing/expiry dates, quantity...  |
| `reminders`   | dose, frequency, time, linked to a medicine           |
| `usage_logs`  | auto-created whenever a reminder is marked Taken/Skipped |
| `profile`     | single-row Admin profile (name/age/location)          |

## 3. API endpoints

| Method | Endpoint                          | Purpose                        |
|--------|------------------------------------|---------------------------------|
| GET    | `/api/medicines`                  | list all medicines             |
| POST   | `/api/medicines`                  | add a medicine                 |
| PUT    | `/api/medicines/<id>`             | edit a medicine                |
| DELETE | `/api/medicines/<id>`             | delete a medicine              |
| GET    | `/api/reminders`                  | list all reminders             |
| POST   | `/api/reminders`                  | add a reminder                 |
| PUT    | `/api/reminders/<id>`             | edit a reminder                |
| PATCH  | `/api/reminders/<id>/status`      | mark Taken/Skipped (also logs usage) |
| DELETE | `/api/reminders/<id>`             | delete a reminder              |
| GET    | `/api/usage`                      | usage log (for Reports page)   |
| GET    | `/api/profile` / `PUT /api/profile` | read/update profile          |
| GET    | `/api/dashboard/stats`            | counts for the dashboard cards |

All request/response bodies are JSON and use the same field names your
`medicineForm` / `reminderForm` already submit (`name`, `batch`, `expiry`,
`medicineId`, `dose`, `time`, etc.), so the payloads map over almost directly.

## 4. Connecting your existing `script.js`

Right now you have:

```javascript
let medicines = load(STORAGE_MED, defaultMedicines);
function save(key, value){ localStorage.setItem(key, JSON.stringify(value)); }
```

Replace the load/save pair with fetch calls to the API, e.g.:

```javascript
const API = "http://localhost:5000/api";

async function loadMedicines() {
  const res = await fetch(`${API}/medicines`);
  medicines = await res.json();
  renderMedicines();
}

async function addMedicine(formData) {
  const res = await fetch(`${API}/medicines`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formData),
  });
  const newMedicine = await res.json();
  medicines.push(newMedicine);
  renderMedicines();
}
```

Do the same pattern for reminders (`PATCH /api/reminders/<id>/status` when the
user taps "Mark Taken/Skipped"), usage log, and profile. Because CORS is
already enabled in `app.py`, you can keep serving `index.html` as a static
file (e.g. double-click it, or `python -m http.server` in the frontend
folder) while the API runs separately on port 5000.

## 5. Next steps once this is working

- Swap SQLite for MySQL/Postgres (one line, see above) when you need multiple
  concurrent users.
- Add authentication (Flask-JWT-Extended) if this stops being single-admin.
- Deploy: Render/Railway/PythonAnywhere for the Flask API, plus any static
  host (Netlify/Vercel/GitHub Pages) for the frontend.
