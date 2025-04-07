import os
import matplotlib.pyplot as plt


def visualize_transactions(transactions, user_id):
    """Visualizes transactions with line and bar charts."""
    transactions.sort(key=lambda x: x['datetime'])

    dates = [tx['datetime'] for tx in transactions]
    balance = [tx['balance'] for tx in transactions]
    incoming = [tx['incoming'] or 0 for tx in transactions]
    outgoing = [tx['outgoing'] or 0 for tx in transactions]

    # Create directory if not exists
    os.makedirs("cache/chart_cache", exist_ok=True)

    # Line chart - Balance over time
    plt.figure(figsize=(10, 5))
    plt.plot(dates, balance, marker='o', linestyle='-', color='blue')
    plt.title("Balance Over Time")
    plt.xlabel("Date")
    plt.ylabel("Balance")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"cache/chart_cache/{user_id}_balance_line.png")
    plt.close()

    # Bar chart - Incoming vs Outgoing
    plt.figure(figsize=(10, 5))
    plt.bar(dates, incoming, color='green', label='Incoming')
    plt.bar(dates, [-val for val in outgoing], color='red', label='Outgoing', alpha=0.7)
    plt.title("Incoming vs Outgoing")
    plt.xlabel("Date")
    plt.ylabel("Amount")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"cache/chart_cache/{user_id}_bar.png")
    plt.close()
