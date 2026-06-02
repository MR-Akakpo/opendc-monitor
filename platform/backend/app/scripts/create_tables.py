from app.database.connection import Base, engine
from app.database.models import Equipment, Event, ActiveAlarm

def create_tables():
    Base.metadata.create_all(bind=engine)
    print('✅ PostgreSQL tables created successfully')

if __name__ == '__main__':
    create_tables()
