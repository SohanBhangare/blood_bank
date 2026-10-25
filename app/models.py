from datetime import datetime, date, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')  # 'admin', 'staff', 'donor'
    full_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship for donor role
    donor_profile = db.relationship('Donor', backref='user_account', uselist=False, lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_staff(self):
        return self.role in ['admin', 'staff']

    @property
    def is_donor(self):
        return self.role == 'donor'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Donor(db.Model):
    __tablename__ = 'donors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False, index=True)  # A+, A-, B+, B-, AB+, AB-, O+, O-
    gender = db.Column(db.String(10), nullable=False)  # Male, Female, Other
    date_of_birth = db.Column(db.Date, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(50), nullable=True, default='Pune')
    state = db.Column(db.String(50), nullable=True, default='Maharashtra')
    pincode = db.Column(db.String(10), nullable=True)
    status = db.Column(db.String(20), default='Eligible')  # Eligible, Deferred, Inactive
    last_donation_date = db.Column(db.Date, nullable=True)
    total_donations = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Detailed Medical History Questionnaire Fields
    has_chronic_illness = db.Column(db.Boolean, default=False)
    chronic_illness_details = db.Column(db.String(255), nullable=True)
    has_recent_surgery = db.Column(db.Boolean, default=False)  # Past 6 months
    has_recent_tattoo_piercing = db.Column(db.Boolean, default=False)  # Past 6 months
    on_medications = db.Column(db.Boolean, default=False)
    medications_details = db.Column(db.String(255), nullable=True)
    has_infectious_history = db.Column(db.Boolean, default=False)  # Hep B/C, HIV, malaria
    is_pregnant_or_nursing = db.Column(db.Boolean, default=False)
    medical_notes = db.Column(db.Text, nullable=True)

    donations = db.relationship('Donation', backref='donor', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if not self.date_of_birth:
            return 0
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def days_since_last_donation(self):
        if not self.last_donation_date:
            return 9999
        return (date.today() - self.last_donation_date).days

    @property
    def is_eligible_to_donate(self):
        if self.status != 'Eligible':
            return False, f"Status is {self.status}"
        if self.age < 18 or self.age > 65:
            return False, f"Age {self.age} not within eligible 18-65 range"
        if self.weight_kg < 50:
            return False, f"Weight {self.weight_kg}kg is below minimum 50kg requirement"
        if self.has_infectious_history:
            return False, "Deferred: History of infectious disease (Hepatitis, HIV, Malaria)"
        if self.has_chronic_illness:
            return False, f"Deferred: Chronic condition ({self.chronic_illness_details or 'Medical condition'})"
        if self.has_recent_surgery:
            return False, "Temporary deferral: Surgery within the past 6 months"
        if self.has_recent_tattoo_piercing:
            return False, "Temporary deferral: Tattoo / piercing within the past 6 months"
        if self.is_pregnant_or_nursing:
            return False, "Temporary deferral: Pregnancy or nursing period"
        if self.last_donation_date:
            days = self.days_since_last_donation
            if days < 90:
                next_date = self.last_donation_date + timedelta(days=90)
                return False, f"Recent donation cooldown. Eligible again on {next_date.strftime('%b %d, %Y')} ({90 - days} days left)"
        return True, "Eligible to donate blood"

    def __repr__(self):
        return f'<Donor {self.full_name} ({self.blood_group})>'


class DonationCamp(db.Model):
    __tablename__ = 'donation_camps'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    organizer = db.Column(db.String(150), nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False, default='Pune')
    state = db.Column(db.String(50), default='Maharashtra')
    pincode = db.Column(db.String(10), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    operating_hours = db.Column(db.String(100), default='09:00 AM - 05:00 PM')
    contact_person = db.Column(db.String(100), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    target_units = db.Column(db.Integer, default=100)
    collected_units = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='Ongoing')  # Ongoing, Upcoming, Completed
    facilities = db.Column(db.String(255), default='Air-conditioned blood mobile, certified doctors, refreshments & certificate')
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_active_today(self):
        today = date.today()
        return self.start_date <= today <= self.end_date

    def __repr__(self):
        return f'<DonationCamp {self.name} [{self.status}]>'


class Hospital(db.Model):
    __tablename__ = 'hospitals'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    hospital_type = db.Column(db.String(50), default='Multi-Specialty')  # Super-Specialty, Trauma Center, Govt Hospital
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(50), nullable=False, default='Pune')
    state = db.Column(db.String(50), default='Maharashtra')
    pincode = db.Column(db.String(10), nullable=True)
    phone = db.Column(db.String(50), nullable=False)
    emergency_helpline = db.Column(db.String(50), nullable=False)
    accepts_donations = db.Column(db.Boolean, default=True)
    blood_bank_inhouse = db.Column(db.Boolean, default=True)
    blood_groups_accepted = db.Column(db.String(100), default='All Blood Groups (A+, A-, B+, B-, AB+, AB-, O+, O-)')
    urgent_requirements = db.Column(db.String(255), nullable=True)
    timing = db.Column(db.String(100), default='24x7 Emergency Blood Wing')
    map_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Hospital {self.name} ({self.city})>'


class Donation(db.Model):
    __tablename__ = 'donations'

    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donors.id'), nullable=False)
    camp_id = db.Column(db.Integer, db.ForeignKey('donation_camps.id'), nullable=True)
    donation_date = db.Column(db.Date, default=date.today, nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    component = db.Column(db.String(30), default='Whole Blood')  # Whole Blood, RBC, Platelets, Plasma
    units = db.Column(db.Integer, default=1)
    systolic_bp = db.Column(db.Integer, nullable=True)  # mmHg
    diastolic_bp = db.Column(db.Integer, nullable=True)
    hemoglobin_level = db.Column(db.Float, nullable=True)  # g/dL
    pulse_rate = db.Column(db.Integer, nullable=True)
    bag_barcode = db.Column(db.String(50), unique=True, nullable=False)
    screening_status = db.Column(db.String(20), default='Passed')  # Passed, Failed, Pending
    remarks = db.Column(db.Text, nullable=True)
    recorded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recorder = db.relationship('User', foreign_keys=[recorded_by_id])
    camp = db.relationship('DonationCamp', backref='camp_donations')
    inventory_items = db.relationship('BloodInventory', backref='source_donation', lazy='dynamic')

    def __repr__(self):
        return f'<Donation {self.bag_barcode} ({self.blood_group})>'


class BloodInventory(db.Model):
    __tablename__ = 'blood_inventory'

    id = db.Column(db.Integer, primary_key=True)
    bag_barcode = db.Column(db.String(50), unique=True, nullable=False, index=True)
    blood_group = db.Column(db.String(5), nullable=False, index=True)
    component = db.Column(db.String(30), default='Whole Blood')
    units = db.Column(db.Integer, default=1)
    collection_date = db.Column(db.Date, default=date.today, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(20), default='Available', index=True)  # Available, Reserved, Dispatched, Expired, Discarded
    storage_location = db.Column(db.String(100), default='Cold Storage - Shelf A')
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id'), nullable=True)
    request_id = db.Column(db.Integer, db.ForeignKey('blood_requests.id'), nullable=True)
    notes = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    dispatch_record = db.relationship('Dispatch', backref='inventory_unit', uselist=False)

    @property
    def is_expired(self):
        return date.today() > self.expiry_date

    @property
    def days_until_expiry(self):
        return (self.expiry_date - date.today()).days

    def __repr__(self):
        return f'<BloodInventory {self.bag_barcode} {self.blood_group} [{self.status}]>'


class BloodRequest(db.Model):
    __tablename__ = 'blood_requests'

    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    patient_age = db.Column(db.Integer, nullable=True)
    patient_gender = db.Column(db.String(10), nullable=True)
    hospital_name = db.Column(db.String(150), nullable=False)
    hospital_contact = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(50), default='Pune', nullable=True)
    doctor_name = db.Column(db.String(100), nullable=True)
    required_blood_group = db.Column(db.String(5), nullable=False, index=True)
    component = db.Column(db.String(30), default='Whole Blood')
    units_requested = db.Column(db.Integer, nullable=False, default=1)
    units_allocated = db.Column(db.Integer, default=0)
    urgency = db.Column(db.String(20), default='Normal', index=True)  # Normal, Urgent, Emergency
    diagnosis_reason = db.Column(db.Text, nullable=True)
    contact_person = db.Column(db.String(100), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Pending', index=True)  # Pending, Approved, Dispatched, Rejected, Cancelled
    request_date = db.Column(db.Date, default=date.today)
    required_by_date = db.Column(db.Date, nullable=True)
    rejection_reason = db.Column(db.String(255), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by_id])
    dispatches = db.relationship('Dispatch', backref='request', lazy='dynamic', cascade='all, delete-orphan')
    allocated_units = db.relationship('BloodInventory', backref='allocated_request', foreign_keys='BloodInventory.request_id')

    def __repr__(self):
        return f'<BloodRequest #{self.id} {self.patient_name} - {self.required_blood_group} ({self.status})>'


class Dispatch(db.Model):
    __tablename__ = 'dispatches'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('blood_requests.id'), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey('blood_inventory.id'), nullable=False)
    dispatch_date = db.Column(db.DateTime, default=datetime.utcnow)
    dispatched_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    recipient_name = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    dispatched_by = db.relationship('User', foreign_keys=[dispatched_by_id])

    def __repr__(self):
        return f'<Dispatch Request #{self.request_id} Unit #{self.inventory_id}>'
