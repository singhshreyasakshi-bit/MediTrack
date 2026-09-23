from datetime import date, datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def parse_date(value):
    """Accepts 'YYYY-MM-DD' string or None, returns a date object or None."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


class Medicine(db.Model):
    __tablename__ = "medicines"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    generic = db.Column(db.String(150))
    manufacturer = db.Column(db.String(150))
    strength = db.Column(db.String(50))
    form = db.Column(db.String(50))
    batch = db.Column(db.String(50), nullable=False)
    manufacturing_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    storage = db.Column(db.String(255))
    uses = db.Column(db.Text)
    precautions = db.Column(db.Text)
    side_effects = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    reminders = db.relationship(
        "Reminder", backref="medicine", cascade="all, delete-orphan"
    )
    usage_logs = db.relationship(
        "UsageLog", backref="medicine", cascade="all, delete-orphan"
    )

    def to_dict(self):
        today = date.today()
        days_left = (self.expiry_date - today).days if self.expiry_date else None
        if days_left is None:
            status = "Unknown"
        elif days_left < 0:
            status = "Expired"
        elif days_left <= 30:
            status = "Expiring Soon"
        else:
            status = "Safe"

        return {
            "id": self.id,
            "name": self.name,
            "generic": self.generic,
            "manufacturer": self.manufacturer,
            "strength": self.strength,
            "form": self.form,
            "batch": self.batch,
            "manufacturing": self.manufacturing_date.isoformat()
            if self.manufacturing_date
            else None,
            "expiry": self.expiry_date.isoformat() if self.expiry_date else None,
            "quantity": self.quantity,
            "storage": self.storage,
            "uses": self.uses,
            "precautions": self.precautions,
            "sideEffects": self.side_effects,
            "status": status,
            "daysLeft": days_left,
        }


class Reminder(db.Model):
    __tablename__ = "reminders"

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(
        db.Integer, db.ForeignKey("medicines.id"), nullable=False
    )
    dose = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    time = db.Column(db.String(10))  # "HH:MM"
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default="Pending")  # Pending / Taken / Skipped

    usage_logs = db.relationship("UsageLog", backref="reminder")

    def to_dict(self):
        return {
            "id": self.id,
            "medicineId": self.medicine_id,
            "medicine": self.medicine.name if self.medicine else None,
            "dose": self.dose,
            "frequency": self.frequency,
            "time": self.time,
            "startDate": self.start_date.isoformat() if self.start_date else None,
            "endDate": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
        }


class UsageLog(db.Model):
    __tablename__ = "usage_logs"

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey("medicines.id"))
    reminder_id = db.Column(db.Integer, db.ForeignKey("reminders.id"))
    log_date = db.Column(db.Date, default=date.today)
    log_time = db.Column(db.String(10))
    status = db.Column(db.String(20))  # Taken / Skipped

    def to_dict(self):
        return {
            "id": self.id,
            "medicineId": self.medicine_id,
            "medicine": self.medicine.name if self.medicine else None,
            "reminderId": self.reminder_id,
            "date": self.log_date.isoformat() if self.log_date else None,
            "time": self.log_time,
            "status": self.status,
        }


class Profile(db.Model):
    __tablename__ = "profile"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), default="Admin")
    age = db.Column(db.Integer)
    location = db.Column(db.String(120))

    def to_dict(self):
        return {"name": self.name, "age": self.age, "location": self.location}
