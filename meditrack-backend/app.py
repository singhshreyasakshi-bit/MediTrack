from datetime import date, datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

from models import Medicine, Profile, Reminder, UsageLog, db, parse_date

app = Flask(__name__)

# --- Config -----------------------------------------------------------
# SQLite by default (zero setup). Swap this line for MySQL/Postgres later, e.g.:
#   "mysql+pymysql://user:password@localhost/meditrack"
#   "postgresql+psycopg2://user:password@localhost/meditrack"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///meditrack.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
CORS(app)  # allows the frontend (served from a different port/file) to call this API


# --- Helpers ------------------------------------------------------------
def bad_request(message):
    return jsonify({"error": message}), 400


def not_found(message="Not found"):
    return jsonify({"error": message}), 404


# --- Medicines ------------------------------------------------------------
@app.get("/api/medicines")
def list_medicines():
    medicines = Medicine.query.order_by(Medicine.name).all()
    return jsonify([m.to_dict() for m in medicines])


@app.get("/api/medicines/<int:medicine_id>")
def get_medicine(medicine_id):
    medicine = Medicine.query.get(medicine_id)
    if not medicine:
        return not_found("Medicine not found")
    return jsonify(medicine.to_dict())


@app.post("/api/medicines")
def create_medicine():
    data = request.get_json(force=True, silent=True) or {}
    if not data.get("name") or not data.get("batch") or not data.get("expiry"):
        return bad_request("name, batch and expiry are required")

    medicine = Medicine(
        name=data.get("name"),
        generic=data.get("generic"),
        manufacturer=data.get("manufacturer"),
        strength=data.get("strength"),
        form=data.get("form"),
        batch=data.get("batch"),
        manufacturing_date=parse_date(data.get("manufacturing")),
        expiry_date=parse_date(data.get("expiry")),
        quantity=data.get("quantity", 1),
        storage=data.get("storage"),
        uses=data.get("uses"),
        precautions=data.get("precautions"),
        side_effects=data.get("sideEffects"),
    )
    db.session.add(medicine)
    db.session.commit()
    return jsonify(medicine.to_dict()), 201


@app.put("/api/medicines/<int:medicine_id>")
def update_medicine(medicine_id):
    medicine = Medicine.query.get(medicine_id)
    if not medicine:
        return not_found("Medicine not found")

    data = request.get_json(force=True, silent=True) or {}
    for field, attr in [
        ("name", "name"),
        ("generic", "generic"),
        ("manufacturer", "manufacturer"),
        ("strength", "strength"),
        ("form", "form"),
        ("batch", "batch"),
        ("quantity", "quantity"),
        ("storage", "storage"),
        ("uses", "uses"),
        ("precautions", "precautions"),
        ("sideEffects", "side_effects"),
    ]:
        if field in data:
            setattr(medicine, attr, data[field])
    if "manufacturing" in data:
        medicine.manufacturing_date = parse_date(data["manufacturing"])
    if "expiry" in data:
        medicine.expiry_date = parse_date(data["expiry"])

    db.session.commit()
    return jsonify(medicine.to_dict())


@app.delete("/api/medicines/<int:medicine_id>")
def delete_medicine(medicine_id):
    medicine = Medicine.query.get(medicine_id)
    if not medicine:
        return not_found("Medicine not found")
    db.session.delete(medicine)
    db.session.commit()
    return jsonify({"message": "Deleted"})


# --- Reminders ------------------------------------------------------------
@app.get("/api/reminders")
def list_reminders():
    reminders = Reminder.query.order_by(Reminder.time).all()
    return jsonify([r.to_dict() for r in reminders])


