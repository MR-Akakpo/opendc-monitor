from app.database.connection import engine

def test_connection():
    with engine.connect() as conn:
        print('✅ PostgreSQL connection OK')

if __name__ == '__main__':
    test_connection()
