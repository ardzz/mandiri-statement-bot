import matplotlib.pyplot as plt

def plot_balance_over_time(transactions, output_path='cache/chart_cache/balance_over_time.png', all_time=False):
    """Plot balance over time."""
    if all_time:
        dates = [t.date for t in transactions if t.date]
        balances = [t.balance for t in transactions]
    else:
        dates = [t['date'] for t in transactions]
        balances = [t['balance'] for t in transactions]

    plt.figure(figsize=(10, 6))
    plt.plot(dates, balances, marker='o', linestyle='-', color='royalblue')
    plt.title("Balance Over Time")
    plt.xlabel("Date")
    plt.ylabel("Balance")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_incoming_vs_outgoing(transactions, output_path='cache/chart_cache/incoming_outgoing.png', all_time=False):
    """Plot incoming vs outgoing transactions."""
    if all_time:
        dates = [t.date for t in transactions if t.date]
        incoming = [t.incoming or 0 for t in transactions]
        outgoing = [t.outgoing or 0 for t in transactions]
    else:
        dates = [t['date'].strftime('%Y-%m-%d') for t in transactions]
        incoming = [t['incoming'] or 0 for t in transactions]
        outgoing = [t['outgoing'] or 0 for t in transactions]

    plt.figure(figsize=(12, 6))
    plt.bar(dates, incoming, label='Incoming', color='green')
    plt.bar(dates, outgoing, bottom=incoming, label='Outgoing', color='red')  # stacked
    plt.xticks(rotation=45, ha='right')
    plt.title("Incoming vs Outgoing")
    plt.xlabel("Date")
    plt.ylabel("Amount")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_total_incoming_outgoing(transactions, output_path='cache/chart_cache/pie_io.png', all_time=False):
    """Plot total incoming vs outgoing transactions."""
    if all_time:
        total_incoming = sum(t.incoming or 0 for t in transactions)
        total_outgoing = sum(t.outgoing or 0 for t in transactions)
    else:
        total_incoming = sum(t['incoming'] or 0 for t in transactions)
        total_outgoing = sum(t['outgoing'] or 0 for t in transactions)

    labels = ['Incoming', 'Outgoing']
    values = [total_incoming, total_outgoing]
    colors = ['green', 'red']

    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
    plt.title("Total Incoming vs Outgoing")
    plt.savefig(output_path)
    plt.close()
