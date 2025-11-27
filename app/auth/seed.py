import warnings
warnings.filterwarnings('ignore', message='.*bcrypt.*')
warnings.filterwarnings('ignore', message='.*error reading bcrypt.*')

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.db.session import SessionLocal
from app.auth.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def seed_users():
    db: Session = SessionLocal()
    try:
        users_to_seed = [
            {
                "email": "admin@gmail.com",
                "fullname": "Admin Forensic",
                "password": "admin.admin",
                "role": "admin",
                "tag":"Admin"
            }
        ]

        for u in users_to_seed:
            existing_user = db.query(User).filter(User.email == u["email"]).first()
            if existing_user:
                hashed_pw = get_password_hash(u["password"])
                setattr(existing_user, 'password', u["password"])
                setattr(existing_user, 'hashed_password', hashed_pw)
                setattr(existing_user, 'is_active', True)
                db.add(existing_user)
                print(f"User '{u['email']}' sudah ada, password di-update.")
            else:
                hashed_pw = get_password_hash(u["password"])
                new_user = User(
                    email=u["email"],
                    fullname=u["fullname"],
                    password=u["password"],
                    hashed_password=hashed_pw,
                    role=u["role"],
                    is_active=True,
                    tag=u["tag"]
                )
                db.add(new_user)
                print(f"User '{u['email']}' berhasil ditambahkan ({u['role']}).")

        db.commit()
        print("Seeder user selesai.")
    except Exception as e:
        db.rollback()
        print(f"Gagal menambahkan user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
