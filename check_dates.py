#!/usr/bin/env python3
"""Check dates in database"""

import sqlite3
from datetime import datetime

conn = sqlite3.connect('energy_monitor.db')
cursor = conn.cursor()

cursor.execute("SELECT MIN(date(timestamp)) as min_date, MAX(date(timestamp)) as max_date FROM energy_readings")
result = cursor.fetchone()
print(f"Date range: {result[0]} to {result[1]}")

cursor.execute("SELECT date(timestamp) as date, COUNT(*) as count FROM energy_readings GROUP BY date(timestamp) ORDER BY date DESC LIMIT 10")
dates = cursor.fetchall()
print("\nRecent dates:")
for date, count in dates:
    print(f"  {date}: {count} readings")

print(f"\nToday is: {datetime.now().strftime('%Y-%m-%d')}")

conn.close()