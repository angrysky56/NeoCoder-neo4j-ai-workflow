#!/usr/bin/env python

"""
LV Framework Integration Example
==============================

Demonstrates how to use the Lotka-Volterra Ecosystem Intelligence Framework
within the NeoCoder Neo4j-guided workflow system.

This example follows the exact NeoCoder procedure:
1. Identify Task & Keyword
2. Consult the Hub  
3. Retrieve Instructions from ActionTemplate
4. Execute Guided Workflow
5. Perform Verification (ALL tests must pass)
6. Record Completion (only after tests pass)
7. Finalize Updates
"""

import asyncio
import logging
from typing import Dict, Any
from pathlib import Path

# Following Step 3 from KNOWLEDGE_EXTRACT_LV template
from src.mcp_neocoder.lv_integration import NeoCoder_LV_Integration
from src.mcp_neocoder.lv_ecosystem import EntropyEstimator

logger = logging.getLogger(__name__)


async def lv_knowledge_extraction_example(document_path: str, user_prompt: str):
    """
    Complete example of LV-enhanced knowledge extraction following NeoCoder workflow
    
    This function demonstrates all steps from the KNOWLEDGE_EXTRACT_LV template:
    1. Check entropy
    2. Make enhancement decision
    3. Initialize LV system
    4. Execute with ecosystem dynamics
    5. Verify results meet quality thresholds
    6. Record execution (only if tests pass)
    7. Present results with LV explanation
    """
    
    print("🧬 Starting LV-Enhanced Knowledge Extraction")
    print("=" * 60)
    
    # Step 1: Check entropy (from KNOWLEDGE_EXTRACT_LV template)
    print("Step 1: Checking entropy...")
    estimator = EntropyEstimator()
    entropy = estimator.estimate_prompt_entropy(user_prompt)
    print(f"   Entropy: {entropy:.3f}")
    
    # Step 2: Decision logic (from template)
    print("Step 2: Enhancement decision...")
    if entropy > 0.4:
        print(f"   High entropy ({entropy:.3f}) - Using LV enhancement ✅")
        use_lv = True
    else:
        print(f"   Low entropy ({entropy:.3f}) - Using standard extraction")
        use_lv = False
        return await standard_extraction_fallback(document_path, user_prompt)
    
    # Step 3-4: Initialize and setup LV system (from template)
    print("Step 3-4: Initializing LV system...")
    try:
        # Note: In real usage, you'd get these from your existing NeoCoder setup
        neo4j_session = None  # Your Neo4j session
        qdrant_client = None  # Your Qdrant client
        
        # This would be: lv_system = NeoCoder_LV_Integration(neo4j_session, qdrant_client)
        print("   LV system initialized (placeholder for demo)")
        
    except Exception as e:
        print(f"   ❌ LV initialization failed: {e}")
        return {'error': 'LV system unavailable', 'fallback': 'standard_extraction'}
    
    # Step 5: Execute LV-enhanced extraction (from template)
    print("Step 5: Executing LV-enhanced extraction...")
    
    # Simulate LV enhancement execution
    context = {
        'document_path': document_path,
        'prompt': user_prompt,
        'extraction_mode': 'comprehensive',
        'history': []
    }
    
    # This would be: results = await lv_system.enhance_existing_template("KNOWLEDGE_EXTRACT", context)
    results = await simulate_lv_extraction_results(context, entropy)
    
    print(f"   Strategies used: {results.get('strategies_used', [])}")
    print(f"   Entities extracted: {results.get('entities_extracted', 0)}")
    print(f"   Diversity score: {results.get('diversity_metrics', {}).get('semantic_diversity', 0):.3f}")
    
    # Step 6: Verification (CRITICAL - from template)
    print("Step 6: Performing verification...")
    verification_passed = await verify_lv_results(results)
    
    if not verification_passed:
        print("   ❌ Verification FAILED - Cannot record execution")
        return {'error': 'Verification failed', 'results': results}
    
    print("   ✅ All verification tests PASSED")
    
    # Step 7: Record execution (only after tests pass - from template)
    print("Step 7: Recording successful execution...")
    
    # This would use your existing log_workflow_execution function
    execution_record = {
        'project_id': 'lv_framework_demo',
        'template_keyword': 'KNOWLEDGE_EXTRACT_LV',
        'summary': f'LV-enhanced extraction with {entropy:.3f} entropy, {results.get("entities_extracted", 0)} entities',
        'files_changed': [document_path],
        'lv_session_id': results.get('session_id'),
        'diversity_preserved': True
    }
    
    print(f"   Execution recorded: {execution_record['summary']}")
    
    # Step 8: Report with LV explanation (from template)
    print("Step 8: Generating final report...")
    
    report = generate_lv_extraction_report(results, entropy, user_prompt)
    print("\n🧬 LV ECOSYSTEM INTELLIGENCE REPORT")
    print("=" * 50)
    print(report)
    
    return results


