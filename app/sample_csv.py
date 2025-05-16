import pandas as pd
import numpy as np
import random
import os

# Write files into the current working directory
output_dir = './sampledata'    # project root
os.makedirs(output_dir, exist_ok=True)

descriptions = [
    'Groceries', 'Salary', 'Rent', 'Utilities', 'Coffee', 'Dining Out',
    'Transport', 'Entertainment', 'Subscription', 'Gift', 'Medical',
    'Insurance', 'Investment', 'Dividend', 'Refund'
]

for i in range(1, 6):
    # generate a 20-day range starting 1 Jan 2025
    dates = pd.date_range(start='2025-01-01', periods=20)
    # pick random amounts between -200 and +200
    amounts = np.round(np.random.uniform(-200, 200, size=20), 2)
    # random descriptions
    descs = [random.choice(descriptions) for _ in range(20)]
    # running balance beginning at 500
    balance = np.round(500 + np.cumsum(amounts), 2)

    df = pd.DataFrame({
        # change here: use '%d/%m/%Y'
        'Date':        dates.strftime('%d/%m/%Y'),
        'Amount':      amounts,
        'Description': descs,
        'Balance':     balance
    })

    filename = f'transactions_{i}.csv'
    filepath = os.path.join(output_dir, filename)
    df.to_csv(filepath, index=False)

    print(f"Written: {filepath}")
