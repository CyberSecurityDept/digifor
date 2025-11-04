from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.db.session import SessionLocal
from app.auth.models import User  # sesuaikan path model User kamu

# Inisialisasi password hasher (pakai bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash password dengan bcrypt."""
    return pwd_context.hash(password)


def seed_users():
    """Seeder untuk memastikan akun admin dan user default ada di database."""
    db: Session = SessionLocal()
    try:
        users_to_seed = [
            {
                "email": "admin@gmail.com",
                "fullname": "Admin Forensic",
                "password": "admin.admin",
                "role": "admin",
                "tag":"Admin"
            },
            {
                "email": "investigator@gmail.com",
                "fullname": "Ivestigator",
                "password": "admin.admin",
                "role": "user",
                "tag":"Investigator"
            },
            {
                "email": "ahliforensic@gmail.com",
                "fullname": "Ahli Forensic",
                "password": "admin.admin",
                "role": "user",
                "tag":"Ahli Forensic"
            },
        ]

        for u in users_to_seed:
            existing_user = db.query(User).filter(User.email == u["email"]).first()
            if existing_user:
                print(f"✅ User '{u['email']}' sudah ada, skip insert.")
            else:
                hashed_pw = get_password_hash(u["password"])
                new_user = User(
                    email=u["email"],
                    fullname=u["fullname"],
                    hashed_password=hashed_pw,
                    role=u["role"],
                    is_active=True,
                    tag=u["tag"]
                )
                db.add(new_user)
                print(f"🎉 User '{u['email']}' berhasil ditambahkan ({u['role']}).")

        db.commit()
        print("✅ Seeder user selesai.")
    except Exception as e:
        db.rollback()
        print(f"❌ Gagal menambahkan user: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
