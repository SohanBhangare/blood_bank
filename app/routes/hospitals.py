from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Hospital, BloodRequest
from app.utils import staff_required

hospitals_bp = Blueprint('hospitals', __name__)

@hospitals_bp.route('/')
def index():
    city = request.args.get('city', '').strip()
    search = request.args.get('search', '').strip()
    accepts_only = request.args.get('accepts_donations') == 'true'

    query = Hospital.query

    if city:
        query = query.filter(Hospital.city.ilike(f'%{city}%'))
    if search:
        query = query.filter(
            (Hospital.name.ilike(f'%{search}%')) |
            (Hospital.address.ilike(f'%{search}%')) |
            (Hospital.hospital_type.ilike(f'%{search}%'))
        )
    if accepts_only:
        query = query.filter_by(accepts_donations=True)

    hospitals = query.order_by(Hospital.name.asc()).all()
    cities = [r[0] for r in db.session.query(Hospital.city).distinct().all() if r[0]]

    return render_template(
        'hospitals/index.html',
        hospitals=hospitals,
        cities=cities,
        selected_city=city,
        search=search,
        accepts_only=accepts_only
    )

@hospitals_bp.route('/emergency')
def emergency_feed():
    city = request.args.get('city', '').strip()
    blood_group = request.args.get('blood_group', '').strip()

    # Query all pending emergency and urgent blood requests from hospitals
    query = BloodRequest.query.filter(
        BloodRequest.status.in_(['Pending', 'Partially Dispatched']),
        BloodRequest.urgency.in_(['Emergency', 'Urgent'])
    )

    if city:
        query = query.filter(BloodRequest.city.ilike(f'%{city}%'))
    if blood_group:
        query = query.filter_by(required_blood_group=blood_group)

    # Emergency requests first, then earliest date
    urgent_requests = query.order_by(
        db.case((BloodRequest.urgency == 'Emergency', 1), else_=2),
        BloodRequest.request_date.desc(),
        BloodRequest.id.desc()
    ).all()

    cities = [r[0] for r in db.session.query(BloodRequest.city).distinct().all() if r[0]]

    return render_template(
        'hospitals/emergency.html',
        urgent_requests=urgent_requests,
        selected_city=city,
        selected_bg=blood_group,
        cities=cities
    )

@hospitals_bp.route('/add', methods=['GET', 'POST'])
@login_required
@staff_required
def add_hospital():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        hospital_type = request.form.get('hospital_type', 'Multi-Specialty')
        address = request.form.get('address', '').strip()
        city = request.form.get('city', 'Pune').strip()
        state = request.form.get('state', 'Maharashtra').strip()
        pincode = request.form.get('pincode', '').strip()
        phone = request.form.get('phone', '').strip()
        emergency_helpline = request.form.get('emergency_helpline', '').strip()
        accepts_donations = bool(request.form.get('accepts_donations'))
        blood_bank_inhouse = bool(request.form.get('blood_bank_inhouse'))
        blood_groups_accepted = request.form.get('blood_groups_accepted', 'All Blood Groups')
        urgent_requirements = request.form.get('urgent_requirements', '')
        timing = request.form.get('timing', '24x7 Emergency Blood Bank')

        hospital = Hospital(
            name=name,
            hospital_type=hospital_type,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            phone=phone,
            emergency_helpline=emergency_helpline,
            accepts_donations=accepts_donations,
            blood_bank_inhouse=blood_bank_inhouse,
            blood_groups_accepted=blood_groups_accepted,
            urgent_requirements=urgent_requirements,
            timing=timing
        )
        db.session.add(hospital)
        db.session.commit()

        flash(f'Hospital "{name}" registered in the healthcare network!', 'success')
        return redirect(url_for('hospitals.index'))

    return render_template('hospitals/form.html')
