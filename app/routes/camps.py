from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from app.models import DonationCamp
from app.utils import staff_required, validate_phone

camps_bp = Blueprint('camps', __name__)

@camps_bp.route('/')
def index():
    city = request.args.get('city', '').strip()
    status = request.args.get('status', '').strip()

    today = date.today()
    query = DonationCamp.query

    if city:
        query = query.filter(DonationCamp.city.ilike(f'%{city}%'))
    if status:
        query = query.filter_by(status=status)

    # Sort ongoing camps first, then upcoming, then date
    camps = query.order_by(
        db.case(
            (DonationCamp.status == 'Ongoing', 1),
            (DonationCamp.status == 'Upcoming', 2),
            else_=3
        ),
        DonationCamp.start_date.asc()
    ).all()

    # Distinct cities for dropdown
    cities = [r[0] for r in db.session.query(DonationCamp.city).distinct().all() if r[0]]

    return render_template(
        'camps/index.html',
        camps=camps,
        selected_city=city,
        selected_status=status,
        cities=cities,
        today=today
    )

@camps_bp.route('/add', methods=['GET', 'POST'])
@login_required
@staff_required
def add_camp():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        organizer = request.form.get('organizer', '').strip()
        venue = request.form.get('venue', '').strip()
        city = request.form.get('city', 'Pune').strip()
        state = request.form.get('state', 'Maharashtra').strip()
        pincode = request.form.get('pincode', '').strip()
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        operating_hours = request.form.get('operating_hours', '09:00 AM - 05:00 PM')
        contact_person = request.form.get('contact_person', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()

        is_phone_valid, clean_phone = validate_phone(contact_phone)
        if not is_phone_valid:
            flash('Contact phone number must be exactly 10 digits (e.g. 9876543210).', 'danger')
            return render_template('camps/form.html', today=date.today())
        contact_phone = clean_phone

        target_units = int(request.form.get('target_units', 100))
        facilities = request.form.get('facilities', '')

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Invalid date range specified.', 'danger')
            return render_template('camps/form.html', today=date.today())

        today = date.today()
        status = 'Ongoing' if start_date <= today <= end_date else ('Upcoming' if start_date > today else 'Completed')

        camp = DonationCamp(
            name=name,
            organizer=organizer,
            venue=venue,
            city=city,
            state=state,
            pincode=pincode,
            start_date=start_date,
            end_date=end_date,
            operating_hours=operating_hours,
            contact_person=contact_person,
            contact_phone=contact_phone,
            target_units=target_units,
            collected_units=0,
            status=status,
            facilities=facilities
        )
        db.session.add(camp)
        db.session.commit()

        flash(f'Donation Camp "{name}" scheduled successfully!', 'success')
        return redirect(url_for('camps.index'))

    return render_template('camps/form.html', today=date.today())

@camps_bp.route('/<int:id>/rsvp', methods=['POST'])
@login_required
def rsvp_camp(id):
    camp = DonationCamp.query.get_or_404(id)
    donor_name = current_user.full_name or current_user.username
    flash(f'Thank you {donor_name}! You have pledged to donate at "{camp.name}". A reminder has been set.', 'success')
    return redirect(url_for('camps.index'))
