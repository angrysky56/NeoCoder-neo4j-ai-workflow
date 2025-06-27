#!/usr/bin/env python3

"""
Failing Test for LV Templates Class Structure Errors
==================================================

This test demonstrates the 3 class structure errors in lv_templates.py.
It must fail initially, then pass after the fix is implemented.

Following NeoCoder FIX workflow - Step 3: Write Failing Test
"""

import sys
import os
import pytest
import inspect
from unittest.mock import Mock

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


class TestLVTemplatesClassStructure:
    """Test that LV template classes have proper method structure"""

    def setup_method(self):
        """Set up test fixtures"""
        # Mock Neo4j and Qdrant clients
        self.mock_neo4j = Mock()
        self.mock_qdrant = Mock()

    def test_lv_knowledge_extract_template_has_map_selected_strategies_method(self):
        """
        Test that LVKnowledgeExtractTemplate has _map_selected_strategies as a proper instance method
        
        This test MUST fail initially because the method is defined outside the class scope.
        """
        from mcp_neocoder.lv_templates import LVKnowledgeExtractTemplate
        
        # Create instance
        template = LVKnowledgeExtractTemplate(self.mock_neo4j, self.mock_qdrant)
        
        # Verify method exists as instance method
        assert hasattr(template, '_map_selected_strategies'), \
            "LVKnowledgeExtractTemplate should have _map_selected_strategies method"
        
        # Verify it's actually callable
        assert callable(getattr(template, '_map_selected_strategies')), \
            "_map_selected_strategies should be callable"
        
        # Verify method signature (should take self, strategies, selected_outputs)
        method = getattr(template, '_map_selected_strategies')
        sig = inspect.signature(method)
        param_names = list(sig.parameters.keys())
        
        # Should have parameters for strategies and selected_outputs (self is implicit)
        assert len(param_names) >= 2, \
            f"_map_selected_strategies should have at least 2 parameters, got: {param_names}"

    def test_lv_knowledge_query_template_has_unique_methods(self):
        """
        Test that LVKnowledgeQueryTemplate has proper unique methods without duplicates
        
        This test MUST fail initially because there are duplicate method definitions.
        """
        from mcp_neocoder.lv_templates import LVKnowledgeQueryTemplate
        
        # Create instance
        template = LVKnowledgeQueryTemplate(self.mock_neo4j, self.mock_qdrant)
        
        # Verify _map_selected_strategies exists and is properly defined
        assert hasattr(template, '_map_selected_strategies'), \
            "LVKnowledgeQueryTemplate should have _map_selected_strategies method"
        
        # Verify method is callable
        assert callable(getattr(template, '_map_selected_strategies')), \
            "_map_selected_strategies should be callable on LVKnowledgeQueryTemplate"
        
        # Check for _combine_query_results method
        assert hasattr(template, '_combine_query_results'), \
            "LVKnowledgeQueryTemplate should have _combine_query_results method"
        
        assert callable(getattr(template, '_combine_query_results')), \
            "_combine_query_results should be callable"

    def test_no_duplicate_method_definitions_in_file(self):
        """
        Test that there are no duplicate method definitions in the file
        
        This test MUST fail initially because of duplicate _map_selected_strategies definitions.
        """
        # Read the source file
        file_path = 'src/mcp_neocoder/lv_templates.py'
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Count occurrences of _map_selected_strategies definition
        map_strategies_defs = content.count('def _map_selected_strategies')
        
        # Should only be defined once per class, total 2 times maximum
        assert map_strategies_defs <= 2, \
            f"_map_selected_strategies should be defined at most 2 times (once per class), found {map_strategies_defs}"
        
        # Verify no methods are defined outside class scope (should not find "def " at beginning of line)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('def ') and not line.startswith('def __'):
                # Check if this line is inside a class (previous non-empty line should be indented)
                context_lines = lines[max(0, i-10):i]
                class_found = False
                for context_line in reversed(context_lines):
                    if context_line.strip().startswith('class '):
                        class_found = True
                        break
                    elif context_line.strip() and not context_line.startswith(' ') and not context_line.startswith('\t'):
                        break
                
                assert class_found, \
                    f"Method definition at line {i+1} appears to be outside class scope: {line.strip()}"

    def test_all_methods_are_properly_indented_class_members(self):
        """
        Test that all methods are properly indented as class members
        
        This test MUST fail initially because some methods are defined outside class scope.
        """
        from mcp_neocoder.lv_templates import LVKnowledgeExtractTemplate, LVKnowledgeQueryTemplate
        
        # Test LVKnowledgeExtractTemplate
        extract_template = LVKnowledgeExtractTemplate(self.mock_neo4j, self.mock_qdrant)
        
        required_extract_methods = [
            '_map_selected_strategies',
            '_load_document', 
            '_generate_extraction_strategies',
            '_execute_extraction_strategies',
            '_store_extracted_knowledge'
        ]
        
        for method_name in required_extract_methods:
            assert hasattr(extract_template, method_name), \
                f"LVKnowledgeExtractTemplate missing method: {method_name}"
            
            method = getattr(extract_template, method_name)
            assert callable(method), \
                f"LVKnowledgeExtractTemplate.{method_name} should be callable"
        
        # Test LVKnowledgeQueryTemplate
        query_template = LVKnowledgeQueryTemplate(self.mock_neo4j, self.mock_qdrant)
        
        required_query_methods = [
            '_map_selected_strategies',
            '_combine_query_results',
            '_generate_query_strategies',
            '_execute_query_strategies'
        ]
        
        for method_name in required_query_methods:
            assert hasattr(query_template, method_name), \
                f"LVKnowledgeQueryTemplate missing method: {method_name}"
            
            method = getattr(query_template, method_name)
            assert callable(method), \
                f"LVKnowledgeQueryTemplate.{method_name} should be callable"


if __name__ == "__main__":
    # Run the failing tests to verify they fail before the fix
    pytest.main([__file__, "-v"])
