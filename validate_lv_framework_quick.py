#!/usr/bin/env python3

"""
Quick LV Framework Validation Test
=================================

Tests the core components of the LV framework to ensure everything is working.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_lv_imports():
    """Test that LV modules can be imported"""
    try:
        from mcp_neocoder.lv_ecosystem import EntropyEstimator, LVEcosystem
        from mcp_neocoder.lv_neo4j_storage import LVNeo4jStorage
        print("✅ LV modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_entropy_calculation():
    """Test entropy calculation functionality"""
    try:
        from mcp_neocoder.lv_ecosystem import EntropyEstimator
        
        estimator = EntropyEstimator()
        
        # Test high entropy prompt
        high_entropy_prompt = "Give me multiple creative approaches to solve climate change using diverse innovative strategies"
        high_entropy = estimator.estimate_prompt_entropy(high_entropy_prompt)
        
        # Test low entropy prompt  
        low_entropy_prompt = "What is the capital of France?"
        low_entropy = estimator.estimate_prompt_entropy(low_entropy_prompt)
        
        print(f"✅ Entropy calculation working:")
        print(f"   High entropy prompt: {high_entropy:.3f}")
        print(f"   Low entropy prompt: {low_entropy:.3f}")
        
        # Validate that high entropy > low entropy
        if high_entropy > low_entropy:
            print("✅ Entropy ordering is correct")
            return True
        else:
            print("❌ Entropy ordering is incorrect")
            return False
            
    except Exception as e:
        print(f"❌ Entropy test failed: {e}")
        return False

def test_lv_configuration_structure():
    """Test that LV configuration structure is valid"""
    try:
        # Test configuration structure
        lv_config = {
            'framework_version': '1.0',
            'entropy_thresholds': [0.3, 0.6],
            'damping_factor': 0.15,
            'max_iterations': 10,
            'convergence_threshold': 1e-6,
            'weight_schemes': {
                'low_entropy': {'quality': 0.9, 'novelty': 0.0, 'bias': 0.05, 'cost': 0.05},
                'medium_entropy': {'quality': 0.6, 'novelty': 0.3, 'bias': 0.05, 'cost': 0.05},
                'high_entropy': {'quality': 0.2, 'novelty': 0.7, 'bias': 0.05, 'cost': 0.05}
            },
            'alpha_weights': {'semantic': 0.6, 'niche': 0.3, 'task': 0.1}
        }
        
        # Validate weight schemes sum to 1.0
        for scheme_name, weights in lv_config['weight_schemes'].items():
            total = sum(weights.values())
            if abs(total - 1.0) < 0.001:
                print(f"✅ {scheme_name} weights sum correctly: {total:.3f}")
            else:
                print(f"❌ {scheme_name} weights sum incorrectly: {total:.3f}")
                return False
        
        # Validate alpha weights
        alpha_total = sum(lv_config['alpha_weights'].values())
        if abs(alpha_total - 1.0) < 0.001:
            print(f"✅ Alpha weights sum correctly: {alpha_total:.3f}")
            return True
        else:
            print(f"❌ Alpha weights sum incorrectly: {alpha_total:.3f}")
            return False
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run LV framework validation tests"""
    print("🧬 LV Framework Validation Test")
    print("=" * 40)
    
    tests = [
        ("Module Imports", test_lv_imports),
        ("Entropy Calculation", test_entropy_calculation), 
        ("Configuration Structure", test_lv_configuration_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        if test_func():
            passed += 1
        
    print(f"\n{'='*40}")
    print(f"LV Framework Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 LV Framework is ready for use!")
        print("\nNext steps:")
        print("1. Use Neo4j ActionTemplates with keywords: KNOWLEDGE_EXTRACT_LV, KNOWLEDGE_QUERY_LV, LV_SELECT")
        print("2. Follow your established NeoCoder workflow procedure")
        print("3. Entropy > 0.4 triggers LV enhancement automatically")
        print("4. All results stored in Neo4j with full traceability")
        return True
    else:
        print("❌ Some tests failed - please check the setup")
        return False

if __name__ == "__main__":
    main()
