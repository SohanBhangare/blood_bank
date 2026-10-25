from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from app.models import BloodRequest, BloodInventory, Dispatch
from app.utils import (
    BLOOD_GROUPS, COMPONENTS, staff_required,
    get_compatible_donors_for_recipient, validate_phone
)

requests_bp = Blueprint('requests', __name__)

@requests_bp.route('/')
@login_required
@staff_required
def list_requests():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '').strip()
    urgency = request.args.get('urgency', '').strip()
    blood_group = request.args.get('blood_group', '').strip()
    search = request.args.get('search', '').strip()

    query = BloodRequest.query

    if status:
        query = query.filter_by(status=status)
    if urgency:
        query = query.filter_by(urgency=urgency)
    if blood_group:
        query = query.filter_by(required_blood_group=blood_group)
    if search:
        query = query.filter(
            (BloodRequest.patient_name.ilike(f'%{search}%')) |
            (BloodRequest.hospital_name.ilike(f'%{search}%')) |
            (BloodRequest.doctor_name.ilike(f'%{search}%'))
        )

    # Order emergency first, then urgent, then date
    pagination = query.order_by(
        db.case(
            (BloodRequest.urgency == 'Emergency', 1),
            (BloodRequest.urgency == 'Urgent', 2),
            else_=3
        ),
        BloodRequest.request_date.desc(),
        BloodRequest.id.desc()
    ).paginate(page=page, per_page=10, error_out=False)

    requests_list = pagination.items

    return render_template(
        'requests/list.html',
        requests=requests_list,
        pagination=pagination,
        selected_status=status,
        selected_urgency=urgency,
        selected_bg=blood_group,
        search=search,
        blood_groups=BLOOD_GROUPS
    )

