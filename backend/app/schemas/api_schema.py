from marshmallow import Schema, fields, validate

RISK_LEVELS = ("LOW", "MEDIUM", "HIGH")


class PatientSummaryUpdateSchema(Schema):
    patient_name = fields.String(allow_none=True)
    bed_number = fields.String(allow_none=True)
    condition = fields.String(allow_none=True)
    medications = fields.List(fields.String(), allow_none=True)
    vitals = fields.List(fields.String(), allow_none=True)
    allergies = fields.List(fields.String(), allow_none=True)
    pending_tasks = fields.List(fields.String(), allow_none=True)
    observations = fields.List(fields.String(), allow_none=True)
    risk_level = fields.String(validate=validate.OneOf(RISK_LEVELS), allow_none=True)


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=1))
