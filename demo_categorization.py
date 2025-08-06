#!/usr/bin/env python3
"""
Demonstration script for OpenAI integration in categorization service
"""

import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.categorization_service import CategorizationService


def test_categorization_service():
    """Test the categorization service with sample transactions"""
    
    print("🔧 Initializing Categorization Service...")
    service = CategorizationService()
    
    # Check if OpenAI is enabled
    if service.openai_enabled:
        print("✓ OpenAI integration is enabled")
    else:
        print("ℹ️  OpenAI integration is disabled - using keyword-based categorization")
    
    print("\n📊 Testing transaction categorization...")
    
    # Sample transactions to test
    test_transactions = [
        "McDonald's Restaurant #123",
        "Grab ride to office",
        "Starbucks Coffee",
        "Shell Gas Station",
        "Tokopedia online shopping",
        "Netflix subscription",
        "Hospital medical bill",
        "Unknown merchant XYZ"
    ]
    
    results = []
    
    for transaction in test_transactions:
        print(f"\n🔍 Categorizing: '{transaction}'")
        
        try:
            result = service.categorize_transaction(transaction)
            
            if result:
                method = result.get('method', 'unknown')
                confidence = result.get('confidence', 'N/A')
                
                print(f"  ✓ Category: {result['category_name']}")
                print(f"  ✓ Subcategory: {result.get('subcategory_name', 'N/A')}")
                print(f"  ✓ Method: {method}")
                if confidence != 'N/A':
                    print(f"  ✓ Confidence: {confidence}")
                
                results.append({
                    'transaction': transaction,
                    'category': result['category_name'],
                    'subcategory': result.get('subcategory_name', 'N/A'),
                    'method': method,
                    'confidence': confidence
                })
            else:
                print("  ❌ Could not categorize transaction")
                results.append({
                    'transaction': transaction,
                    'category': 'Uncategorized',
                    'subcategory': 'N/A',
                    'method': 'none',
                    'confidence': 'N/A'
                })
                
        except Exception as e:
            print(f"  ❌ Error categorizing transaction: {e}")
            results.append({
                'transaction': transaction,
                'category': 'Error',
                'subcategory': 'N/A',
                'method': 'error',
                'confidence': 'N/A'
            })
    
    # Summary
    print("\n📈 Summary:")
    print("-" * 60)
    categorized = sum(1 for r in results if r['category'] not in ['Uncategorized', 'Error'])
    openai_count = sum(1 for r in results if r['method'] == 'openai')
    keyword_count = sum(1 for r in results if r['method'] == 'keywords')
    
    print(f"Total transactions: {len(test_transactions)}")
    print(f"Successfully categorized: {categorized}")
    print(f"OpenAI categorizations: {openai_count}")
    print(f"Keyword categorizations: {keyword_count}")
    print(f"Success rate: {categorized/len(test_transactions)*100:.1f}%")
    
    # Close session
    if hasattr(service, 'session'):
        service.session.close()
    
    return results


if __name__ == "__main__":
    print("🚀 OpenAI Categorization Service Demo")
    print("=" * 50)
    
    try:
        results = test_categorization_service()
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)