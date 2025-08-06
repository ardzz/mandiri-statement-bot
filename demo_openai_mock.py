#!/usr/bin/env python3
"""
OpenAI Integration Demo with Mock
This demonstrates how the OpenAI integration would work with actual API calls
"""

import os
import sys
from unittest.mock import Mock, patch

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.categorization_service import CategorizationService


def demo_openai_categorization():
    """Demo OpenAI categorization with a mock client"""
    
    print("🤖 OpenAI Integration Demo (Mock)")
    print("=" * 50)
    
    # Create mock OpenAI client
    mock_client = Mock()
    
    # Sample responses for different transaction types
    responses = {
        "McDonald's Restaurant": '{"category": "Food & Dining", "subcategory": "Fast Food", "confidence": 0.95}',
        "Uber ride to airport": '{"category": "Transportation", "subcategory": "Taxi & Ride Sharing", "confidence": 0.92}',
        "Amazon online purchase": '{"category": "Shopping", "subcategory": "Online Shopping", "confidence": 0.88}',
        "Monthly gym membership": '{"category": "Health & Fitness", "subcategory": "Gym & Fitness", "confidence": 0.90}',
        "Strange payment ABC123": 'null'  # OpenAI couldn't categorize
    }
    
    # Mock response function
    def mock_create(**kwargs):
        user_message = kwargs['messages'][1]['content']
        
        # Extract transaction description from prompt
        for transaction, response in responses.items():
            if transaction in user_message:
                mock_choice = Mock()
                mock_choice.message.content = response
                mock_response = Mock()
                mock_response.choices = [mock_choice]
                return mock_response
        
        # Default response if not found
        mock_choice = Mock()
        mock_choice.message.content = 'null'
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        return mock_response
    
    mock_client.chat.completions.create.side_effect = mock_create
    
    # Patch the service to use OpenAI
    with patch('config.settings.OPENAI_ENABLE_CATEGORIZATION', True), \
         patch('config.settings.OPENAI_API_KEY', 'mock-key'):
        
        # Initialize service
        service = CategorizationService()
        service.openai_enabled = True
        service.openai_client = mock_client
        
        print("✓ Mock OpenAI client initialized")
        
        # Mock database responses
        def mock_query_side_effect(model):
            mock_result = Mock()
            
            if hasattr(model, '__name__'):
                if model.__name__ == 'Category':
                    # Mock categories for _get_available_categories
                    mock_categories = []
                    for cat_name in ["Food & Dining", "Transportation", "Shopping", "Health & Fitness"]:
                        mock_cat = Mock()
                        mock_cat.name = cat_name
                        mock_cat.id = hash(cat_name) % 1000
                        mock_categories.append(mock_cat)
                    mock_result.filter.return_value.all.return_value = mock_categories
                    
                    # Mock specific category lookup
                    def first_side_effect():
                        # Return the first matching category
                        return mock_categories[0] if mock_categories else None
                    mock_result.filter.return_value.first.side_effect = first_side_effect
                    
                elif model.__name__ == 'Subcategory':
                    # Mock subcategories
                    mock_subcategories = []
                    for sub_name in ["Fast Food", "Taxi & Ride Sharing", "Online Shopping", "Gym & Fitness"]:
                        mock_sub = Mock()
                        mock_sub.name = sub_name
                        mock_sub.id = hash(sub_name) % 1000
                        mock_subcategories.append(mock_sub)
                    mock_result.filter.return_value.all.return_value = mock_subcategories
                    
                    # Mock specific subcategory lookup
                    def first_sub_side_effect():
                        return mock_subcategories[0] if mock_subcategories else None
                    mock_result.filter.return_value.first.side_effect = first_sub_side_effect
            
            return mock_result
        
        with patch.object(service.session, 'query', side_effect=mock_query_side_effect):
            
            # Test transactions
            test_transactions = [
                "McDonald's Restaurant",
                "Uber ride to airport", 
                "Amazon online purchase",
                "Monthly gym membership",
                "Strange payment ABC123"
            ]
            
            print(f"\n📊 Testing {len(test_transactions)} transactions with OpenAI...")
            
            results = []
            for transaction in test_transactions:
                print(f"\n🔍 Categorizing: '{transaction}'")
                
                try:
                    result = service.categorize_transaction(transaction)
                    
                    if result:
                        print(f"  ✓ Category: {result['category_name']}")
                        print(f"  ✓ Subcategory: {result.get('subcategory_name', 'N/A')}")
                        print(f"  ✓ Method: {result['method']}")
                        print(f"  ✓ Confidence: {result.get('confidence', 'N/A')}")
                        results.append(result)
                    else:
                        print("  ❌ Could not categorize transaction")
                        
                except Exception as e:
                    print(f"  ❌ Error: {e}")
            
            # Summary
            print(f"\n📈 Results Summary:")
            print("-" * 40)
            print(f"Total transactions: {len(test_transactions)}")
            print(f"Successfully categorized: {len(results)}")
            
            openai_count = sum(1 for r in results if r.get('method') == 'openai')
            keyword_count = sum(1 for r in results if r.get('method') == 'keywords')
            
            print(f"OpenAI categorizations: {openai_count}")
            print(f"Keyword categorizations: {keyword_count}")
            print(f"Success rate: {len(results)/len(test_transactions)*100:.1f}%")
            
            if results:
                avg_confidence = sum(r.get('confidence', 0) for r in results if r.get('confidence')) / len([r for r in results if r.get('confidence')])
                print(f"Average confidence: {avg_confidence:.2f}")
    
    print("\n✅ OpenAI Demo completed!")
    return results


if __name__ == "__main__":
    try:
        demo_openai_categorization()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)