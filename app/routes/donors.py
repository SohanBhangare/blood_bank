from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app import db
from app.models import Donor, Donation, BloodInventory
from app.utils import BLOOD_GROUPS, staff_required, admin_required, generate_bag_barcode, validate_phone

donors_bp = Blueprint('donors', __name__)

@donors_bp.route('/')
@login_required
@staff_required
def list_donors():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    blood_group = request.args.get('blood_group', '').strip()
    status = request.args.get('status', '').strip()

    query = Donor.query

    if search:
        query = query.filter(
            (Donor.first_name.ilike(f'%{search}%')) |
            (Donor.last_name.ilike(f'%{search}%')) |
            (Donor.phone.ilike(f'%{search}%')) |
            (Donor.email.ilike(f'%{search}%')) |
            (Donor.city.ilike(f'%{search}%'))
        )
    if blood_group:
        query = query.filter_by(blood_group=blood_group)
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(Donor.first_name.asc()).paginate(page=page, per_page=10, error_out=False)
    donors = pagination.items

    return render_template(
        'donors/list.html',
        donors=donors,
        pagination=pagination,
        search=search,
        selected_bg=blood_group,
        selected_status=status,
        blood_groups=BLOOD_GROUPS
    )

@donors_bp.route('/add', methods=['GET', 'POST'])
@login_required
@staff_required
def add_donor():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        blood_group = request.form.get('blood_group', '')
        gender = request.form.get('gender', '')
        dob_str = request.form.get('date_of_birth', '')
        weight_str = request.form.get('weight_kg', '0')
        address = request.form.get('address', '')
        city = request.form.get('city', '')
        state = request.form.get('state', '')
        pincode = request.form.get('pincode', '')
        medical_notes = request.form.get('medical_notes', '')

        # Medical History fields
        has_chronic_illness = bool(request.form.get('has_chronic_illness'))
        chronic_illness_details = request.form.get('chronic_illness_details', '').strip()
        has_recent_surgery = bool(request.form.get('has_recent_surgery'))
        has_recent_tattoo_piercing = bool(request.form.get('has_recent_tattoo_piercing'))
        on_medications = bool(request.form.get('on_medications'))
        medications_details = request.form.get('medications_details', '').strip()
        has_infectious_history = bool(request.form.get('has_infectious_history'))
        is_pregnant_or_nursing = bool(request.form.get('is_pregnant_or_nursing'))

        init_status = 'Deferred' if (has_infectious_history or has_chronic_illness or has_recent_surgery or has_recent_tattoo_piercing or is_pregnant_or_nursing) else 'Eligible'

        if not all([first_name, last_name, email, phone, blood_group, dob_str]):
            flash('Please fill in all mandatory fields.', 'danger')
            return render_template('donors/form.html', blood_groups=BLOOD_GROUPS, donor=None)

        is_phone_valid, clean_phone = validate_phone(phone)
        if not is_phone_valid:
            flash('Phone number must be exactly 10 digits (e.g. 9876543210).', 'danger')
            return render_template('donors/form.html', blood_groups=BLOOD_GROUPS, donor=None)
        phone = clean_phone

        if Donor.query.filter_by(email=email).first():
            flash('A donor with this email address is already registered.', 'danger')
            return render_template('donors/form.html', blood_groups=BLOOD_GROUPS, donor=None)

        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            weight = float(weight_str)
        except ValueError:
            flash('Invalid date of birth or weight value.', 'danger')
            return render_template('donors/form.html', blood_groups=BLOOD_GROUPS, donor=None)

        new_donor = Donor(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            blood_group=blood_group,
            gender=gender,
            date_of_birth=dob,
            weight_kg=weight,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            medical_notes=medical_notes,
            status=init_status,
            has_chronic_illness=has_chronic_illness,
            chronic_illness_details=chronic_illness_details,
            has_recent_surgery=has_recent_surgery,
            has_recent_tattoo_piercing=has_recent_tattoo_piercing,
            on_medications=on_medications,
            medications_details=medications_details,
            has_infectious_history=has_infectious_history,
            is_pregnant_or_nursing=is_pregnant_or_nursing
        )
        db.session.add(new_donor)
        db.session.commit()

        flash(f'Donor {new_donor.full_name} ({new_donor.blood_group}) registered successfully!', 'success')
        return redirect(url_for('donors.view_donor', id=new_donor.id))

    return render_template('donors/form.html', blood_groups=BLOOD_GROUPS, donor=None)

@donors_bp.route('/<int:id>')
@login_required
@staff_required
def view_donor(id):
    donor = Donor.query.get_or_404(id)
    is_eligible, eligibility_msg = donor.is_eligible_to_donate
    donations = donor.donations.order_by(Donation.donation_date.desc()).all()
    return render_template(
        'donors/view.html',
        donor=donor,
        is_eligible=is_eligible,
        eligibility_msg=eligibility_msg,
        donations=donations
    )

