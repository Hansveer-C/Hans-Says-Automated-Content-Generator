from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS topic_packages'))
    conn.commit()
    print('Dropped topic_packages table')
