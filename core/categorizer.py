import json


CATEGORY_KEYWORDS = {
    "groceries": "Food",
}

def categorize_transaction(description):
    for keyword, category in CATEGORY_KEYWORDS.items():
        if keyword.lower() in description.lower():
            return category
    return "Uncategorized"