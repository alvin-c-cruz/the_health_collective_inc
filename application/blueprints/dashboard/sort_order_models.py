"""
Sort Order Models

Stores custom sort orders for dashboard report line items.
Allows admins to rearrange items via drag-and-drop and persist the order for all users.
"""
from application.extensions import db


class ReportItemSortOrder(db.Model):
    """
    Stores custom sort order for report line items (tenders, product types, etc.)

    Usage:
    - section: 'payment_methods', 'service_demographics', etc.
    - item_key: The unique identifier for the item (e.g., tender name, product type name)
    - sort_order: Integer representing display order (lower numbers appear first)
    """
    __tablename__ = "report_item_sort_order"

    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(50), nullable=False, index=True)  # 'payment_methods', 'service_demographics'
    item_key = db.Column(db.String(200), nullable=False)  # Tender name, product type name, etc.
    sort_order = db.Column(db.Integer, nullable=False, default=999)  # Lower = appears first

    # Ensure each item appears only once per section
    __table_args__ = (
        db.UniqueConstraint('section', 'item_key', name='uq_section_item'),
    )

    def __repr__(self):
        return f'<ReportItemSortOrder {self.section}:{self.item_key} order={self.sort_order}>'
