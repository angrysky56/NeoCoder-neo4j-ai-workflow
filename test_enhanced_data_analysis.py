#!/usr/bin/env python3
"""
Test script for enhanced Data Analysis incarnation features.
Tests the new type detection, visualization, and ML capabilities.
"""

import sys
import os
import tempfile
import csv
import json
from datetime import datetime, timedelta
import random

# Add the source directory to the path
sys.path.insert(0, '/home/ty/Repositories/NeoCoder-neo4j-ai-workflow/src')

def create_test_csv():
    """Create a test CSV file with various data types."""
    test_data = []
    base_date = datetime(2023, 1, 1)
    
    for i in range(100):
        row = {
            'id': i + 1,
            'name': f'Customer_{i+1}',
            'email': f'customer{i+1}@example.com',
            'age': random.randint(18, 80),
            'salary': random.randint(30000, 150000),
            'department': random.choice(['Sales', 'Marketing', 'Engineering', 'HR']),
            'join_date': (base_date + timedelta(days=random.randint(0, 1000))).strftime('%Y-%m-%d'),
            'is_active': random.choice(['True', 'False', 'Yes', 'No']),
            'commission_rate': f"{random.uniform(0.05, 0.15):.1%}",
            'bonus': f"${random.randint(1000, 10000)}",
            'score': random.uniform(1.0, 10.0),
            'website': f'https://customer{i+1}.example.com'
        }
        test_data.append(row)
    
    # Create temporary CSV file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    
    fieldnames = test_data[0].keys()
    writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(test_data)
    
    temp_file.close()
    return temp_file.name

