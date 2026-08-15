import hashlib
from sqlalchemy import select
from backend.db import Base, SessionLocal, engine
from backend.models import User

def seed():
    Base.metadata.create_all(bind=engine); db=SessionLocal()
    for username,role in [('admin','admin'),('operator','operator'),('viewer','viewer')]:
        if not db.scalar(select(User).where(User.username==username)):
            db.add(User(username=username,display_name=username,password_hash=hashlib.sha256((username+'123').encode()).hexdigest(),role=role,status='active'))
    db.commit(); db.close()
if __name__=='__main__': seed(); print('production seed complete')
