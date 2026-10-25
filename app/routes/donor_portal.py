from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date
from app import db
from app.models import Donor, Donation, DonationCamp, BloodRequest

donor_portal_bp = Blueprint('donor_portal', __name__)

@donor_portal_bp.route('/')
@login_required
def dashboard():
    donor = current_user.donor_profile
    if not donor:
        # Check if matched by email
        donor = Donor.query.filter_by(email=current_user.email).first()
        if donor:
            donor.user_id = current_user.id
            db.session.commit()

    if not donor:
        flash("No donor profile linked to this account yet.", "warning")
        return render_template('donor_portal/no_profile.html')

    is_eligible, eligibility_msg = donor.is_eligible_to_donate
    donations = donor.donations.order_by(Donation.donation_date.desc()).all()

    # Active camps today and emergency needs matching donor blood group
    active_camps = DonationCamp.query.filter_by(status='Ongoing').limit(2).all()
    matching_emergencies = BloodRequest.query.filter(
        BloodRequest.status == 'Pending',
        BloodRequest.required_blood_group == donor.blood_group,
        BloodRequest.urgency.in_(['Emergency', 'Urgent'])
    ).limit(3).all()

    return render_template(
        'donor_portal/dashboard.html',
        donor=donor,
        is_eligible=is_eligible,
        eligibility_msg=eligibility_msg,
        donations=donations,
        active_camps=active_camps,
        matching_emergencies=matching_emergencies,
        today=date.today()
    )

@donor_portal_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    donor = current_user.donor_profile or Donor.query.filter_by(email=current_user.email).first_or_404()

    if request.method == 'POST':
        donor.phone = request.form.get('phone', donor.phone).strip()
        donor.address = request.form.get('address', donor.address).strip()
        donor.city = request.form.get('city', donor.city).strip()
        donor.state = request.form.get('state', donor.state).strip()
        donor.pincode = request.form.get('pincode', donor.pincode).strip()
        try:
            donor.weight_kg = float(request.form.get('weight_kg', donor.weight_kg))
        except (ValueError, TypeError):
            pass

        db.session.commit()
        flash("Your profile information has been updated.", "success")
        return redirect(url_for('donor_portal.dashboard'))

    return render_template('donor_portal/edit_profile.html', donor=donor)
