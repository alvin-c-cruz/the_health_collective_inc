from flask import Blueprint, render_template, current_app, g, request, jsonify
from datetime import datetime

from .. user import login_required
from .extensions import get_dashboard_stats, get_sorted_items
from application.extensions import ph_today, db
from .sort_order_models import ReportItemSortOrder


bp = Blueprint('dashboard', __name__, template_folder="pages")


@bp.route("/", methods=["GET"])
@login_required
def home():
    # Get date from query parameter or default to today
    as_of_date_str = request.args.get('as_of_date')

    if as_of_date_str:
        try:
            as_of_date = datetime.strptime(as_of_date_str, '%Y-%m-%d').date()
        except ValueError:
            as_of_date = ph_today()
    else:
        as_of_date = ph_today()

    context = get_dashboard_stats(as_of_date)
    context['get_sorted_items'] = get_sorted_items  # Make helper function available in template
    return render_template("dashboard/home.html", **context)


@bp.route("/about")
@login_required
def about():
    return render_template("dashboard/about.html")


@bp.route("/api/sort-order", methods=["POST"])
@login_required
def save_sort_order():
    """Save custom sort order for report line items (admin only)"""
    from flask_login import current_user

    # Only admins can save sort orders
    if not (current_user.admin or current_user.superuser):
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.get_json()
    section = data.get('section')  # e.g., 'payment_methods', 'service_demographics'
    items = data.get('items')  # List of item keys in desired order

    if not section or not items:
        return jsonify({"success": False, "error": "Missing section or items"}), 400

    try:
        # Delete existing sort orders for this section
        ReportItemSortOrder.query.filter_by(section=section).delete()

        # Save new sort orders
        for index, item_key in enumerate(items):
            sort_order = ReportItemSortOrder(
                section=section,
                item_key=item_key,
                sort_order=index
            )
            db.session.add(sort_order)

        db.session.commit()
        return jsonify({"success": True, "message": f"Sort order saved for {len(items)} items"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/sort-order/<section>", methods=["GET"])
@login_required
def get_sort_order(section):
    """Get custom sort order for a section"""
    try:
        orders = ReportItemSortOrder.query.filter_by(section=section).order_by(ReportItemSortOrder.sort_order).all()
        items = [order.item_key for order in orders]
        return jsonify({"success": True, "section": section, "items": items})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.before_app_request
def set_g():
    g.company_name = current_app.config["COMPANY_NAME"]
