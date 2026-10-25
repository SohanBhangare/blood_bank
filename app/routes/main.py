from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import Donor, Donation, BloodInventory, BloodRequest, User, DonationCamp, Hospital
from app.utils import BLOOD_GROUPS, update_expired_inventory_units
from app.seed import seed_sample_data

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'donor':
            return redirect(url_for('donor_portal.dashboard'))
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'donor':
        return redirect(url_for('donor_portal.dashboard'))

    # Auto-update expired inventory units
    update_expired_inventory_units(db, BloodInventory)

    # Key KPI metrics
    total_available_units = BloodInventory.query.filter_by(status='Available').count()
    total_donors = Donor.query.count()
    total_donations = Donation.query.count()
    pending_requests = BloodRequest.query.filter_by(status='Pending').count()
    emergency_requests = BloodRequest.query.filter(
        BloodRequest.status == 'Pending',
        BloodRequest.urgency == 'Emergency'
    ).count()

    # Blood group stock counts
    stock_counts = {}
    critical_groups = []
    for bg in BLOOD_GROUPS:
        count = BloodInventory.query.filter_by(blood_group=bg, status='Available').count()
        stock_counts[bg] = count
        if count < 3:
            critical_groups.append({'group': bg, 'count': count})

    # Recent activities
    recent_donations = Donation.query.order_by(Donation.donation_date.desc(), Donation.id.desc()).limit(5).all()
    recent_requests = BloodRequest.query.order_by(BloodRequest.created_at.desc()).limit(5).all()

    # Expiring soon (next 7 days)
    from datetime import date, timedelta
    soon = date.today() + timedelta(days=7)
    expiring_soon_count = BloodInventory.query.filter(
        BloodInventory.status == 'Available',
        BloodInventory.expiry_date <= soon,
        BloodInventory.expiry_date >= date.today()
    ).count()

    # Ongoing camps & active nearby emergency needs
    ongoing_camps = DonationCamp.query.filter_by(status='Ongoing').limit(2).all()
    nearby_emergencies = BloodRequest.query.filter(
        BloodRequest.status.in_(['Pending', 'Partially Dispatched']),
        BloodRequest.urgency.in_(['Emergency', 'Urgent'])
    ).order_by(
        db.case((BloodRequest.urgency == 'Emergency', 1), else_=2),
        BloodRequest.request_date.desc()
    ).limit(3).all()
    total_camps = DonationCamp.query.count()
    total_hospitals = Hospital.query.count()

    return render_template(
        'dashboard.html',
        total_available_units=total_available_units,
        total_donors=total_donors,
        total_donations=total_donations,
        pending_requests=pending_requests,
        emergency_requests=emergency_requests,
        expiring_soon_count=expiring_soon_count,
        stock_counts=stock_counts,
        critical_groups=critical_groups,
        recent_donations=recent_donations,
        recent_requests=recent_requests,
        ongoing_camps=ongoing_camps,
        nearby_emergencies=nearby_emergencies,
        total_camps=total_camps,
        total_hospitals=total_hospitals,
        blood_groups=BLOOD_GROUPS
    )

@main_bp.route('/seed-demo')
@login_required
def seed_demo():
    if not current_user.is_admin:
        flash("Only an administrator can perform data seeding.", "danger")
        return redirect(url_for('main.dashboard'))

    success = seed_sample_data()
    if success:
        flash("Sample data successfully initialized! Donors, donations, inventory, and requests populated.", "success")
    else:
        flash("Database already contains data.", "info")
    return redirect(url_for('main.dashboard'))
