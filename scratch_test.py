import sys
from pathlib import Path

# Add root directory to path
sys.path.append(str(Path(__file__).resolve().parent))

from src.alerts import alert_counts, generate_alerts
from src.database import count_rows, init_db
from src.delay_model import get_delivery_risk_table, load_procurement_data
from src.schedule_impact import get_schedule_impact_table, schedule_impact_summary
from src.vendor_risk import get_vendor_risk_table

print("Initializing DB...")
init_db()

print("Loading procurement data...")
data = load_procurement_data()
print("Data shape:", data.shape if data is not None else "None")

print("Getting delivery risk table...")
delivery_risk = get_delivery_risk_table()
print("Delivery risk shape:", delivery_risk.shape if delivery_risk is not None else "None")

print("Getting vendor risk table...")
vendor_risk = get_vendor_risk_table(data)
print("Vendor risk shape:", vendor_risk.shape if vendor_risk is not None else "None")

print("Getting alert counts...")
counts = alert_counts()
print("Counts:", counts)

print("Getting schedule impact table...")
impact_table = get_schedule_impact_table(data)
print("Impact table shape:", impact_table.shape if impact_table is not None else "None")

print("Getting schedule impact summary...")
summary = schedule_impact_summary(data)
print("Summary:", summary)

print("All functions completed successfully!")
