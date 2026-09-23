"""Run once to populate the database with the same sample data the frontend
originally shipped with (so the app isn't empty on first run).

Usage:
    python seed.py
"""
from app import app
from models import Medicine, Profile, Reminder, db, parse_date

SAMPLE_MEDICINES = [
    dict(
        name="Paracetamol 650mg", generic="Paracetamol", manufacturer="Example Pharma",
        strength="650 mg", form="Tablet", batch="B12345",
        manufacturing="2026-01-10", expiry="2026-10-15", quantity=20,
        storage="Store in a cool, dry place", uses="As prescribed",
        precautions="Use according to prescription", sideEffects="May vary",
    ),
    dict(
        name="Vitamin D3", generic="Cholecalciferol", manufacturer="Example Healthcare",
        strength="60K", form="Capsule", batch="B45678",
        manufacturing="2026-02-05", expiry="2027-01-20", quantity=30,
        storage="Store as directed on the package", uses="As prescribed",
        precautions="Follow prescribed dose", sideEffects="May vary",
    ),
    dict(
        name="Amoxicillin 625mg", generic="Amoxicillin", manufacturer="Example Labs",
        strength="625 mg", form="Tablet", batch="B78912",
        manufacturing="2026-03-01", expiry="2026-09-20", quantity=15,
        storage="Store in a cool, dry place", uses="As prescribed",
        precautions="Use only as prescribed", sideEffects="May vary",
    ),
]

SAMPLE_REMINDERS = [
    dict(medicine="Paracetamol 650mg", dose="1 Tablet", frequency="Once daily", time="09:00", status="Pending"),
    dict(medicine="Vitamin D3", dose="1 Capsule", frequency="Once daily", time="13:00", status="Pending"),
    dict(medicine="Amoxicillin 625mg", dose="1 Tablet", frequency="As prescribed", time="21:00", status="Upcoming"),
]

with app.app_context():
    db.create_all()

    if Medicine.query.count() == 0:
        name_to_id = {}
        for m in SAMPLE_MEDICINES:
            med = Medicine(
                name=m["name"], generic=m["generic"], manufacturer=m["manufacturer"],
                strength=m["strength"], form=m["form"], batch=m["batch"],
                manufacturing_date=parse_date(m["manufacturing"]),
                expiry_date=parse_date(m["expiry"]), quantity=m["quantity"],
                storage=m["storage"], uses=m["uses"],
                precautions=m["precautions"], side_effects=m["sideEffects"],
            )
            db.session.add(med)
            db.session.flush()  # get med.id before commit
            name_to_id[m["name"]] = med.id

        for r in SAMPLE_REMINDERS:
            db.session.add(Reminder(
                medicine_id=name_to_id[r["medicine"]],
                dose=r["dose"], frequency=r["frequency"],
                time=r["time"], status=r["status"],
            ))

        db.session.commit()
        print("Seeded medicines and reminders.")
    else:
        print("Medicines already exist — skipping seed.")

    if Profile.query.count() == 0:
        db.session.add(Profile(name="Admin"))
        db.session.commit()
        print("Seeded profile.")
