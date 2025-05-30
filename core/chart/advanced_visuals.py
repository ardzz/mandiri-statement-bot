from collections import defaultdict
from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def plot_category_trends(transactions, output_path='cache/chart_cache/category_trends.png'):
    """Plot spending trends by category over time with improved categorization."""
    if not transactions:
        return

    # Group by category and month
    category_data = defaultdict(lambda: defaultdict(float))

    for t in transactions:
        date = t.date if hasattr(t, 'date') else t['date']
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')

        month_key = date.strftime('%Y-%m')
        outgoing = abs(t.outgoing or 0) if hasattr(t, 'outgoing') else abs(t['outgoing'] or 0)

        # Improved category detection
        category = "Uncategorized"

        if hasattr(t, 'category') and t.category:
            category = t.category.name if hasattr(t.category, 'name') else str(t.category)
        elif hasattr(t, 'category_id') and t.category_id:
            # Try to get category from database
            try:
                from core.database import Session, Category
                session = Session()
                cat_obj = session.query(Category).filter(Category.id == t.category_id).first()
                if cat_obj:
                    category = cat_obj.name
                session.close()
            except:
                pass
        else:
            # Try auto-categorization based on description
            if hasattr(t, 'description') and t.description:
                from core.services.categorization_service import CategorizationService
                cat_service = CategorizationService()
                auto_cat = cat_service.categorize_transaction(t.description)
                if auto_cat:
                    category = auto_cat['category_name']

        category_data[category][month_key] += outgoing

    # Create plot
    fig, ax = plt.subplots(figsize=(14, 8))

    months = sorted(set(month for cat_data in category_data.values() for month in cat_data.keys()))

    # Plot top 5 categories (excluding Uncategorized if there are other categories)
    sorted_categories = sorted(category_data.items(),
                               key=lambda x: sum(x[1].values()),
                               reverse=True)

    # If we have categorized data, exclude "Uncategorized" from top 5
    if len([cat for cat, _ in sorted_categories if cat != "Uncategorized"]) >= 5:
        top_categories = [cat_data for cat_data in sorted_categories if cat_data[0] != "Uncategorized"][:5]
    else:
        top_categories = sorted_categories[:5]

    colors = plt.cm.Set3(np.linspace(0, 1, len(top_categories)))

    for i, (category, data) in enumerate(top_categories):
        values = [data.get(month, 0) for month in months]
        month_dates = [datetime.strptime(month, '%Y-%m') for month in months]
        ax.plot(month_dates, values, marker='o', linewidth=2,
                label=category, color=colors[i])

    ax.set_title('Spending Trends by Category')
    ax.set_ylabel('Amount (IDR)')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)

    # Add summary text
    total_categories = len(category_data)
    categorized_amount = sum(sum(data.values()) for cat, data in category_data.items() if cat != "Uncategorized")
    uncategorized_amount = sum(category_data.get("Uncategorized", {}).values())

    summary_text = f"Total Categories: {total_categories}"
    if uncategorized_amount > 0:
        summary_text += f"\nUncategorized: {uncategorized_amount:,.0f} IDR"

    ax.text(0.02, 0.98, summary_text, transform=ax.transAxes,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def plot_spending_trends(transactions, output_path='cache/chart_cache/spending_trends.png', period='monthly'):
    """Plot spending trends over time with moving averages."""
    if not transactions:
        return

    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame([{
        'date': t.date if hasattr(t, 'date') else t['date'],
        'outgoing': abs(t.outgoing or 0) if hasattr(t, 'outgoing') else abs(t['outgoing'] or 0),
        'incoming': t.incoming or 0 if hasattr(t, 'incoming') else t['incoming'] or 0
    } for t in transactions])

    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    if period == 'daily':
        # Daily spending with 7-day moving average
        daily_spending = df.groupby(df['date'].dt.date)['outgoing'].sum()
        daily_spending.index = pd.to_datetime(daily_spending.index)

        ax1.plot(daily_spending.index, daily_spending.values, alpha=0.7, label='Daily Spending')

        # 7-day moving average
        if len(daily_spending) >= 7:
            ma_7 = daily_spending.rolling(window=7).mean()
            ax1.plot(ma_7.index, ma_7.values, color='red', linewidth=2, label='7-Day Average')

        ax1.set_title('Daily Spending Trends')
        ax1.set_ylabel('Amount (IDR)')

    elif period == 'weekly':
        # Weekly spending
        df['week'] = df['date'].dt.to_period('W')
        weekly_spending = df.groupby('week')['outgoing'].sum()
        weekly_dates = [week.start_time for week in weekly_spending.index]

        ax1.bar(weekly_dates, weekly_spending.values, alpha=0.7, label='Weekly Spending')
        ax1.set_title('Weekly Spending Trends')
        ax1.set_ylabel('Amount (IDR)')

    else:  # monthly
        # Monthly spending
        df['month'] = df['date'].dt.to_period('M')
        monthly_spending = df.groupby('month')['outgoing'].sum()
        monthly_income = df.groupby('month')['incoming'].sum()

        months = [month.start_time for month in monthly_spending.index]

        ax1.bar(months, monthly_spending.values, alpha=0.7, label='Monthly Spending', color='red')
        ax1.bar(months, monthly_income.values, alpha=0.7, label='Monthly Income', color='green')
        ax1.set_title('Monthly Financial Overview')
        ax1.set_ylabel('Amount (IDR)')

    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Spending velocity (second subplot)
    if len(df) > 1:
        df['cumulative_spending'] = df['outgoing'].cumsum()
        df['days_from_start'] = (df['date'] - df['date'].min()).dt.days

        ax2.plot(df['date'], df['cumulative_spending'], color='orange', linewidth=2)
        ax2.set_title('Cumulative Spending Over Time')
        ax2.set_ylabel('Cumulative Amount (IDR)')
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_category_trends(transactions, output_path='cache/chart_cache/category_trends.png'):
    """Plot spending trends by category over time."""
    if not transactions:
        return

    # Group by category and month
    category_data = defaultdict(lambda: defaultdict(float))

    for t in transactions:
        date = t.date if hasattr(t, 'date') else t['date']
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')

        month_key = date.strftime('%Y-%m')
        outgoing = abs(t.outgoing or 0) if hasattr(t, 'outgoing') else abs(t['outgoing'] or 0)

        # Get category name (you might need to implement category lookup)
        category = "Unknown"  # Default category
        if hasattr(t, 'category') and t.category:
            category = t.category.name if hasattr(t.category, 'name') else str(t.category)

        category_data[category][month_key] += outgoing

    # Create plot
    fig, ax = plt.subplots(figsize=(14, 8))

    months = sorted(set(month for cat_data in category_data.values() for month in cat_data.keys()))

    # Plot top 5 categories
    top_categories = sorted(category_data.items(),
                            key=lambda x: sum(x[1].values()),
                            reverse=True)[:5]

    colors = plt.cm.Set3(np.linspace(0, 1, len(top_categories)))

    for i, (category, data) in enumerate(top_categories):
        values = [data.get(month, 0) for month in months]
        month_dates = [datetime.strptime(month, '%Y-%m') for month in months]
        ax.plot(month_dates, values, marker='o', linewidth=2,
                label=category, color=colors[i])

    ax.set_title('Spending Trends by Category')
    ax.set_ylabel('Amount (IDR)')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_spending_heatmap(transactions, output_path='cache/chart_cache/spending_heatmap.png'):
    """Create a calendar heatmap showing spending intensity by day."""
    if not transactions:
        return

    # Prepare data
    daily_spending = defaultdict(float)

    for t in transactions:
        date = t.date if hasattr(t, 'date') else t['date']
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        elif isinstance(date, datetime):
            date = date.date()

        outgoing = abs(t.outgoing or 0) if hasattr(t, 'outgoing') else abs(t['outgoing'] or 0)
        daily_spending[date] += outgoing

    if not daily_spending:
        return

    # Create calendar matrix
    min_date = min(daily_spending.keys())
    max_date = max(daily_spending.keys())

    # Get full date range
    current_date = min_date
    calendar_data = []

    while current_date <= max_date:
        spending = daily_spending.get(current_date, 0)
        calendar_data.append({
            'date': current_date,
            'spending': spending,
            'weekday': current_date.weekday(),
            'week': current_date.isocalendar()[1]
        })
        current_date += timedelta(days=1)

    # Convert to matrix for heatmap
    df = pd.DataFrame(calendar_data)
    pivot_data = df.pivot(index='weekday', columns='week', values='spending').fillna(0)

    # Create heatmap
    fig, ax = plt.subplots(figsize=(16, 6))

    sns.heatmap(pivot_data,
                cmap='Reds',
                ax=ax,
                cbar_kws={'label': 'Daily Spending (IDR)'},
                linewidths=0.5)

    ax.set_title('Daily Spending Heatmap')
    ax.set_ylabel('Day of Week')
    ax.set_xlabel('Week of Year')

    # Set y-axis labels
    ax.set_yticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_day_of_week_analysis(transactions, output_path='cache/chart_cache/weekday_analysis.png'):
    """Analyze spending patterns by day of week."""
    if not transactions:
        return

    weekday_spending = defaultdict(list)

    for t in transactions:
        date = t.date if hasattr(t, 'date') else t['date']
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        elif isinstance(date, datetime):
            date = date.date()

        outgoing = abs(t.outgoing or 0) if hasattr(t, 'outgoing') else abs(t['outgoing'] or 0)
        if outgoing > 0:
            weekday_spending[date.weekday()].append(outgoing)

    # Calculate statistics
    weekday_stats = {}
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    for i in range(7):
        if weekday_spending[i]:
            weekday_stats[weekdays[i]] = {
                'mean': np.mean(weekday_spending[i]),
                'median': np.median(weekday_spending[i]),
                'total': sum(weekday_spending[i]),
                'count': len(weekday_spending[i])
            }
        else:
            weekday_stats[weekdays[i]] = {'mean': 0, 'median': 0, 'total': 0, 'count': 0}

    # Create visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # Average spending by weekday
    avg_spending = [weekday_stats[day]['mean'] for day in weekdays]
    colors = ['lightblue' if i < 5 else 'lightcoral' for i in range(7)]

    ax1.bar(weekdays, avg_spending, color=colors)
    ax1.set_title('Average Spending by Day of Week')
    ax1.set_ylabel('Average Amount (IDR)')
    ax1.tick_params(axis='x', rotation=45)

    # Total spending by weekday
    total_spending = [weekday_stats[day]['total'] for day in weekdays]
    ax2.bar(weekdays, total_spending, color=colors)
    ax2.set_title('Total Spending by Day of Week')
    ax2.set_ylabel('Total Amount (IDR)')
    ax2.tick_params(axis='x', rotation=45)

    # Transaction count by weekday
    transaction_counts = [weekday_stats[day]['count'] for day in weekdays]
    ax3.bar(weekdays, transaction_counts, color=colors)
    ax3.set_title('Number of Transactions by Day of Week')
    ax3.set_ylabel('Transaction Count')
    ax3.tick_params(axis='x', rotation=45)

    # Pie chart for weekend vs weekday spending
    weekday_total = sum(total_spending[:5])  # Mon-Fri
    weekend_total = sum(total_spending[5:])  # Sat-Sun

    if weekday_total + weekend_total > 0:
        ax4.pie([weekday_total, weekend_total],
                labels=['Weekdays', 'Weekends'],
                autopct='%1.1f%%',
                colors=['lightblue', 'lightcoral'])
        ax4.set_title('Weekday vs Weekend Spending')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_spending_velocity(transactions, output_path='cache/chart_cache/spending_velocity.png'):
    """Show spending velocity and predict future balance."""
    if not transactions:
        return

    # Sort transactions by date
    sorted_transactions = sorted(transactions, key=lambda x: x.date if hasattr(x, 'date') else x['date'])

    dates = []
    balances = []
    daily_spending = []

    for t in sorted_transactions:
        date = t.date if hasattr(t, 'date') else t['date']
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')

        balance = t.balance if hasattr(t, 'balance') else t['balance']
        outgoing = abs(t.outgoing or 0) if hasattr(t, 'outgoing') else abs(t['outgoing'] or 0)

        dates.append(date)
        balances.append(balance)
        daily_spending.append(outgoing)

    if len(dates) < 2:
        return

    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'balance': balances,
        'spending': daily_spending
    })

    # Calculate daily spending rate
    df['days_from_start'] = (df['date'] - df['date'].min()).dt.days

    # Calculate moving average spending
    if len(df) >= 7:
        df['spending_7day_avg'] = df['spending'].rolling(window=7, min_periods=1).mean()
    else:
        df['spending_7day_avg'] = df['spending']

    # Create plot
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12))

    # Balance over time
    ax1.plot(df['date'], df['balance'], color='blue', linewidth=2, label='Account Balance')
    ax1.set_title('Account Balance Over Time')
    ax1.set_ylabel('Balance (IDR)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Daily spending with moving average
    ax2.bar(df['date'], df['spending'], alpha=0.6, label='Daily Spending', color='red')
    ax2.plot(df['date'], df['spending_7day_avg'], color='darkred', linewidth=2, label='7-Day Average')
    ax2.set_title('Daily Spending Pattern')
    ax2.set_ylabel('Spending (IDR)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # Spending trend analysis
    if len(df) >= 14:
        # Calculate recent vs previous spending rate
        recent_avg = df['spending'].tail(7).mean()
        previous_avg = df['spending'].iloc[-14:-7].mean() if len(df) >= 14 else df['spending'].head(7).mean()

        trend_pct = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0

        # Velocity indicators
        velocity_data = [previous_avg, recent_avg]
        velocity_labels = ['Previous 7 Days', 'Recent 7 Days']
        colors = ['lightblue', 'red' if recent_avg > previous_avg else 'green']

        bars = ax3.bar(velocity_labels, velocity_data, color=colors)
        ax3.set_title(f'Spending Velocity Comparison\n({"↑" if trend_pct > 0 else "↓"} {abs(trend_pct):.1f}% change)')
        ax3.set_ylabel('Average Daily Spending (IDR)')

        # Add value labels on bars
        for bar, value in zip(bars, velocity_data):
            ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                     f'{value:,.0f}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_budget_progress(transactions, budget_limits, output_path='cache/chart_cache/budget_progress.png'):
    """Show budget progress with visual indicators."""
    if not transactions or not budget_limits:
        return

    # Calculate current month spending by category
    current_month = datetime.now().replace(day=1)
    current_month_transactions = [
        t for t in transactions
        if (t.date if hasattr(t, 'date') else t['date']) >= current_month
    ]

    category_spending = defaultdict(float)
    for t in current_month_transactions:
        outgoing = abs(t.outgoing or 0) if hasattr(t, 'outgoing') else abs(t['outgoing'] or 0)
        category = "Unknown"
        if hasattr(t, 'category') and t.category:
            category = t.category.name if hasattr(t.category, 'name') else str(t.category)
        category_spending[category] += outgoing

    # Create budget progress visualization
    categories = list(budget_limits.keys())
    spent_amounts = [category_spending.get(cat, 0) for cat in categories]
    budget_amounts = [budget_limits[cat] for cat in categories]
    progress_pcts = [min(spent / budget * 100, 100) if budget > 0 else 0
                     for spent, budget in zip(spent_amounts, budget_amounts)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Progress bars
    colors = ['red' if pct >= 100 else 'orange' if pct >= 80 else 'green' for pct in progress_pcts]
    bars = ax1.barh(categories, progress_pcts, color=colors)

    ax1.set_title('Budget Progress (% of Budget Used)')
    ax1.set_xlabel('Percentage (%)')
    ax1.set_xlim(0, 120)

    # Add percentage labels
    for bar, pct in zip(bars, progress_pcts):
        ax1.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                 f'{pct:.1f}%', va='center')

    # Add budget limit line
    ax1.axvline(x=100, color='red', linestyle='--', alpha=0.7, label='Budget Limit')
    ax1.legend()

    # Spending vs Budget comparison
    x = np.arange(len(categories))
    width = 0.35

    ax2.bar(x - width / 2, spent_amounts, width, label='Spent', color='lightcoral')
    ax2.bar(x + width / 2, budget_amounts, width, label='Budget', color='lightblue')

    ax2.set_title('Spending vs Budget Amounts')
    ax2.set_ylabel('Amount (IDR)')
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories, rotation=45, ha='right')
    ax2.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()