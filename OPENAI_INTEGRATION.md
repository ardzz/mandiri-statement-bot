# OpenAI Integration for Transaction Categorization

## Overview

The categorization service now supports OpenAI integration for improved transaction categorization. When OpenAI is configured, the service will use AI to categorize transactions. If OpenAI is not available or fails, it automatically falls back to the existing keyword-based categorization.

## Configuration

### Environment Variables

Add the following variables to your `.env` file:

```env
# OpenAI Configuration (optional)
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_ENABLE_CATEGORIZATION=true
```

### Configuration Options

- `OPENAI_API_KEY`: Your OpenAI API key (required for OpenAI features)
- `OPENAI_MODEL`: The OpenAI model to use (default: `gpt-3.5-turbo`)
- `OPENAI_ENABLE_CATEGORIZATION`: Enable/disable OpenAI categorization (default: `false`)

## How It Works

1. **OpenAI First**: If OpenAI is configured and enabled, the service will first attempt to categorize transactions using AI
2. **Keyword Fallback**: If OpenAI is not available or fails, the service automatically falls back to keyword-based categorization
3. **Error Handling**: All OpenAI errors are gracefully handled with fallback to keywords

## Usage

The categorization service works exactly the same way - the OpenAI integration is transparent:

```python
from core.services.categorization_service import CategorizationService

service = CategorizationService()
result = service.categorize_transaction("Starbucks coffee purchase")

if result:
    print(f"Category: {result['category_name']}")
    print(f"Subcategory: {result['subcategory_name']}")
    print(f"Method: {result['method']}")  # 'openai' or 'keywords'
    if 'confidence' in result:
        print(f"Confidence: {result['confidence']}")
```

## Response Format

The categorization service returns a dictionary with the following fields:

```python
{
    'category_id': 1,
    'subcategory_id': 3,
    'category_name': 'Food & Dining',
    'subcategory_name': 'Coffee & Beverages',
    'method': 'openai',  # 'openai' or 'keywords'
    'confidence': 0.9     # Only present for OpenAI results
}
```

## Testing

Run the tests to verify the integration works correctly:

```bash
python -m pytest tests/test_categorization_service.py -v
```

Run the demo script to see the categorization in action:

```bash
python demo_categorization.py
```

## Available Categories

The following categories and subcategories are available:

- **Food & Dining**: Restaurants, Fast Food, Coffee & Beverages, Groceries & Supermarkets, Street Food, Bakery & Snacks
- **Shopping**: Online Shopping, Retail Stores, Convenience Stores, Pharmacy, Electronics, Clothing & Fashion
- **Transportation**: Public Transport, Taxi & Ride Sharing, Fuel, Parking, Vehicle Maintenance
- **Health & Fitness**: Gym & Fitness, Medical Expenses, Pharmacy, Health Insurance
- **Entertainment**: Movies & Recreation, Games & Apps, Books & Media, Sports & Activities
- **Personal Care**: Haircut & Grooming, Beauty & Cosmetics, Spa & Wellness
- **Bills & Utilities**: Bank Fees, Service Charges, Subscription Services, Insurance
- **Transfers & Banking**: Bank Transfers, ATM Withdrawals, Cash Deposits, Investment Transfers
- **Income**: Salary, Freelance Income, Investment Returns, Other Income
- **Education**: Tuition Fees, Books & Supplies, Online Courses, Educational Services
- **Travel**: Accommodation, Transportation, Food & Dining, Souvenirs & Shopping

## Benefits of OpenAI Integration

1. **Improved Accuracy**: AI can understand context and nuance better than keyword matching
2. **Better Handling of Edge Cases**: Can categorize transactions that don't match predefined keywords
3. **Continuous Learning**: OpenAI models are constantly improving
4. **Graceful Fallback**: If OpenAI fails, the system still works with keyword-based categorization
5. **Confidence Scoring**: OpenAI provides confidence scores for its categorizations

## Cost Considerations

- OpenAI API calls incur costs based on usage
- The service is optimized to use minimal tokens for cost efficiency
- Keyword-based categorization is always available as a free fallback

## Troubleshooting

If categorization is not working as expected:

1. Check that your OpenAI API key is valid and has sufficient credits
2. Verify that `OPENAI_ENABLE_CATEGORIZATION=true` in your `.env` file
3. Check the logs for any OpenAI-related error messages
4. The service will automatically fall back to keyword-based categorization if OpenAI fails