@requests_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_request():
    if request.method == 'POST':
        patient_name = request.form.get('patient_name', '').strip()
        patient_age = request.form.get('patient_age', type=int)
        patient_gender = request.form.get('patient_gender', '')
        hospital_name = request.form.get('hospital_name', '').strip()
        hospital_contact = request.form.get('hospital_contact', '').strip()
        doctor_name = request.form.get('doctor_name', '').strip()
        required_blood_group = request.form.get('required_blood_group', '')
        component = request.form.get('component', 'Whole Blood')
        units_requested = int(request.form.get('units_requested', 1))
        urgency = request.form.get('urgency', 'Normal')
        diagnosis_reason = request.form.get('diagnosis_reason', '')
        contact_person = request.form.get('contact_person', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()

        is_phone_valid, clean_phone = validate_phone(contact_phone)
        if not is_phone_valid:
            flash('Contact phone must be exactly 10 digits (e.g. 9876543210).', 'danger')
            return render_template(
                'requests/form.html',
                blood_groups=BLOOD_GROUPS,
                components=COMPONENTS,
                today=date.today()
            )
        contact_phone = clean_phone

        required_by_date_str = request.form.get('required_by_date', '')

        required_by = None
        if required_by_date_str:
            try:
                required_by = datetime.strptime(required_by_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        blood_req = BloodRequest(
            patient_name=patient_name,
            patient_age=patient_age,
            patient_gender=patient_gender,
            hospital_name=hospital_name,
            hospital_contact=hospital_contact,
            doctor_name=doctor_name,
            required_blood_group=required_blood_group,
            component=component,
            units_requested=units_requested,
            units_allocated=0,
            urgency=urgency,
            diagnosis_reason=diagnosis_reason,
            contact_person=contact_person,
            contact_phone=contact_phone,
            status='Pending',
            request_date=date.today(),
            required_by_date=required_by,
            created_by_id=current_user.id
        )
        db.session.add(blood_req)
        db.session.commit()

        flash(f'Blood Request #{blood_req.id} created successfully for {patient_name} ({required_blood_group})!', 'success')
        return redirect(url_for('requests.view_request', id=blood_req.id))

    return render_template(
        'requests/form.html',
        blood_groups=BLOOD_GROUPS,
        components=COMPONENTS,
        today=date.today()
    )

@requests_bp.route('/<int:id>')
@login_required
def view_request(id):
    blood_req = BloodRequest.query.get_or_404(id)

    # Compatible blood groups for this recipient
    compatible_groups = get_compatible_donors_for_recipient(blood_req.required_blood_group)

    # Available units in stock that are compatible
    available_compatible_units = BloodInventory.query.filter(
        BloodInventory.blood_group.in_(compatible_groups),
        BloodInventory.status == 'Available',
        BloodInventory.expiry_date >= date.today()
    ).order_by(
        # Exact blood group first, then earliest expiry
        db.case((BloodInventory.blood_group == blood_req.required_blood_group, 1), else_=2),
        BloodInventory.expiry_date.asc()
    ).all()

    # Units currently reserved for this request
    allocated_units = BloodInventory.query.filter_by(
        request_id=blood_req.id
    ).all()

    # Dispatches
    dispatches = blood_req.dispatches.all()

    return render_template(
        'requests/view.html',
        req=blood_req,
        compatible_groups=compatible_groups,
        available_units=available_compatible_units,
        allocated_units=allocated_units,
        dispatches=dispatches
    )

@requests_bp.route('/<int:id>/allocate-unit/<int:unit_id>', methods=['POST'])
@login_required
@staff_required
def allocate_unit(id, unit_id):
    blood_req = BloodRequest.query.get_or_404(id)
    unit = BloodInventory.query.get_or_404(unit_id)

    if blood_req.units_allocated >= blood_req.units_requested:
        flash('This request has already reached its requested units capacity.', 'warning')
        return redirect(url_for('requests.view_request', id=blood_req.id))

    if unit.status != 'Available':
        flash('This blood unit is no longer available.', 'danger')
        return redirect(url_for('requests.view_request', id=blood_req.id))

    unit.status = 'Reserved'
    unit.request_id = blood_req.id
    blood_req.units_allocated += 1
    if blood_req.units_allocated == blood_req.units_requested:
        blood_req.status = 'Approved'
    else:
        blood_req.status = 'Partially Dispatched' if blood_req.status == 'Dispatched' else 'Approved'

    db.session.commit()
    flash(f'Unit {unit.bag_barcode} ({unit.blood_group}) successfully allocated to Request #{blood_req.id}.', 'success')
    return redirect(url_for('requests.view_request', id=blood_req.id))

@requests_bp.route('/<int:id>/unallocate-unit/<int:unit_id>', methods=['POST'])
@login_required
@staff_required
def unallocate_unit(id, unit_id):
    blood_req = BloodRequest.query.get_or_404(id)
    unit = BloodInventory.query.get_or_404(unit_id)

    if unit.request_id == blood_req.id and unit.status == 'Reserved':
        unit.status = 'Available'
        unit.request_id = None
        blood_req.units_allocated = max(0, blood_req.units_allocated - 1)
        if blood_req.units_allocated == 0:
            blood_req.status = 'Pending'
        db.session.commit()
        flash(f'Unit {unit.bag_barcode} unallocated and returned to available stock.', 'info')

    return redirect(url_for('requests.view_request', id=blood_req.id))

@requests_bp.route('/<int:id>/dispatch', methods=['POST'])
@login_required
@staff_required
def dispatch_request(id):
    blood_req = BloodRequest.query.get_or_404(id)
    recipient_name = request.form.get('recipient_name', '').strip() or blood_req.contact_person
    dispatch_notes = request.form.get('dispatch_notes', '')

    reserved_units = BloodInventory.query.filter_by(
        request_id=blood_req.id,
        status='Reserved'
    ).all()

    if not reserved_units:
        flash('No reserved units available to dispatch. Please allocate units first.', 'danger')
        return redirect(url_for('requests.view_request', id=blood_req.id))

    for unit in reserved_units:
        unit.status = 'Dispatched'
        dispatch_entry = Dispatch(
            request_id=blood_req.id,
            inventory_id=unit.id,
            dispatch_date=datetime.utcnow(),
            dispatched_by_id=current_user.id,
            recipient_name=recipient_name,
            notes=dispatch_notes
        )
        db.session.add(dispatch_entry)

    blood_req.status = 'Dispatched'
    db.session.commit()

    flash(f'{len(reserved_units)} unit(s) dispatched to {blood_req.hospital_name} for patient {blood_req.patient_name}!', 'success')
    return redirect(url_for('requests.view_request', id=blood_req.id))

@requests_bp.route('/<int:id>/reject', methods=['POST'])
@login_required
@staff_required
def reject_request(id):
    blood_req = BloodRequest.query.get_or_404(id)
    reason = request.form.get('rejection_reason', 'Stock unavailability or administrative reasons.')

    # Unreserve any allocated units
    allocated = BloodInventory.query.filter_by(request_id=blood_req.id, status='Reserved').all()
    for u in allocated:
        u.status = 'Available'
        u.request_id = None

    blood_req.status = 'Rejected'
    blood_req.units_allocated = 0
    blood_req.rejection_reason = reason
    db.session.commit()

    flash(f'Request #{blood_req.id} has been marked as Rejected.', 'warning')
    return redirect(url_for('requests.view_request', id=blood_req.id))
