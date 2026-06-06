"""
Centralized Audit Trail Module

This module provides comprehensive audit logging for all modules in the application.
Based on the proven CAS (Computerized Accounting System) pattern.

Features:
- Centralized audit log storage
- Object-level change tracking with JSON
- Login history tracking
- Audit log viewer with filtering
- Role-based access (Admin and Accountant only)
"""

app_name = "audit"
app_label = "Audit Trail"
menu_label = (app_name, f"/{app_name}/audit-log", app_label)

from flask import Blueprint

bp = Blueprint("audit", __name__, template_folder="pages", url_prefix="/audit")

from application.blueprints.audit import views
