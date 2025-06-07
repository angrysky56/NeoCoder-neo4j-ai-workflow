#!/usr/bin/env python3
"""
Script to add enhanced action templates to NeoCoder system
Integrates MVP Agent, Coder Agent, and Adaptive Engineering Lead protocols
"""

import asyncio
import json
from neo4j import AsyncGraphDatabase

async def add_enhanced_templates():
    """Add the enhanced action templates to Neo4j"""

    # Enhanced templates based on the protocols
    templates = [
        {
            "keyword": "MVP_DESIGN",
            "name": "MVP Design & Planning Workflow",
            "description": "Comprehensive MVP outline generation using structured exploration framework",
            "version": "1.0",
            "protocol_type": "mvp_agent",
            "steps": """1. **Phase 1: Core Principles (Why?)**
   - Define the Principle of Inquiry: What core problem does this MVP solve?
   - Establish primary value proposition
   - Align with ethical considerations (harm avoidance, wisdom, integrity, fairness, empathy)

2. **Phase 2: Dimensional Axes (What?)**
   - Intent: Specific purpose (expression, evocation, problem-solving)
   - Method: High-level approaches, techniques, constraints
   - Output: Tangible outcome (visual, textual, experiential)
   - Core Features: Minimum viable feature set prioritized by user need and feasibility
   - Out-of-Scope: Features explicitly excluded from MVP

3. **Phase 3: Recursive Frameworks (How?)**
   - Architectural Design: High-level software architecture (scalability, performance)
   - Technology Stack: Programming languages, frameworks, databases
   - Front-End: UI elements, responsiveness, accessibility
   - Back-End: Server logic, database interactions, integrations
   - Full-Stack Integration: Component integration and testing approach
   - AI/ML Integration: Model types, data requirements, evaluation metrics (if applicable)

4. **Phase 4: Constraints as Catalysts (What if?)**
   - Technical limitations: budget, time, infrastructure
   - Functional limitations: data availability, API restrictions
   - Innovation stimulation: How constraints drive creative solutions

5. **Phase 5: Controlled Emergence (How Else?)**
   - Controlled experimentation areas for novelty/unexpected solutions
   - A/B testing opportunities, algorithm parameter exploration
   - Surprise/novelty control aligned with core purpose

6. **Phase 6: Feedback Loops (What Next?)**
   - Validation strategy: unit, integration, user acceptance testing
   - Anti-hallucination mechanisms and bias detection
   - User feedback collection and integration processes
   - Reflection and re-contextualization mechanisms

7. **Phase 7: Adaptive Flexibility (What Now?)**
   - Future enhancement accommodation and scalability design
   - Meta-level development process adjustments
   - Version control and code quality assurance strategies

8. **Phase 8: Deliverable Structure**
   - Present MVP outline with clear headings and actionable bullet points
   - Flag uncertainties and suggest validation areas
   - Prioritize clarity and feasibility for MVP scope"""
        },
        {
            "keyword": "META_CODE",
            "name": "Meta-Cognitive AI Coding Protocol",
            "description": "Advanced coding workflow with meta-validation and fail-safe intelligence",
            "version": "1.0",
            "protocol_type": "coder_agent",
            "steps": """1. **🛠 Init (Observe & Understand)**
   - Observe: Understand repo structure, design patterns, domain architecture
   - Defer: Refrain from code generation until system understanding reaches threshold
   - Integrate: Align with existing conventions and architectural philosophy
   - Meta-Validate: Consistency, Completeness, Soundness, Expressiveness

2. **🚀 Execute (Targeted Implementation)**
   - Target: Modify primary source directly (no workaround scripts)
   - Scope: Enact minimum viable change to fix targeted issue
   - Leverage: Prefer existing abstractions over introducing new ones
   - Preserve: Assume complexity is intentional; protect advanced features
   - Hypothesize: "If X is modified, then Y should change in Z way"
   - Test: Create local validations specific to this hypothesis

3. **🔎 Validate (Verification & Review)**
   - Test: Define and run specific validation steps for each change
   - Verify: Confirm no degradation of existing behaviors or dependencies
   - Review: Self-audit for consistency with codebase patterns
   - Reflect & Refactor: Log rationale behind decisions

4. **📡 Communicate++ (Documentation)**
   - What: Issue + root cause, framed in architectural context
   - Where: File + line-level references
   - How: Precise code delta required
   - Why: Rationale including discarded alternatives
   - Trace: Show logical steps from diagnosis to decision
   - Context: Identify impacted modules, dependencies, workflows

5. **⚠️ Fail-Safe Intelligence**
   - Avoid: Workaround scripts, oversimplification, premature solutions
   - Flag Uncertainty: Surface confidence level and assumptions
   - Risk-Aware: Estimate impact level, guard against coupling effects"""
        },
        {
            "keyword": "PROJECT_LEAD",
            "name": "Adaptive Engineering Lead Protocol",
            "description": "Collaborative software development with understanding, execution, and iteration phases",
            "version": "1.0",
            "protocol_type": "adaptive_lead",
            "steps": """1. **Phase 1: Understanding & Planning (The Blueprint)**
   - Comprehensive Analysis: Analyze all materials, identify objectives and success criteria
   - Strategic Plan Development: Create detailed, testable task breakdown
   - Clarification & Confirmation: Present understanding, resolve ambiguities

2. **Phase 2: Execution & Iteration (The Build Cycle)**
   - Focused Implementation: One task at a time with coding protocol
     * Minimalism & Precision: Clean, efficient code only
     * Isolation: No sweeping changes or unrelated edits
     * Quality: Modular, well-commented, testable code
     * Non-Regression: Preserve existing functionality
   - Progress Reporting: Document accomplishments, file changes, testing instructions
   - Await Feedback: Pause for testing and feedback before next task

3. **Phase 3: Adaptability & Problem Solving (The Agile Response)**
   - Proactive Obstacle Management: Pause, articulate problems, propose alternatives
   - Responding to Quirks: Explain reasoning, treat as learning opportunities
   - Plan Evolution: Adapt based on insights, requirements, obstacles

4. **Interaction Style**
   - Methodical & Structured: Step-by-step, refer to plan
   - Collaborative Partner: Augment capabilities, proactive communication
   - Clarity & Conciseness: Clear explanations, avoid jargon
   - User-Centric: Prioritize goals and constraints
   - Continuous Learning: Understand preferences and nuances"""
        }
    ]

    driver = AsyncGraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "00000000"))

    try:
        async with driver.session(database="neo4j") as session:
            for template in templates:
                async def create_template(tx):
                    query = """
                    CREATE (t:ActionTemplate {
                        keyword: $keyword,
                        name: $name,
                        description: $description,
                        steps: $steps,
                        version: $version,
                        protocol_type: $protocol_type,
                        isCurrent: true,
                        created: datetime(),
                        updated: datetime()
                    })
                    """
                    return await tx.run(query, template)

                await session.execute_write(create_template)
                print(f"✅ Created enhanced template: {template['keyword']}")

        print("\n🎉 All enhanced action templates added successfully!")
        print("\nAvailable enhanced templates:")
        print("- MVP_DESIGN: Comprehensive MVP planning")
        print("- META_CODE: Meta-cognitive coding protocol")
        print("- PROJECT_LEAD: Adaptive engineering leadership")

    except Exception as e:
        print(f"❌ Error adding templates: {e}")
    finally:
        await driver.close()

if __name__ == "__main__":
    asyncio.run(add_enhanced_templates())
