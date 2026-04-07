from datetime import datetime
current_date = datetime.now().strftime("%Y.%m.%d")
current_month = datetime.now().strftime("%Y.%m")
print(f"current date: {current_date}")
print(f"current month: {current_month}")