from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.notification import Notification
from app import db

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/notifications')
@login_required
def list():
    """Display user's notifications."""
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .all()
    return render_template('notification/list.html', notifications=notifications)

@notification_bp.route('/notifications/<int:notification_id>/read')
@login_required
def mark_read(notification_id):
    """Mark a specific notification as read."""
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        flash('You do not have permission to modify this notification.', 'error')
        return redirect(url_for('notification.list'))
    
    notification.mark_as_read()
    db.session.commit()
    return redirect(url_for('notification.list'))

@notification_bp.route('/notifications/mark-all-read')
@login_required
def mark_all_read():
    """Mark all notifications as read."""
    Notification.mark_all_read(current_user.id)
    db.session.commit()
    return redirect(url_for('notification.list'))

@notification_bp.route('/notifications/clear-all')
@login_required
def clear_all():
    """Delete all notifications for the current user."""
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return redirect(url_for('notification.list'))

@notification_bp.route('/notifications/count')
@login_required
def get_unread_count():
    """Get the count of unread notifications."""
    count = Notification.get_unread_count(current_user.id)
    return {'count': count} 