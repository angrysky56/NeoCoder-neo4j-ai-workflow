#!/usr/bin/env python3
"""
Add LV Framework Tools to Knowledge Graph Incarnation

This script adds the LV framework functions as MCP tools
"""

import os

# The LV tools to add to the knowledge graph incarnation
LV_TOOLS_CODE = '''
    # ============= LV FRAMEWORK TOOLS =============
    # Added by add_lv_tools.py
    
    async def test_lv_framework(
        self,
        test_case: str = Field(
            default="basic",
            description="Type of test: 'basic', 'stress', 'diversity', or 'stability'"
        )
    ) -> List[types.TextContent]:
        """Test the Lotka-Volterra framework functionality"""
        try:
            # Initialize LV integration if not already done
            if not hasattr(self, '_lv_integration'):
                from ..lv_integration import NeoCoder_LV_Integration
                self._lv_integration = NeoCoder_LV_Integration(
                    self.driver,
                    getattr(self, 'qdrant_client', None)
                )
            
            results = await self._lv_integration.test_lv_framework(test_case)
            
            response = f"# LV Framework Test Results\\n\\n"
            response += f"Test Type: {results.get('test_type', 'unknown')}\\n"
            response += f"Test Passed: {'✅ Yes' if results.get('test_passed') else '❌ No'}\\n\\n"
            
            if 'components_tested' in results:
                response += f"## Components Tested\\n"
                for component in results['components_tested']:
                    response += f"- {component}\\n"
                response += "\\n"
            
            if 'errors' in results and results['errors']:
                response += f"## Errors\\n"
                for error in results['errors']:
                    response += f"- {error}\\n"
                    
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error testing LV framework: {e}")]
    
    async def estimate_prompt_entropy(
        self,
        prompt: str = Field(..., description="The prompt to analyze for entropy"),
        context_history: Optional[List[str]] = Field(
            default=None,
            description="Previous prompts for context (optional)"
        )
    ) -> List[types.TextContent]:
        """Estimate the entropy of a prompt to determine if LV enhancement would be beneficial"""
        try:
            from ..lv_ecosystem import EntropyEstimator
            
            estimator = EntropyEstimator()
            entropy = estimator.estimate_prompt_entropy(prompt, context_history)
            
            # Determine behavioral mode
            if entropy < 0.3:
                mode = "PRECISION MODE"
                weights = "Quality: 90%, Novelty: 0%"
                recommendation = "Use standard templates - low uncertainty"
            elif entropy < 0.6:
                mode = "BALANCED MODE"
                weights = "Quality: 60%, Novelty: 30%"
                recommendation = "LV enhancement beneficial - moderate uncertainty"
            else:
                mode = "CREATIVITY MODE"
                weights = "Quality: 20%, Novelty: 70%"
                recommendation = "LV enhancement highly recommended - high uncertainty"
            
            response = f"""# Entropy Analysis

**Prompt:** "{prompt[:100]}{'...' if len(prompt) > 100 else ''}"

**Entropy Score:** {entropy:.3f}

**Behavioral Mode:** {mode}
**Weight Distribution:** {weights}

**Recommendation:** {recommendation}

## Interpretation
- Entropy < 0.3: Factual/deterministic queries → Standard execution
- Entropy 0.3-0.6: Analytical tasks → Balanced LV enhancement  
- Entropy > 0.6: Creative/exploratory tasks → Maximum LV diversity

{'**Context History Considered:** Yes' if context_history else '**Note:** No context history provided'}
"""
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error estimating entropy: {e}")]
    
    async def enhance_template_with_lv(
        self,
        template_keyword: str = Field(..., description="Template keyword (e.g., 'FIX', 'FEATURE')"),
        prompt: str = Field(..., description="The task prompt"),
        context: Optional[Dict[str, Any]] = Field(
            default=None,
            description="Additional context for the template"
        )
    ) -> List[types.TextContent]:
        """Apply LV enhancement to any NeoCoder template based on entropy"""
        try:
            if not hasattr(self, '_lv_integration'):
                from ..lv_integration import NeoCoder_LV_Integration
                self._lv_integration = NeoCoder_LV_Integration(
                    self.driver,
                    getattr(self, 'qdrant_client', None)
                )
            
            # Build context
            full_context = context or {}
            full_context['prompt'] = prompt
            
            # Enhance the template
            results = await self._lv_integration.enhance_existing_template(
                template_keyword,
                full_context
            )
            
            response = f"# LV-Enhanced Template Execution\\n\\n"
            response += f"**Template:** {template_keyword}\\n"
            response += f"**Entropy:** {results.get('entropy', 'N/A')}\\n"
            response += f"**Enhanced:** {'Yes' if results.get('enhanced_execution') else 'No'}\\n\\n"
            
            if 'strategies_used' in results:
                response += "## Strategies Applied\\n"
                for strategy in results['strategies_used']:
                    response += f"- {strategy}\\n"
                response += "\\n"
            
            if 'lv_analysis' in results:
                analysis = results['lv_analysis']
                response += f"## LV Analysis\\n"
                response += f"- Diversity Score: {analysis.get('diversity_metrics', {}).get('semantic_diversity', 'N/A')}\\n"
                response += f"- Convergence Iterations: {analysis.get('convergence_iterations', 'N/A')}\\n"
                
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error enhancing template: {e}")]
    
    async def get_lv_dashboard(self) -> List[types.TextContent]:
        """Get LV ecosystem monitoring dashboard data"""
        try:
            if not hasattr(self, '_lv_integration'):
                from ..lv_integration import NeoCoder_LV_Integration
                self._lv_integration = NeoCoder_LV_Integration(
                    self.driver,
                    getattr(self, 'qdrant_client', None)
                )
            
            dashboard = await self._lv_integration.create_lv_dashboard_data()
            
            response = "# 🧬 LV Ecosystem Dashboard\\n\\n"
            
            if 'error' in dashboard:
                response += f"Error: {dashboard['error']}\\n"
                return [types.TextContent(type="text", text=response)]
            
            response += f"**Status:** {dashboard.get('status', 'unknown')}\\n"
            response += f"**Total Executions:** {dashboard.get('total_lv_executions', 0)}\\n\\n"
            
            if 'performance_metrics' in dashboard:
                metrics = dashboard['performance_metrics']
                response += "## Performance Metrics\\n"
                response += f"- Average Convergence: {metrics.get('average_convergence_iterations', 'N/A')} iterations\\n"
                response += f"- Stability Rate: {metrics.get('stability_rate', 'N/A')}\\n"
                response += f"- Diversity Preservation: {metrics.get('diversity_preservation_score', 'N/A')}\\n\\n"
            
            if 'entropy_distribution' in dashboard:
                dist = dashboard['entropy_distribution']
                response += "## Entropy Distribution\\n"
                response += f"- Low Entropy: {dist.get('low_entropy_percentage', 0):.0%}\\n"
                response += f"- Medium Entropy: {dist.get('medium_entropy_percentage', 0):.0%}\\n"
                response += f"- High Entropy: {dist.get('high_entropy_percentage', 0):.0%}\\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error generating dashboard: {e}")]
'''

