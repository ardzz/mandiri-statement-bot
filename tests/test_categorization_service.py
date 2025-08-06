#!/usr/bin/env python3
"""
Tests for CategorizationService with OpenAI integration
"""

import os
import pytest
import unittest.mock as mock
from unittest.mock import Mock, patch

# Add project root to Python path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.categorization_service import CategorizationService
from core.database import Category, Subcategory


class TestCategorizationService:
    """Test cases for CategorizationService"""

    def setup_method(self):
        """Setup test environment"""
        self.service = CategorizationService()

    def teardown_method(self):
        """Cleanup after tests"""
        if hasattr(self.service, 'session'):
            self.service.session.close()

    def test_keyword_categorization_fallback(self):
        """Test that keyword-based categorization works when OpenAI is disabled"""
        with patch.object(self.service, 'openai_enabled', False):
            # Mock database queries
            with patch.object(self.service.session, 'query') as mock_query:
                # Mock category
                mock_category = Mock()
                mock_category.id = 1
                mock_category.name = "Food & Dining"
                
                mock_query.return_value.filter.return_value.first.return_value = mock_category
                
                # Test categorization
                result = self.service.categorize_transaction("McDonald's restaurant payment")
                
                assert result is not None
                assert result['category_name'] == "Food & Dining"
                assert result['method'] == 'keywords'

    @patch('openai.OpenAI')
    def test_openai_categorization_success(self, mock_openai_class):
        """Test successful OpenAI categorization"""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock OpenAI response
        mock_choice = Mock()
        mock_choice.message.content = '{"category": "Food & Dining", "subcategory": "Restaurants", "confidence": 0.9}'
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create service with OpenAI enabled
        with patch('config.settings.OPENAI_ENABLE_CATEGORIZATION', True), \
             patch('config.settings.OPENAI_API_KEY', 'test-key'):
            
            service = CategorizationService()
            service.openai_enabled = True
            service.openai_client = mock_client
            
            # Mock database queries
            with patch.object(service.session, 'query') as mock_query:
                # Mock available categories for _get_available_categories
                mock_category = Mock()
                mock_category.name = "Food & Dining"
                mock_category.id = 1
                mock_categories = [mock_category]
                
                mock_subcategory = Mock()
                mock_subcategory.name = "Restaurants"
                mock_subcategories = [mock_subcategory]
                
                # Setup query responses
                def query_side_effect(model):
                    mock_result = Mock()
                    if hasattr(model, '__name__') and model.__name__ == 'Category':
                        mock_result.filter.return_value.all.return_value = mock_categories
                        mock_result.filter.return_value.first.return_value = mock_category
                    elif hasattr(model, '__name__') and model.__name__ == 'Subcategory':
                        mock_result.filter.return_value.all.return_value = mock_subcategories
                        mock_subcategory_found = Mock()
                        mock_subcategory_found.id = 1
                        mock_subcategory_found.name = "Restaurants"
                        mock_result.filter.return_value.first.return_value = mock_subcategory_found
                    return mock_result
                
                mock_query.side_effect = query_side_effect
                
                # Test categorization
                result = service.categorize_transaction("Expensive restaurant bill")
                
                assert result is not None
                assert result['category_name'] == "Food & Dining"
                assert result['subcategory_name'] == "Restaurants"
                assert result['method'] == 'openai'
                assert result['confidence'] == 0.9

    @patch('openai.OpenAI')
    def test_openai_fallback_to_keywords(self, mock_openai_class):
        """Test fallback to keywords when OpenAI fails"""
        # Mock OpenAI client that raises an exception
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Create service with OpenAI enabled
        with patch('config.settings.OPENAI_ENABLE_CATEGORIZATION', True), \
             patch('config.settings.OPENAI_API_KEY', 'test-key'):
            
            service = CategorizationService()
            service.openai_enabled = True
            service.openai_client = mock_client
            
            # Mock database queries for fallback
            with patch.object(service.session, 'query') as mock_query:
                mock_category = Mock()
                mock_category.id = 1
                mock_category.name = "Food & Dining"
                
                mock_query.return_value.filter.return_value.first.return_value = mock_category
                mock_query.return_value.filter.return_value.all.return_value = []  # For _get_available_categories
                
                # Test categorization - should fallback to keywords
                result = service.categorize_transaction("McDonald's restaurant")
                
                assert result is not None
                assert result['category_name'] == "Food & Dining"
                assert result['method'] == 'keywords'

    def test_empty_description(self):
        """Test handling of empty description"""
        result = self.service.categorize_transaction("")
        assert result is None
        
        result = self.service.categorize_transaction(None)
        assert result is None

    def test_get_available_categories(self):
        """Test _get_available_categories method"""
        with patch.object(self.service.session, 'query') as mock_query:
            # Mock categories with proper name attribute
            mock_category1 = Mock()
            mock_category1.name = "Food & Dining"
            mock_category1.id = 1
            
            mock_category2 = Mock()
            mock_category2.name = "Transportation"
            mock_category2.id = 2
            
            mock_categories = [mock_category1, mock_category2]
            
            # Mock subcategories with proper name attribute
            mock_sub1 = Mock()
            mock_sub1.name = "Restaurants"
            mock_sub2 = Mock()
            mock_sub2.name = "Fast Food"
            mock_subcategories_food = [mock_sub1, mock_sub2]
            
            mock_sub3 = Mock()
            mock_sub3.name = "Taxi"
            mock_sub4 = Mock()
            mock_sub4.name = "Fuel"
            mock_subcategories_transport = [mock_sub3, mock_sub4]
            
            def query_side_effect(model):
                mock_result = Mock()
                if hasattr(model, '__name__') and model.__name__ == 'Category':
                    mock_result.filter.return_value.all.return_value = mock_categories
                elif hasattr(model, '__name__') and model.__name__ == 'Subcategory':
                    # Alternate between subcategories for different categories
                    mock_filter_result = Mock()
                    # For simplicity, just return food subcategories for all queries
                    mock_filter_result.all.return_value = mock_subcategories_food
                    mock_result.filter.return_value = mock_filter_result
                return mock_result
            
            mock_query.side_effect = query_side_effect
            
            categories = self.service._get_available_categories()
            
            assert "Food & Dining" in categories
            assert "Transportation" in categories
            assert len(categories) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])