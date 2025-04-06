import matplotlib.pyplot as plt
from collections import defaultdict
import os

def generate_pie_chart(transactions, user_id):
    category_totals = defaultdict(float)
    for tx in transactions:
        if tx['amount'] < 0:  # Only expenses
            category_totals[tx['category']] += abs(tx['amount'])

    labels = category_totals.keys()
    sizes = category_totals.values()

    plt.figure(figsize=(6,6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%')
    plt.title("Expense Breakdown")

    path = f"cache/chart_cache/{user_id}_pie.png"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path)
    plt.close()
