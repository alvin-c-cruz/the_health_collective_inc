"""
Run the audit log migration
"""
from application import create_app
from application.extensions import db
from sqlalchemy import text

# Set up Flask app context
app = create_app()

with app.app_context():
    # Create audit_log table directly
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            record_type VARCHAR(50) NOT NULL,
            record_id INTEGER NOT NULL,
            action VARCHAR(50) NOT NULL,
            old_values TEXT,
            new_values TEXT,
            changed_fields TEXT,
            reason VARCHAR(500),
            notes TEXT,
            user_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL,
            ip_address VARCHAR(45),
            metadata TEXT,
            FOREIGN KEY(user_id) REFERENCES user (id)
        )
    """))

    # Create indexes
    db.session.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_audit_log_record
        ON audit_log (record_type, record_id)
    """))

    db.session.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_audit_log_user
        ON audit_log (user_id)
    """))

    db.session.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_audit_log_created_at
        ON audit_log (created_at)
    """))

    db.session.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_audit_log_action
        ON audit_log (action)
    """))

    db.session.commit()

    print("Audit log table and indexes created successfully")