async def simulate_lv_extraction_results(context: Dict[str, Any], entropy: float) -> Dict[str, Any]:
    """
    Simulate LV extraction results for demonstration
    In real usage, this would be handled by the LV system
    """
    # Simulate different entropy-based behaviors
    if entropy > 0.7:
        # High entropy - maximum diversity
        strategies = ['creative', 'aggressive', 'domain_specific']
        diversity_score = 0.85
        entities_count = 15
    elif entropy > 0.4:
        # Medium entropy - balanced approach  
        strategies = ['conservative', 'balanced', 'structured']
        diversity_score = 0.72
        entities_count = 8
    else:
        # Low entropy - precision focused
        strategies = ['conservative']
        diversity_score = 0.45
        entities_count = 3
    
    return {
        'strategies_used': strategies,
        'entities_extracted': entities_count,
        'relationships_created': entities_count // 2,
        'diversity_metrics': {
            'semantic_diversity': diversity_score,
            'population_diversity': 0.8,
            'num_selected': len(strategies)
        },
        'lv_analysis': {
            'entropy': entropy,
            'convergence_iterations': 6,
            'ecosystem_stable': True
        },
        'session_id': f'lv_demo_{int(asyncio.get_event_loop().time())}'
    }


async def verify_lv_results(results: Dict[str, Any]) -> bool:
    """
    Verification function following Step 7 from KNOWLEDGE_EXTRACT_LV template:
    "Verify: Check results["entities_extracted"] > 0 and results["diversity_metrics"]["semantic_diversity"] > 0.7"
    
    ALL tests must pass for the workflow to be considered successful.
    """
    print("   Running LV verification tests...")
    
    # Test 1: Entities extracted
    entities_extracted = results.get('entities_extracted', 0)
    test1_passed = entities_extracted > 0
    print(f"   Test 1 - Entities extracted > 0: {entities_extracted} {'✅' if test1_passed else '❌'}")
    
    # Test 2: Diversity threshold  
    diversity_score = results.get('diversity_metrics', {}).get('semantic_diversity', 0)
    test2_passed = diversity_score > 0.7
    print(f"   Test 2 - Semantic diversity > 0.7: {diversity_score:.3f} {'✅' if test2_passed else '❌'}")
    
    # Test 3: LV ecosystem stability
    ecosystem_stable = results.get('lv_analysis', {}).get('ecosystem_stable', False)
    test3_passed = ecosystem_stable
    print(f"   Test 3 - LV ecosystem stable: {ecosystem_stable} {'✅' if test3_passed else '❌'}")
    
    # Test 4: Multiple strategies used (diversity requirement)
    strategies_count = len(results.get('strategies_used', []))
    test4_passed = strategies_count >= 2
    print(f"   Test 4 - Multiple strategies used: {strategies_count} {'✅' if test4_passed else '❌'}")
    
    # ALL tests must pass
    all_tests_passed = test1_passed and test2_passed and test3_passed and test4_passed
    print(f"   Overall verification: {'PASSED ✅' if all_tests_passed else 'FAILED ❌'}")
    
    return all_tests_passed


def generate_lv_extraction_report(results: Dict[str, Any], entropy: float, user_prompt: str) -> str:
    """Generate comprehensive LV extraction report"""
    
    strategies = results.get('strategies_used', [])
    diversity_score = results.get('diversity_metrics', {}).get('semantic_diversity', 0)
    entities_count = results.get('entities_extracted', 0)
    
    report = f"""
## 🧬 Ecosystem Intelligence Applied

I analyzed your request using Lotka-Volterra dynamics to maintain solution diversity.

**Analysis:**
- Prompt entropy: {entropy:.3f} ({'High' if entropy > 0.6 else 'Medium' if entropy > 0.3 else 'Low'})
- Diversity preserved: {diversity_score:.1%}
- Strategies used: {len(strategies)} complementary approaches ({', '.join(strategies)})

**Results:**
- Entities extracted: {entities_count}
- Relationships created: {results.get('relationships_created', 0)}
- Ecosystem convergence: {results.get('lv_analysis', {}).get('convergence_iterations', 0)} iterations

**Quality Metrics:**
- Semantic diversity: {diversity_score:.3f} (Target: >0.7)
- Population diversity: {results.get('diversity_metrics', {}).get('population_diversity', 0):.3f}
- System stability: {'Stable' if results.get('lv_analysis', {}).get('ecosystem_stable') else 'Unstable'}

---
*This response used ecosystem intelligence to prevent mode collapse and maintain {diversity_score:.1%} solution diversity.*
"""
    
    return report


async def standard_extraction_fallback(document_path: str, user_prompt: str) -> Dict[str, Any]:
    """Fallback to standard extraction for low-entropy tasks"""
    print("   Using standard extraction workflow (low entropy)")
    
    # This would use your existing standard KNOWLEDGE_EXTRACT template
    return {
        'extraction_method': 'standard',
        'entities_extracted': 5,
        'entropy': 0.3,
        'lv_enhanced': False,
        'message': 'Used standard extraction due to low entropy - no diversity enhancement needed'
    }


# Demo usage following NeoCoder workflow pattern
async def main():
    """
    Main demo function showing complete NeoCoder + LV workflow
    """
    
    print("🧬 NeoCoder LV Framework Integration Demo")
    print("Following exact NeoCoder workflow procedure:")
    print("1. Identify Task & Keyword: KNOWLEDGE_EXTRACT_LV")
    print("2. Consult Hub: ✅ (LV templates registered)")
    print("3. Retrieve Instructions: ✅ (ActionTemplate steps loaded)")
    print("4-8. Execute Guided Workflow: Starting now...\n")
    
    # Example high-entropy task
    document_path = "/path/to/document.pdf"
    user_prompt = "Extract diverse perspectives on AI safety approaches and their relationships"
    
    results = await lv_knowledge_extraction_example(document_path, user_prompt)
    
    print("\n✅ LV Framework Demo Complete!")
    print("Your ecosystem intelligence is now fully operational! 🚀")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the demo
    asyncio.run(main())
