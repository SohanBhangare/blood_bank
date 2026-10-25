from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app import db
from app.models import BloodInventory
from app.utils import BLOOD_GROUPS, COMPONENTS, staff_required, update_expired_inventory_units, generate_bag_barcode

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
@login_required
@staff_required
def index():
    # Update expired units on load
    update_expired_inventory_units(db, BloodInventory)

    page = request.args.get('page', 1, type=int)
    blood_group = request.args.get('blood_group', '').strip()
    status = request.args.get('status', '').strip()
    component = request.args.get('component', '').strip()
    search = request.args.get('search', '').strip()

    # Aggregate counts by blood group for summary cards
    group_stats = {}
    for bg in BLOOD_GROUPS:
        avail = BloodInventory.query.filter_by(blood_group=bg, status='Available').count()
        reserved = BloodInventory.query.filter_by(blood_group=bg, status='Reserved').count()
        group_stats[bg] = {'available': avail, 'reserved': reserved, 'total': avail + reserved}

    query = BloodInventory.query

    if blood_group:
        query = query.filter_by(blood_group=blood_group)
    if status:
        query = query.filter_by(status=status)
    if component:
        query = query.filter_by(component=component)
    if search:
        query = query.filter(
            (BloodInventory.bag_barcode.ilike(f'%{search}%')) |
            (BloodInventory.storage_location.ilike(f'%{search}%'))
        )

    pagination = query.order_by(BloodInventory.expiry_date.asc()).paginate(page=page, per_page=12, error_out=False)
    units = pagination.items

    return render_template(
        'inventory/index.html',
        units=units,
        pagination=pagination,
        group_stats=group_stats,
        blood_groups=BLOOD_GROUPS,
        components=COMPONENTS,
        selected_bg=blood_group,
        selected_status=status,
        selected_component=component,
        search=search,
        today=date.today()
    )

@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
@staff_required
def add_unit():
    if request.method == 'POST':
        blood_group = request.form.get('blood_group')
        component = request.form.get('component', 'Whole Blood')
        units = int(request.form.get('units', 1))
        collection_date_str = request.form.get('collection_date')
        storage_location = request.form.get('storage_location', 'Cold Storage')
        notes = request.form.get('notes', '')

        try:
            coll_date = datetime.strptime(collection_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            coll_date = date.today()

        shelf_life = 42
        if component == 'Platelets':
            shelf_life = 5
        elif component == 'Plasma':
            shelf_life = 365

        expiry_date = coll_date + timedelta(days=shelf_life)
        barcode = generate_bag_barcode(blood_group)

        unit = BloodInventory(
            bag_barcode=barcode,
            blood_group=blood_group,
            component=component,
            units=units,
            collection_date=coll_date,
            expiry_date=expiry_date,
            status='Available',
            storage_location=storage_location,
            notes=notes
        )
        db.session.add(unit)
        db.session.commit()

        flash(f'New blood bag [{barcode}] successfully cataloged in inventory.', 'success')
        return redirect(url_for('inventory.index'))

    return render_template('inventory/add.html', blood_groups=BLOOD_GROUPS, components=COMPONENTS, today=date.today())

@inventory_bp.route('/<int:id>/discard', methods=['POST'])
@login_required
@staff_required
def discard_unit(id):
    unit = BloodInventory.query.get_or_404(id)
    unit.status = 'Discarded'
    db.session.commit()
    flash(f'Unit {unit.bag_barcode} marked as Discarded.', 'warning')
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/check-expired')
@login_required
@staff_required
def check_expired():
    count = update_expired_inventory_units(db, BloodInventory)
    flash(f'{count} inventory unit(s) checked and updated to Expired status.', 'info')
    return redirect(url_for('inventory.index'))
