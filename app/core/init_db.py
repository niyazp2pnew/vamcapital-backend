from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.user_model import User, UserRole


def init_db(db: Session) -> None:
    """Creates the master Super Admin account on initial boot."""
    admin_email = "admin@vamcapital.in"
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    if not existing_admin:
        master_admin = User(
            id="usr_admin_master",
            email=admin_email,
            hashed_password=get_password_hash("Admin@VAM2026#"),
            role=UserRole.SUPER_ADMIN,
            permissions=["*"],
            is_active=True
        )
        db.add(master_admin)
        db.commit()
        print(f" Master Super Admin created: {admin_email} (Password: Admin@VAM2026#)")