@donors_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@staff_required
def edit_donor(id):
    donor = Donor.query.get_or_404(id)

    if request.method == 'POST':
        phone_input = request.form.get('phone', '').strip()
        is_phone_valid, clean_phone = validate_phone(phone_input)
        if not is_phone_valid:
            flash('Phone number must be exactly 10 digits (e.g. 9876543210).', 'danger')
            return render_template('donors/form.html', blood_groups=BLOOD_GROUPS, donor=donor)

        donor.first_name = request.form.get('first_name', donor.first_name).strip()
        donor.last_name = request.form.get('last_name', donor.last_name).strip()
        donor.phone = clean_phone
        donor.blood_group = request.form.get('blood_group', donor.blood_group)
        donor.gender = request.form.get('gender', donor.gender)
        donor.address = request.form.get('address', donor.address)
        donor.city = request.form.get('city', donor.city)
        donor.state = request.form.get('state', donor.state)
        donor.pincode = request.form.get('pincode', donor.pincode)
        donor.medical_notes = request.form.get('medical_notes', donor.medical_notes)
        donor.status = request.form.get('status', donor.status)

        # Medical History fields
        donor.has_chronic_illness = bool(request.form.get('has_chronic_illness'))
        donor.chronic_illness_details = request.form.get('chronic_illness_details', '').strip()
        donor.has_recent_surgery = bool(request.form.get('has_recent_surgery'))
        donor.has_recent_tattoo_piercing = bool(request.form.get('has_recent_tattoo_piercing'))
        donor.on_medications = bool(request.form.get('on_medications'))
        donor.medications_details = request.form.get('medications_details', '').strip()
        donor.has_infectious_history = bool(request.form.get('has_infectious_history'))
        donor.is_pregnant_or_nursing = bool(request.form.get('is_pregnant_or_nursing'))

        try:
            donor.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            donor.weight_kg = float(request.form.get('weight_kg', donor.weight_kg))
        except (ValueError, TypeError):
            pass

        db.session.commit()
        flash('Donor details updated successfully!', 'success')
        return redirect(url_for('donors.view_donor', id=donor.id))

    return render_template('donors/form.html', blood_groups=BLOOD_GROUPS, donor=donor)

@donors_bp.route('/<int:id>/donate', methods=['GET', 'POST'])
@login_required
@staff_required
def record_donation(id):
    donor = Donor.query.get_or_404(id)
    is_eligible, eligibility_msg = donor.is_eligible_to_donate

    if request.method == 'POST':
        force_record = request.form.get('force_override') == 'true'
        if not is_eligible and not force_record and not current_user.is_admin:
            flash(f"Cannot record donation: {eligibility_msg}", "danger")
            return redirect(url_for('donors.view_donor', id=donor.id))

        component = request.form.get('component', 'Whole Blood')
        units = int(request.form.get('units', 1))
        systolic_bp = request.form.get('systolic_bp', type=int)
        diastolic_bp = request.form.get('diastolic_bp', type=int)
        hemoglobin = request.form.get('hemoglobin_level', type=float)
        pulse = request.form.get('pulse_rate', type=int)
        remarks = request.form.get('remarks', '')
        screening_status = request.form.get('screening_status', 'Passed')

        donation_date = date.today()
        # Barcode generation
        barcode = generate_bag_barcode(donor.blood_group)

        # Shelf life: Whole Blood/RBC = 42 days, Platelets = 5 days, Plasma = 365 days
        shelf_life_days = 42
        if component == 'Platelets':
            shelf_life_days = 5
        elif component == 'Plasma':
            shelf_life_days = 365

        expiry_date = donation_date + timedelta(days=shelf_life_days)

        new_donation = Donation(
            donor_id=donor.id,
            donation_date=donation_date,
            blood_group=donor.blood_group,
            component=component,
            units=units,
            systolic_bp=systolic_bp,
            diastolic_bp=diastolic_bp,
            hemoglobin_level=hemoglobin,
            pulse_rate=pulse,
            bag_barcode=barcode,
            screening_status=screening_status,
            remarks=remarks,
            recorded_by_id=current_user.id
        )
        db.session.add(new_donation)
        db.session.flush()

        # Update donor record
        donor.last_donation_date = donation_date
        donor.total_donations = (donor.total_donations or 0) + 1

        # Add to inventory if passed screening
        if screening_status == 'Passed':
            inv_unit = BloodInventory(
                bag_barcode=barcode,
                blood_group=donor.blood_group,
                component=component,
                units=units,
                collection_date=donation_date,
                expiry_date=expiry_date,
                status='Available',
                storage_location=f"Rack {donor.blood_group.replace('+', 'Pos').replace('-', 'Neg')}",
                donation_id=new_donation.id
            )
            db.session.add(inv_unit)

        db.session.commit()
        flash(f'Donation recorded! Barcode {barcode} generated and blood unit added to inventory.', 'success')
        return redirect(url_for('donors.view_donor', id=donor.id))

    return render_template(
        'donors/record_donation.html',
        donor=donor,
        is_eligible=is_eligible,
        eligibility_msg=eligibility_msg,
        today=date.today()
    )

@donors_bp.route('/<int:id>/certificate')
@login_required
def certificate(id):
    donor = Donor.query.get_or_404(id)
    # Donors can only view their own certificate
    if current_user.role == 'donor' and (not current_user.donor_profile or current_user.donor_profile.id != donor.id):
        flash("You are not authorized to view this certificate.", "danger")
        return redirect(url_for('donor_portal.dashboard'))

    return render_template('donors/certificate.html', donor=donor, today=date.today())

@donors_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_donor(id):
    donor = Donor.query.get_or_404(id)
    name = donor.full_name
    db.session.delete(donor)
    db.session.commit()
    flash(f'Donor {name} has been removed from the database.', 'info')
    return redirect(url_for('donors.list_donors'))
