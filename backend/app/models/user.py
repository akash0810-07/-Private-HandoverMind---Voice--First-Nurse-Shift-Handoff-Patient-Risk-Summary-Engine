import bcrypt
from app.extensions import db
from app.models.base import BaseModel


class Ward(BaseModel):
    __tablename__ = "wards"

    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))

    nurses = db.relationship("Nurse", back_populates="ward")
    recordings = db.relationship("HandoffRecording", back_populates="ward")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}


class Nurse(BaseModel):
    __tablename__ = "nurses"

    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="NURSE")  # NURSE | ADMIN
    ward_id = db.Column(db.String(36), db.ForeignKey("wards.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    ward = db.relationship("Ward", back_populates="nurses")

    def set_password(self, raw_password: str) -> None:
        self.password_hash = bcrypt.hashpw(
            raw_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                raw_password.encode("utf-8"), self.password_hash.encode("utf-8")
            )
        except ValueError:
            return False

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "ward_id": self.ward_id,
            "ward_name": self.ward.name if self.ward else None,
            "is_active": self.is_active,
        }
