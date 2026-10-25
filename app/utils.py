import random
import string
import re
from datetime import datetime, date, timedelta
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
COMPONENTS = ['Whole Blood', 'Red Blood Cells', 'Platelets', 'Plasma']

# Compatibility dictionary: For a given patient blood group (recipient), which donor blood groups are compatible?
COMPATIBILITY_RECIPIENT_CAN_RECEIVE = {
    'O-': ['O-'],
    'O+': ['O+', 'O-'],
    'A-': ['A-', 'O-'],
    'A+': ['A+', 'A-', 'O+', 'O-'],
    'B-': ['B-', 'O-'],
    'B+': ['B+', 'B-', 'O+', 'O-'],
    'AB-': ['AB-', 'A-', 'B-', 'O-'],
    'AB+': ['AB+', 'AB-', 'A+', 'A-', 'B+', 'B-', 'O+', 'O-']
}

# For a given donor blood group, who can receive it?
COMPATIBILITY_DONOR_CAN_GIVE_TO = {
    'O-': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'],
    'O+': ['O+', 'A+', 'B+', 'AB+'],
    'A-': ['A-', 'A+', 'AB-', 'AB+'],
    'A+': ['A+', 'AB+'],
    'B-': ['B-', 'B+', 'AB-', 'AB+'],
    'B+': ['B+', 'AB+'],
    'AB-': ['AB-', 'AB+'],
    'AB+': ['AB+']
}

def get_compatible_donors_for_recipient(recipient_group):
    """Returns list of donor blood groups compatible with the recipient."""
    return COMPATIBILITY_RECIPIENT_CAN_RECEIVE.get(recipient_group, [recipient_group])

def get_compatible_recipients_for_donor(donor_group):
    """Returns list of recipient blood groups that can receive from donor."""
    return COMPATIBILITY_DONOR_CAN_GIVE_TO.get(donor_group, [donor_group])

def is_compatible(donor_group, recipient_group):
    """Returns True if donor can give blood to recipient."""
    return recipient_group in COMPATIBILITY_DONOR_CAN_GIVE_TO.get(donor_group, [])

def validate_phone(phone_str):
    """Validates that a phone string contains exactly 10 digits and returns (is_valid, cleaned_digits)."""
    if not phone_str:
        return False, ""
    cleaned = re.sub(r'\D', '', str(phone_str))
    # Must be exactly 10 digits
    if len(cleaned) == 10 and cleaned.isdigit():
        return True, cleaned
    return False, cleaned

def generate_bag_barcode(blood_group):
    clean_bg = blood_group.replace('+', 'P').replace('-', 'N')
    date_str = datetime.now().strftime('%y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"BB-{clean_bg}-{date_str}-{random_str}"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Administrator privileges are required to access this resource.", "danger")
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_staff:
            flash("Staff or Administrator access is required.", "danger")
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def update_expired_inventory_units(db, BloodInventory):
    """Mark all available units that have passed their expiry date as 'Expired'."""
    today = date.today()
    expired_units = BloodInventory.query.filter(
        BloodInventory.expiry_date < today,
        BloodInventory.status == 'Available'
    ).all()
    count = 0
    for unit in expired_units:
        unit.status = 'Expired'
        count += 1
    if count > 0:
        db.session.commit()
    return count
