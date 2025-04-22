from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Alert, Category

alert_bp = Blueprint('alert', __name__, url_prefix='/alert')

@alert_bp.route('/manage')
@login_required
def manage():
    # Get all alerts for the current user
    alerts = Alert.query.filter_by(user_id=current_user.id).all()
    
    # Get all categories for the dropdown
    categories = Category.query.all()
    
    return render_template('alert/manage.html', alerts=alerts, categories=categories)

@alert_bp.route('/create', methods=['POST'])
@login_required
def create():
    # Get form data
    keywords = request.form.get('keywords')
    category_id = request.form.get('category_id')
    min_price = request.form.get('min_price', type=float)
    max_price = request.form.get('max_price', type=float)
    
    # Validate input (at least one criterion must be specified)
    if not any([keywords, category_id, min_price is not None, max_price is not None]):
        flash('Please specify at least one criterion for your alert', 'danger')
        return redirect(url_for('alert.manage'))
    
    # Convert empty strings to None
    if category_id == '':
        category_id = None
    
    # Create the alert
    alert = Alert(
        user_id=current_user.id,
        keywords=keywords,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price
    )
    
    db.session.add(alert)
    db.session.commit()
    
    flash('Alert created successfully', 'success')
    return redirect(url_for('alert.manage'))

@alert_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    alert = Alert.query.get_or_404(id)
    
    # Check if the alert belongs to the current user
    if alert.user_id != current_user.id:
        flash('You are not authorized to delete this alert', 'danger')
        return redirect(url_for('alert.manage'))
    
    db.session.delete(alert)
    db.session.commit()
    
    flash('Alert deleted successfully', 'success')
    return redirect(url_for('alert.manage'))

@alert_bp.route('/toggle/<int:id>')
@login_required
def toggle(id):
    alert = Alert.query.get_or_404(id)
    
    # Check if the alert belongs to the current user
    if alert.user_id != current_user.id:
        flash('You are not authorized to modify this alert', 'danger')
        return redirect(url_for('alert.manage'))
    
    # Toggle the active status
    alert.is_active = not alert.is_active
    db.session.commit()
    
    status = 'activated' if alert.is_active else 'deactivated'
    flash(f'Alert {status} successfully', 'success')
    return redirect(url_for('alert.manage'))