@app.post("/api/reminders")
def create_reminder():
    data = request.get_json(force=True, silent=True) or {}
    medicine_id = data.get("medicineId")
    medicine = Medicine.query.get(medicine_id) if medicine_id else None
    if not medicine:
        return bad_request("A valid medicineId is required")

    reminder = Reminder(
        medicine_id=medicine.id,
        dose=data.get("dose"),
        frequency=data.get("frequency"),
        time=data.get("time"),
        start_date=parse_date(data.get("startDate")),
        end_date=parse_date(data.get("endDate")),
        status=data.get("status", "Pending"),
    )
    db.session.add(reminder)
    db.session.commit()
    return jsonify(reminder.to_dict()), 201


@app.put("/api/reminders/<int:reminder_id>")
def update_reminder(reminder_id):
    reminder = Reminder.query.get(reminder_id)
    if not reminder:
        return not_found("Reminder not found")

    data = request.get_json(force=True, silent=True) or {}
    for field, attr in [
        ("dose", "dose"),
        ("frequency", "frequency"),
        ("time", "time"),
        ("status", "status"),
    ]:
        if field in data:
            setattr(reminder, attr, data[field])
    if "startDate" in data:
        reminder.start_date = parse_date(data["startDate"])
    if "endDate" in data:
        reminder.end_date = parse_date(data["endDate"])

    db.session.commit()
    return jsonify(reminder.to_dict())


@app.patch("/api/reminders/<int:reminder_id>/status")
def set_reminder_status(reminder_id):
    """Mark a reminder Taken/Skipped and automatically write a usage log entry."""
    reminder = Reminder.query.get(reminder_id)
    if not reminder:
        return not_found("Reminder not found")

    data = request.get_json(force=True, silent=True) or {}
    status = data.get("status")
    if status not in ("Taken", "Skipped", "Pending"):
        return bad_request("status must be Taken, Skipped or Pending")

    reminder.status = status
    if status in ("Taken", "Skipped"):
        log = UsageLog(
            medicine_id=reminder.medicine_id,
            reminder_id=reminder.id,
            log_date=date.today(),
            log_time=datetime.now().strftime("%H:%M"),
            status=status,
        )
        db.session.add(log)

    db.session.commit()
    return jsonify(reminder.to_dict())


@app.delete("/api/reminders/<int:reminder_id>")
def delete_reminder(reminder_id):
    reminder = Reminder.query.get(reminder_id)
    if not reminder:
        return not_found("Reminder not found")
    db.session.delete(reminder)
    db.session.commit()
    return jsonify({"message": "Deleted"})


# --- Usage log / reports ---------------------------------------------------
@app.get("/api/usage")
def list_usage():
    logs = UsageLog.query.order_by(UsageLog.log_date.desc()).all()
    return jsonify([log.to_dict() for log in logs])


# --- Profile ----------------------------------------------------------------
@app.get("/api/profile")
def get_profile():
    profile = Profile.query.first()
    if not profile:
        profile = Profile(name="Admin")
        db.session.add(profile)
        db.session.commit()
    return jsonify(profile.to_dict())


@app.put("/api/profile")
def update_profile():
    profile = Profile.query.first()
    if not profile:
        profile = Profile()
        db.session.add(profile)

    data = request.get_json(force=True, silent=True) or {}
    if "name" in data:
        profile.name = data["name"]
    if "age" in data:
        profile.age = data["age"]
    if "location" in data:
        profile.location = data["location"]

    db.session.commit()
    return jsonify(profile.to_dict())


# --- Dashboard summary -------------------------------------------------------
@app.get("/api/dashboard/stats")
def dashboard_stats():
    total_medicines = Medicine.query.count()
    today_str = date.today().isoformat()
    today_reminders = Reminder.query.filter(
        (Reminder.start_date.is_(None)) | (Reminder.start_date <= date.today())
    ).count()
    expiring_soon = sum(
        1
        for m in Medicine.query.all()
        if m.expiry_date and 0 <= (m.expiry_date - date.today()).days <= 30
    )
    usage_records = UsageLog.query.count()

    return jsonify(
        {
            "totalMedicines": total_medicines,
            "todayReminders": today_reminders,
            "expiringSoon": expiring_soon,
            "usageRecords": usage_records,
        }
    )


# --- Entry point --------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