def add_lv_tools():
    """Add LV tools to the knowledge graph incarnation"""
    
    # Path to the knowledge graph incarnation file
    kg_file = "/home/ty/Repositories/NeoCoder-neo4j-ai-workflow/src/mcp_neocoder/incarnations/knowledge_graph_incarnation.py"
    
    # Read the current file
    with open(kg_file, 'r') as f:
        content = f.read()
    
    # Check if LV tools already added
    if "LV FRAMEWORK TOOLS" in content:
        print("❌ LV tools already added to knowledge graph incarnation!")
        return False
    
    # Find the last method (open_nodes) and add our tools after it
    # We'll add before the final class closing
    
    # Find the last occurrence of a method definition
    lines = content.split('\n')
    insert_index = -1
    
    # Find where to insert (before the last few lines of the file)
    for i in range(len(lines) - 1, 0, -1):
        if lines[i].strip() and not lines[i].strip().startswith('#'):
            # Found last non-empty, non-comment line
            insert_index = i
            break
    
    if insert_index == -1:
        print("❌ Could not find insertion point!")
        return False
    
    # Insert the LV tools
    lines.insert(insert_index, LV_TOOLS_CODE)
    
    # Write back
    new_content = '\n'.join(lines)
    with open(kg_file, 'w') as f:
        f.write(new_content)
    
    print("✅ Successfully added LV tools to knowledge graph incarnation!")
    print("\nAdded tools:")
    print("  - test_lv_framework: Test LV functionality")
    print("  - estimate_prompt_entropy: Analyze prompt entropy")
    print("  - enhance_template_with_lv: Apply LV enhancement to any template")
    print("  - get_lv_dashboard: Monitor LV ecosystem health")
    print("\n⚠️  Remember to restart Claude Desktop for changes to take effect!")
    
    return True

if __name__ == "__main__":
    add_lv_tools()
