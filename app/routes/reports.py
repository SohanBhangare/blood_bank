import csv
import io
from flask import Blueprint, render_template, Response, request
from flask_login import login_required
from app.models import Donor, Donation, BloodInventory, BloodRequest, Dispatch
from app.utils import BLOOD_GROUPS, staff_required
from datetime import date

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
@staff_required
def index():
    # Inventory breakdown
    inventory_summary = []
    total_avail = 0
    total_res = 0
    total_exp = 0
    total_disp = 0

    for bg in BLOOD_GROUPS:
        avail = BloodInventory.query.filter_by(blood_group=bg, status='Available').count()
        res = BloodInventory.query.filter_by(blood_group=bg, status='Reserved').count()
        exp = BloodInventory.query.filter_by(blood_group=bg, status='Expired').count()
        disp = BloodInventory.query.filter_by(blood_group=bg, status='Dispatched').count()

        total_avail += avail
        total_res += res
        total_exp += exp
        total_disp += disp

        inventory_summary.append({
            'group': bg,
            'available': avail,
            'reserved': res,
            'expired': exp,
            'dispatched': disp,
            'total': avail + res + exp + disp
        })

    # Request statistics
    req_total = BloodRequest.query.count()
    req_pending = BloodRequest.query.filter_by(status='Pending').count()
    req_dispatched = BloodRequest.query.filter_by(status='Dispatched').count()
    req_approved = BloodRequest.query.filter_by(status='Approved').count()
    req_rejected = BloodRequest.query.filter_by(status='Rejected').count()

    fulfillment_rate = round((req_dispatched / req_total * 100), 1) if req_total > 0 else 0

    # Donor statistics
    donor_count = Donor.query.count()
    eligible_donors = Donor.query.filter_by(status='Eligible').count()
    total_donations_logged = Donation.query.count()

    return render_template(
        'reports/index.html',
        inventory_summary=inventory_summary,
        total_avail=total_avail,
        total_res=total_res,
        total_exp=total_exp,
        total_disp=total_disp,
        req_total=req_total,
        req_pending=req_pending,
        req_dispatched=req_dispatched,
        req_approved=req_approved,
        req_rejected=req_rejected,
        fulfillment_rate=fulfillment_rate,
        donor_count=donor_count,
        eligible_donors=eligible_donors,
        total_donations_logged=total_donations_logged,
        today=date.today()
    )

@reports_bp.route('/export/inventory')
@login_required
@staff_required
def export_inventory_csv():
    units = BloodInventory.query.order_by(BloodInventory.blood_group, BloodInventory.expiry_date).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Bag Barcode', 'Blood Group', 'Component', 'Units', 'Collection Date', 'Expiry Date', 'Status', 'Storage Location'])

    for u in units:
        writer.writerow([
            u.bag_barcode, u.blood_group, u.component, u.units,
            u.collection_date.strftime('%Y-%m-%d') if u.collection_date else '',
            u.expiry_date.strftime('%Y-%m-%d') if u.expiry_date else '',
            u.status, u.storage_location
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=blood_inventory_{date.today().strftime('%Y%m%d')}.csv"}
    )

@reports_bp.route('/export/donors')
@login_required
@staff_required
def export_donors_csv():
    donors = Donor.query.order_by(Donor.first_name).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Blood Group', 'Gender', 'Phone', 'Email', 'City', 'Total Donations', 'Last Donation Date', 'Status'])

    for d in donors:
        writer.writerow([
            d.id, d.full_name, d.blood_group, d.gender, d.phone, d.email, d.city or '',
            d.total_donations or 0,
            d.last_donation_date.strftime('%Y-%m-%d') if d.last_donation_date else 'Never',
            d.status
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=donors_list_{date.today().strftime('%Y%m%d')}.csv"}
    )

@reports_bp.route('/export/requests')
@login_required
@staff_required
def export_requests_csv():
    requests_list = BloodRequest.query.order_by(BloodRequest.request_date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Request ID', 'Patient Name', 'Hospital', 'Blood Group', 'Units Requested', 'Units Allocated', 'Urgency', 'Status', 'Request Date'])

    for r in requests_list:
        writer.writerow([
            r.id, r.patient_name, r.hospital_name, r.required_blood_group,
            r.units_requested, r.units_allocated, r.urgency, r.status,
            r.request_date.strftime('%Y-%m-%d') if r.request_date else ''
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=blood_requests_{date.today().strftime('%Y%m%d')}.csv"}
    )
