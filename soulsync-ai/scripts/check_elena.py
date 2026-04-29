import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))
from backend.memory.database import get_connection

conn = get_connection()
cur  = conn.cursor()
cur.execute("SELECT message FROM memories WHERE user_id='elena_1777021041' AND role='user' ORDER BY created_at DESC LIMIT 10")
for row in cur.fetchall():
    print(repr(row[0][:120]))
conn.close()