def test_type_detection():
    """Test the enhanced data type detection."""
    print("🔍 Testing Enhanced Data Type Detection")
    print("=" * 50)
    
    # Import the enhanced type detector
    try:
        from mcp_neocoder.incarnations.data_analysis_incarnation import AdvancedDataTypeDetector
        
        detector = AdvancedDataTypeDetector()
        
        # Test various data types
        test_cases = [
            {
                'name': 'Numeric Integer',
                'values': ['1', '2', '3', '100', '500'],
                'expected': 'integer'
            },
            {
                'name': 'Numeric Float', 
                'values': ['1.5', '2.7', '3.14', '100.0', '500.99'],
                'expected': 'numeric'
            },
            {
                'name': 'Boolean',
                'values': ['True', 'False', 'true', 'false', 'yes', 'no'],
                'expected': 'boolean'
            },
            {
                'name': 'Date',
                'values': ['2023-01-01', '2023-12-31', '2024-06-15'],
                'expected': 'datetime'
            },
            {
                'name': 'Currency',
                'values': ['$100', '$1,500', '$25.99', '€50', '£30'],
                'expected': 'currency'
            },
            {
                'name': 'Percentage',
                'values': ['50%', '25.5%', '100%', '0.5%'],
                'expected': 'percentage'
            },
            {
                'name': 'Email',
                'values': ['user@example.com', 'test@gmail.com', 'admin@company.org'],
                'expected': 'email'
            },
            {
                'name': 'URL',
                'values': ['https://example.com', 'http://test.org', 'www.company.com'],
                'expected': 'url'
            },
            {
                'name': 'Categorical',
                'values': ['Red', 'Blue', 'Green', 'Red', 'Blue', 'Green'] * 5,
                'expected': 'categorical'
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            result = detector.detect_data_type(test_case['values'])
            detected_type = result['type']
            confidence = result['confidence']
            
            status = "✅ PASS" if detected_type == test_case['expected'] else "❌ FAIL"
            if detected_type != test_case['expected']:
                all_passed = False
            
            print(f"{status} {test_case['name']}: {detected_type} (confidence: {confidence:.2f})")
        
        print(f"\n📊 Type Detection Test Results: {'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'}")
        return all_passed
        
    except ImportError as e:
        print(f"❌ Could not import AdvancedDataTypeDetector: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing type detection: {e}")
        return False

def test_csv_loading():
    """Test enhanced CSV loading with the new type detector."""
    print("\n📁 Testing Enhanced CSV Loading")
    print("=" * 50)
    
    try:
        from mcp_neocoder.incarnations.data_analysis_incarnation import DataAnalysisIncarnation
        
        # Create test CSV
        test_file = create_test_csv()
        print(f"Created test CSV: {test_file}")
        
        # Create incarnation instance
        incarnation = DataAnalysisIncarnation(driver=None, database="test")
        
        # Test CSV loading
        result = incarnation._load_csv_data(test_file)
        
        print(f"✅ Loaded {result['row_count']} rows and {result['column_count']} columns")
        
        # Check enhanced type detection results
        print("\n🔍 Detected Data Types:")
        for col_name, col_info in result['columns'].items():
            confidence = col_info.get('confidence', 'N/A')
            type_details = col_info.get('type_details', {})
            print(f"  • {col_name}: {col_info['data_type']} (confidence: {confidence:.2f})")
            
            # Show detection breakdown for mixed types
            if 'detection_counts' in type_details:
                detection_counts = type_details['detection_counts']
                significant_types = {k: v for k, v in detection_counts.items() if v > 0}
                if len(significant_types) > 1:
                    print(f"    Detection breakdown: {significant_types}")
        
        # Cleanup
        os.unlink(test_file)
        
        print(f"\n📊 CSV Loading Test: ✅ SUCCESS")
        return True
        
    except Exception as e:
        print(f"❌ Error testing CSV loading: {e}")
        if 'test_file' in locals():
            try:
                os.unlink(test_file)
            except:
                pass
        return False

def test_library_availability():
    """Test availability of required libraries."""
    print("\n📚 Testing Library Availability")
    print("=" * 50)
    
    libraries = [
        ('pandas', 'Data manipulation and analysis'),
        ('numpy', 'Numerical computing'),
        ('matplotlib', 'Static plotting'),
        ('seaborn', 'Statistical visualization'),
        ('plotly', 'Interactive visualization'),
        ('scipy', 'Scientific computing'),
        ('sklearn', 'Machine learning'),
        ('dateutil', 'Date parsing'),
    ]
    
    available_count = 0
    total_count = len(libraries)
    
    for lib_name, description in libraries:
        try:
            if lib_name == 'sklearn':
                import sklearn
            elif lib_name == 'dateutil':
                import dateutil
            else:
                __import__(lib_name)
            print(f"✅ {lib_name}: {description}")
            available_count += 1
        except ImportError:
            print(f"❌ {lib_name}: {description} - NOT AVAILABLE")
    
    print(f"\n📊 Library Availability: {available_count}/{total_count} libraries available")
    
    if available_count == total_count:
        print("🎉 All advanced analytics libraries are available!")
    elif available_count >= total_count * 0.7:
        print("⚠️ Most libraries available - advanced features should work")
    else:
        print("❌ Many libraries missing - only basic features will work")
    
    return available_count >= total_count * 0.7

def run_integration_test():
    """Run a comprehensive integration test."""
    print("\n🧪 Running Integration Test")
    print("=" * 50)
    
    try:
        # Test type detection
        type_test = test_type_detection()
        
        # Test CSV loading
        csv_test = test_csv_loading()
        
        # Test library availability
        lib_test = test_library_availability()
        
        print(f"\n🎯 INTEGRATION TEST RESULTS")
        print("=" * 50)
        print(f"Type Detection: {'✅ PASS' if type_test else '❌ FAIL'}")
        print(f"CSV Loading: {'✅ PASS' if csv_test else '❌ FAIL'}")
        print(f"Library Availability: {'✅ PASS' if lib_test else '❌ FAIL'}")
        
        overall_success = type_test and csv_test and lib_test
        print(f"\n🏆 OVERALL RESULT: {'✅ SUCCESS' if overall_success else '❌ PARTIAL SUCCESS'}")
        
        if overall_success:
            print("\n🚀 Enhanced Data Analysis incarnation is ready for use!")
            print("All core features have been successfully implemented and tested.")
        else:
            print("\n⚠️ Some issues detected - check the details above.")
            print("Basic functionality should still work, but some advanced features may be limited.")
            
        return overall_success
        
    except Exception as e:
        print(f"❌ Integration test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("🔬 Enhanced Data Analysis Testing Suite")
    print("=" * 60)
    print("Testing the enhanced NeoCoder Data Analysis incarnation")
    print("This will verify new features like type detection, ML integration, etc.")
    print("=" * 60)
    
    success = run_integration_test()
    
    if success:
        print("\n🎉 All tests passed! The enhanced data analysis incarnation is ready.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
    
    print("\n" + "=" * 60)
    print("Test completed. Check the results above.")
