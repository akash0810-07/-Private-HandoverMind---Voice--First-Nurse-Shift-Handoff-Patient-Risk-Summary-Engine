"""
Generates realistic but entirely fictional demo data: wards, nurses,
handoff recordings, and AI-style patient summaries with a spread of
LOW/MEDIUM/HIGH risk cases, pending tasks, and allergies.

Usage:
    cd backend
    python ../scripts/seed_data.py
"""
import os
import sys
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from faker import Faker
from app import create_app
from app.extensions import db
from app.models import Ward, Nurse, HandoffRecording, PatientSummary, RiskFlag
from app.models.handoff import JOB_COMPLETED
from app.models.summary import REVIEW_PENDING, REVIEW_CONFIRMED

fake = Faker()
Faker.seed(42)
random.seed(42)

WARD_NAMES = ["General Ward A", "ICU", "Orthopedics"]

CONDITIONS_BY_RISK = {
    "LOW": ["Post-operative recovery, stable", "Routine observation", "Mild viral infection"],
    "MEDIUM": ["Pneumonia, responding to treatment", "Post-fall observation", "Controlled hypertension"],
    "HIGH": ["Pneumonia with breathing difficulty", "Suspected sepsis", "Acute confusion, unresponsive episode"],
}

RISK_INDICATOR_POOL = {
    "LOW": [],
    "MEDIUM": ["Abnormal vital sign", "Sudden change in condition"],
    "HIGH": ["Breathing difficulty", "Medication allergy", "Critical observation"],
}


def build_summary(recording_id, risk_level):
    condition = random.choice(CONDITIONS_BY_RISK[risk_level])
    allergies = ["Penicillin"] if risk_level == "HIGH" and random.random() < 0.6 else []
    summary = PatientSummary(
        recording_id=recording_id,
        patient_name=fake.name(),
        bed_number=str(random.randint(1, 30)),
        condition=condition,
        medications=[f"{fake.word().capitalize()} 500mg" for _ in range(random.randint(0, 2))],
        vitals=[f"Temperature {random.choice(['98.6F', '99.1F', '102F', '103F'])}"],
        allergies=allergies,
        pending_tasks=[fake.sentence(nb_words=4) for _ in range(random.randint(0, 2))],
        observations=[fake.sentence(nb_words=6) for _ in range(random.randint(0, 1))],
        risk_level=risk_level,
        ai_confidence=round(random.uniform(0.55, 0.95), 2),
        ai_original_payload={"synthetic": True},
        review_status=random.choice([REVIEW_PENDING, REVIEW_PENDING, REVIEW_CONFIRMED]),
    )
    db.session.add(summary)
    db.session.flush()

    for indicator in RISK_INDICATOR_POOL[risk_level]:
        db.session.add(RiskFlag(
            patient_summary_id=summary.id,
            indicator=indicator,
            evidence=fake.sentence(nb_words=8),
            source=random.choice(["RULE", "AI", "HYBRID"]),
            severity_weight=random.choice([1.5, 2.0, 3.0]),
        ))
    return summary


def run():
    app = create_app()
    with app.app_context():
        db.create_all()

        if Ward.query.first():
            print("Seed data already present — skipping. Drop tables first to reseed.")
            return

        wards = []
        for name in WARD_NAMES:
            w = Ward(name=name, description=f"{name} — synthetic academic demo ward")
            db.session.add(w)
            wards.append(w)
        db.session.commit()

        # A predictable demo nurse used by Playwright E2E tests and manual demos.
        demo_nurse = Nurse(
            full_name="Demo Nurse", email="nurse.demo@handovermind.test",
            role="NURSE", ward_id=wards[0].id,
        )
        demo_nurse.set_password("DemoPass123!")
        db.session.add(demo_nurse)

        admin = Nurse(full_name="Demo Admin", email="admin.demo@handovermind.test", role="ADMIN")
        admin.set_password("DemoAdminPass123!")
        db.session.add(admin)

        nurses = [demo_nurse, admin]
        for ward in wards:
            for _ in range(random.randint(3, 5)):
                n = Nurse(full_name=fake.name(), email=fake.unique.email(), role="NURSE", ward_id=ward.id)
                n.set_password("Password123!")
                db.session.add(n)
                nurses.append(n)
        db.session.commit()

        risk_levels = ["LOW"] * 10 + ["MEDIUM"] * 6 + ["HIGH"] * 4
        random.shuffle(risk_levels)

        for i, risk_level in enumerate(risk_levels):
            ward = wards[i % len(wards)]
            recorder = random.choice([n for n in nurses if n.ward_id == ward.id] or [demo_nurse])
            transcript = (
                f"Synthetic demo transcript for patient case #{i+1}, ward {ward.name}. "
                f"Condition: {random.choice(CONDITIONS_BY_RISK[risk_level])}."
            )
            recording = HandoffRecording(
                ward_id=ward.id, recorded_by_id=recorder.id,
                transcript=transcript, transcript_provider="mock",
                status=JOB_COMPLETED,
            )
            db.session.add(recording)
            db.session.flush()
            build_summary(recording.id, risk_level)

        db.session.commit()
        print("Seed data created:")
        print(f"  Wards: {len(wards)}")
        print(f"  Nurses: {len(nurses)}")
        print(f"  Handoff recordings: {len(risk_levels)}")
        print()
        print("Demo login — nurse.demo@handovermind.test / DemoPass123!")
        print("Demo login — admin.demo@handovermind.test / DemoAdminPass123!")
        print("All data is synthetic/fictional — academic demonstration only.")


if __name__ == "__main__":
    run()
