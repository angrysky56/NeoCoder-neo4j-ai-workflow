#!/usr/bin/env python3
"""
Tool Summary Script for NeoCoder Framework

This script provides a clean summary of all registered tools by incarnation.
"""

import sys
import os

# Add src to path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

def main():
    """Generate a summary of all registered tools."""
    try:
        from mcp_neocoder.incarnation_registry import registry as inc_registry
        from mcp_neocoder.tool_registry import registry as tool_registry

        # Mock Neo4j driver for testing
        class MockDriver:
            async def session(self, database=None):
                return MockSession()

        class MockSession:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        # Discover incarnations
        inc_registry.discover()

        print("=" * 80)
        print("🚀 NEOCODER FRAMEWORK - TOOL SUMMARY")
        print("=" * 80)
        print(f"📊 Framework Status: {'✅ OPERATIONAL' if len(inc_registry.incarnations) > 0 else '❌ ERROR'}")
        print(f"📦 Incarnations Discovered: {len(inc_registry.incarnations)}")
        print("=" * 80)

        total_tools = 0
        driver = MockDriver()
        incarnation_data = []

        for inc_type, inc_class in inc_registry.incarnations.items():
            # Create instance and get tools
            instance = inc_registry.get_instance(inc_type, driver, "neo4j")
            if instance:
                # Get tool methods
                if hasattr(instance, 'list_tool_methods'):
                    tools = instance.list_tool_methods()
                elif hasattr(instance.__class__, '_tool_methods'):
                    tools = instance.__class__._tool_methods
                else:
                    tools = []

                incarnation_data.append({
                    'type': inc_type,
                    'class': inc_class.__name__,
                    'description': getattr(inc_class, 'description', 'No description'),
                    'tools': sorted(tools),
                    'count': len(tools)
                })
                total_tools += len(tools)

        # Sort by tool count (descending)
        incarnation_data.sort(key=lambda x: x['count'], reverse=True)

        # Display each incarnation
        for data in incarnation_data:
            print(f"\n📦 {data['type'].upper().replace('_', ' ')} INCARNATION")
            print(f"   Class: {data['class']}")
            print(f"   Description: {data['description']}")
            print(f"   Tools: {data['count']}")

            # Show tools in columns for better readability
            tools = data['tools']
            if tools:
                print("   Available Tools:")
                for i in range(0, len(tools), 2):
                    if i + 1 < len(tools):
                        print(f"     • {tools[i]:<30} • {tools[i+1]}")
                    else:
                        print(f"     • {tools[i]}")

        # Summary statistics
        print("\n" + "=" * 80)
        print("📈 SUMMARY STATISTICS")
        print("=" * 80)
        print(f"Total Incarnations: {len(incarnation_data)}")
        print(f"Total Tools: {total_tools}")
        print(f"Average Tools per Incarnation: {total_tools / len(incarnation_data):.1f}")

        # Top incarnations by tool count
        print("\n🏆 TOP INCARNATIONS BY TOOL COUNT:")
        for i, data in enumerate(incarnation_data[:3], 1):
            print(f"   {i}. {data['type'].replace('_', ' ').title()}: {data['count']} tools")

        print("=" * 80)
        print("🎯 Framework Ready for Use!")
        print("=" * 80)

        # Show breakdown by category if tool registry has been populated
        if tool_registry.tool_categories:
            print("\n📋 TOOL CATEGORIES:")
            for category, tools in tool_registry.tool_categories.items():
                print(f"   {category}: {len(tools)} tools")

    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
