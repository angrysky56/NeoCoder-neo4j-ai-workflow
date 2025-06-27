#!/usr/bin/env python

"""
LV Framework Neo4j Storage Implementation
========================================

Provides comprehensive Neo4j persistence for the Lotka-Volterra Ecosystem Intelligence Framework.
Handles configuration management, execution history, analytics, and knowledge storage.

Author: NeoCoder Hybrid Reasoning System with persistent intelligence
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import numpy as np
import hashlib

logger = logging.getLogger(__name__)


class LVNeo4jStorage:
    """
    Comprehensive Neo4j storage manager for LV Framework

    Handles all persistent storage operations for the Lotka-Volterra ecosystem,
    including configuration management, execution tracking, and analytics.
    """

    def __init__(self, neo4j_session):
        """
        Initialize LV Neo4j storage manager

        Args:
            neo4j_session: Active Neo4j database session
        """
        self.neo4j = neo4j_session
        logger.info("LV Neo4j Storage initialized")

    # ========================================
    # LV Configuration Management
    # ========================================

    async def store_lv_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Store LV configuration in Neo4j with versioning

        Args:
            config: LV configuration dictionary

        Returns:
            bool: Success status
        """
        try:
            query = """
            MERGE (cfg:LVConfiguration {framework_version: $framework_version})
            SET cfg += $config,
                cfg.updated_at = datetime(),
                cfg.configuration_hash = $config_hash
            RETURN cfg.framework_version as version
            """

            config_hash = hashlib.md5(json.dumps(config, sort_keys=True).encode()).hexdigest()[:12]

            async with self.neo4j as session:
                result = await session.run(
                    query,
                    framework_version=config['framework_version'],
                    config=config,
                    config_hash=config_hash
                )

                version = await result.single()
                if version:
                    logger.info(f"LV configuration stored: version {version['version']}, hash {config_hash}")
                    return True
                else:
                    logger.error("No version returned when storing LV configuration.")
                    return False

        except Exception as e:
            logger.error(f"Failed to store LV configuration: {e}")
            return False

    async def get_lv_configuration(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve current LV configuration from Neo4j

        Returns:
            Dict with LV configuration or None if not found
        """
        try:
            query = """
            MATCH (cfg:LVConfiguration)
            RETURN cfg as config
            ORDER BY cfg.updated_at DESC
            LIMIT 1
            """

            async with self.neo4j as session:
                result = await session.run(query)
                record = await result.single()

                if record:
                    config = dict(record['config'])
                    logger.info(f"Retrieved LV configuration: version {config.get('framework_version', 'unknown')}")
                    return config

        except Exception as e:
            logger.error(f"Failed to retrieve LV configuration: {e}")

        return None

    async def update_lv_configuration(self, updates: Dict[str, Any]) -> bool:
        """
        Update specific LV configuration parameters

        Args:
            updates: Dictionary of configuration updates

        Returns:
            bool: Success status
        """
        try:
            query = """
            MATCH (cfg:LVConfiguration)
            SET cfg += $updates,
                cfg.updated_at = datetime()
            RETURN cfg.framework_version as version
            """

            async with self.neo4j as session:
                result = await session.run(query, updates=updates)
                record = await result.single()

                if record:
                    logger.info(f"LV configuration updated: {list(updates.keys())}")
                    return True

        except Exception as e:
            logger.error(f"Failed to update LV configuration: {e}")
            return False
        return False

    # ========================================
    # LV Selection Results Storage
    # ========================================

    async def store_lv_selection_session(self,
                                       prompt: str,
                                       entropy: float,
                                       candidates: List[Dict[str, Any]],
                                       selected_outputs: List[Dict[str, Any]],
                                       convergence_data: Dict[str, Any],
                                       template_keyword: Optional[str] = None) -> str:
        """
        Store complete LV selection session in Neo4j

        Args:
            prompt: Original user prompt
            entropy: Calculated entropy level
            candidates: All candidate outputs
            selected_outputs: LV-selected outputs
            convergence_data: LV dynamics convergence information
            template_keyword: Template that triggered LV enhancement

        Returns:
            str: Session ID for tracking
        """
        try:
            session_id = hashlib.md5(f"{prompt}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
            prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]

            # Store main session
            session_query = """
            CREATE (session:LVSelectionSession {
                session_id: $session_id,
                prompt: $prompt,
                prompt_hash: $prompt_hash,
                entropy: $entropy,
                num_candidates: $num_candidates,
                num_selected: $num_selected,
                converged: $converged,
                iterations: $iterations,
                template_keyword: $template_keyword,
                diversity_score: $diversity_score,
                timestamp: datetime(),
                created_at: $created_at
            })
            RETURN session.session_id as id
            """

            diversity_score = self._calculate_session_diversity_score(selected_outputs)

            async with self.neo4j as session:
                result = await session.run(
                    session_query,
                    session_id=session_id,
                    prompt=prompt[:500],  # Truncate long prompts
                    prompt_hash=prompt_hash,
                    entropy=entropy,
                    num_candidates=len(candidates),
                    num_selected=len(selected_outputs),
                    converged=convergence_data.get('converged', False),
                    iterations=convergence_data.get('iterations', 0),
                    template_keyword=template_keyword,
                    diversity_score=diversity_score,
                    created_at=datetime.now().isoformat()
                )

                created_session = await result.single()

                if created_session:
                    # Store selected outputs
                    await self._store_session_outputs(session_id, selected_outputs)

                    # Store candidate metadata
                    await self._store_session_candidates(session_id, candidates)

                    logger.info(f"LV selection session stored: {session_id}")
                    return session_id

            # If no session was created, return empty string
            return ""

        except Exception as e:
            logger.error(f"Failed to store LV selection session: {e}")
            return ""

    async def _store_session_outputs(self, session_id: str, outputs: List[Dict[str, Any]]):
        """Store selected outputs for a session"""
        try:
            output_query = """
            MATCH (session:LVSelectionSession {session_id: $session_id})
            UNWIND $outputs as output
            CREATE (out:LVSelectedOutput {
                session_id: $session_id,
                content: output.content,
                population: output.population,
                quality_score: output.quality_score,
                novelty_score: output.novelty_score,
                content_hash: output.content_hash,
                selection_rank: output.rank
            })
            CREATE (session)-[:SELECTED]->(out)
            """

            # Add rank to outputs
            ranked_outputs = []
            for i, output in enumerate(outputs):
                output_copy = output.copy()
                output_copy['rank'] = i + 1
                ranked_outputs.append(output_copy)

            async with self.neo4j as session:
                await session.run(
                    output_query,
                    session_id=session_id,
                    outputs=ranked_outputs
                )

        except Exception as e:
            logger.error(f"Failed to store session outputs: {e}")

    async def _store_session_candidates(self, session_id: str, candidates: List[Dict[str, Any]]):
        """Store candidate metadata for a session"""
        try:
            candidate_query = """
            MATCH (session:LVSelectionSession {session_id: $session_id})
            UNWIND $candidates as candidate
            CREATE (cand:LVCandidate {
                session_id: $session_id,
                content_hash: candidate.content_hash,
                quality_score: candidate.quality_score,
                novelty_score: candidate.novelty_score,
                bias_score: candidate.bias_score,
                cost_score: candidate.cost_score
            })
            CREATE (session)-[:EVALUATED]->(cand)
            """

            async with self.neo4j as session:
                await session.run(
                    candidate_query,
                    session_id=session_id,
                    candidates=candidates
                )

        except Exception as e:
            logger.error(f"Failed to store session candidates: {e}")

    def _calculate_session_diversity_score(self, outputs: List[Dict[str, Any]]) -> float:
        """Calculate overall diversity score for session"""
        if len(outputs) < 2:
            return 0.0

        try:
            populations = [output.get('population', 0) for output in outputs]
            # Calculate entropy of population distribution
            total_pop = sum(populations)
            if total_pop > 0:
                normalized_pops = [p/total_pop for p in populations]
                entropy = -sum(p * np.log(p) for p in normalized_pops if p > 0)
                return float(entropy / np.log(len(populations)))
            return 0.0
        except Exception:
            return 0.0

    # ========================================
    # LV Execution History & Analytics
    # ========================================

    async def get_lv_execution_history(self,
                                     template_keyword: Optional[str] = None,
                                     limit: int = 20,
                                     min_entropy: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Retrieve LV execution history for analysis

        Args:
            template_keyword: Filter by specific template
            limit: Maximum number of records
            min_entropy: Minimum entropy threshold

        Returns:
            List of execution records
        """
        try:
            conditions = []
            params: Dict[str, Any] = {"limit": limit}

            if template_keyword:
                conditions.append("session.template_keyword = $template_keyword")
                params["template_keyword"] = template_keyword

            if min_entropy is not None:
                conditions.append("session.entropy >= $min_entropy")
                params["min_entropy"] = min_entropy

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            query = f"""
            MATCH (session:LVSelectionSession)
            {where_clause}
            RETURN session {{
                .session_id,
                .prompt_hash,
                .entropy,
                .num_candidates,
                .num_selected,
                .converged,
                .iterations,
                .template_keyword,
                .diversity_score,
                .timestamp
            }} as session_data
            ORDER BY session.timestamp DESC
            LIMIT $limit
            """

            async with self.neo4j as session:
                result = await session.run(query, **params)
                records = await result.data()

                history = [record['session_data'] for record in records]
                logger.info(f"Retrieved {len(history)} LV execution records")
                return history

        except Exception as e:
            logger.error(f"Failed to retrieve LV execution history: {e}")
            return []

    async def get_lv_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive LV performance metrics

        Returns:
            Dict with performance analytics
        """
        try:
            metrics_query = """
            MATCH (session:LVSelectionSession)
            RETURN
                count(session) as total_executions,
                avg(session.entropy) as avg_entropy,
                avg(session.diversity_score) as avg_diversity,
                avg(session.iterations) as avg_iterations,
                sum(CASE WHEN session.converged THEN 1 ELSE 0 END) as converged_count,
                avg(session.num_selected) as avg_selected,
                collect(DISTINCT session.template_keyword) as templates_used
            """

            async with self.neo4j as session:
                result = await session.run(metrics_query)
                record = await result.single()

                if record:
                    metrics = {
                        'total_lv_executions': record['total_executions'],
                        'performance_metrics': {
                            'avg_entropy': float(record['avg_entropy'] or 0),
                            'diversity_preservation_score': float(record['avg_diversity'] or 0),
                            'stability_rate': float(record['converged_count'] / max(record['total_executions'], 1)),
                            'avg_convergence_iterations': float(record['avg_iterations'] or 0),
                            'avg_outputs_selected': float(record['avg_selected'] or 0)
                        },
                        'templates_enhanced': [t for t in record['templates_used'] if t],
                        'generated_at': datetime.now().isoformat()
                    }

                    logger.info(f"Generated LV performance metrics: {metrics['total_lv_executions']} executions")
                    return metrics

        except Exception as e:
            logger.error(f"Failed to generate LV performance metrics: {e}")
            return {
                'total_lv_executions': 0,
                'performance_metrics': {},
                'error': str(e)
            }
        return {
            'total_lv_executions': 0,
            'performance_metrics': {},
            'error': 'Unknown error'
        }

    # ========================================
    # Knowledge Storage for LV Templates
    # ========================================

    async def store_lv_extracted_knowledge(self,
                                         entities: List[Dict[str, Any]],
                                         relations: List[Dict[str, Any]],
                                         session_id: str,
                                         source_document: str) -> Dict[str, Any]:
        """
        Store knowledge extracted by LV-enhanced templates

        Args:
            entities: Extracted entities for Neo4j
            relations: Extracted relationships for Neo4j
            session_id: LV session that performed extraction
            source_document: Source document path/identifier

        Returns:
            Storage results summary
        """
        try:
            results = {
                'entities_stored': 0,
                'relations_stored': 0,
                'extraction_session_id': session_id,
                'source_document': source_document
            }

            # Store extraction metadata
            extraction_query = """
            CREATE (extraction:LVKnowledgeExtraction {
                session_id: $session_id,
                source_document: $source_document,
                num_entities: $num_entities,
                num_relations: $num_relations,
                extracted_at: datetime(),
                extraction_method: 'lv_enhanced'
            })
            RETURN extraction.session_id as stored_session
            """

            async with self.neo4j as session:
                await session.run(
                    extraction_query,
                    session_id=session_id,
                    source_document=source_document,
                    num_entities=len(entities),
                    num_relations=len(relations)
                )

            # Store entities using existing create_entities pattern
            if entities:
                entity_query = """
                UNWIND $entities as entity
                MERGE (e:Entity {name: entity.name})
                SET e.entityType = entity.entityType,
                    e.lv_extracted = true,
                    e.extraction_session = $session_id,
                    e.source_document = $source_document,
                    e.last_updated = datetime()
                WITH e, entity
                UNWIND entity.observations as obs
                MERGE (e)-[:HAS_OBSERVATION]->(o:Observation {content: obs})
                SET o.lv_extracted = true,
                    o.extraction_session = $session_id
                """

                async with self.neo4j as session:
                    await session.run(
                        entity_query,
                        entities=entities,
                        session_id=session_id,
                        source_document=source_document
                    )
                    results['entities_stored'] = len(entities)

            # Store relations using existing create_relations pattern
            if relations:
                relation_query = """
                UNWIND $relations as rel
                MATCH (from:Entity {name: rel.from})
                MATCH (to:Entity {name: rel.to})
                MERGE (from)-[r:RELATION {type: rel.relationType}]->(to)
                SET r.lv_extracted = true,
                    r.extraction_session = $session_id,
                    r.source_document = $source_document,
                    r.created_at = datetime()
                """

                async with self.neo4j as session:
                    await session.run(
                        relation_query,
                        relations=relations,
                        session_id=session_id,
                        source_document=source_document
                    )
                    results['relations_stored'] = len(relations)

            logger.info(f"LV knowledge stored: {results['entities_stored']} entities, {results['relations_stored']} relations")
            return results

        except Exception as e:
            logger.error(f"Failed to store LV extracted knowledge: {e}")
            return {'error': str(e), 'entities_stored': 0, 'relations_stored': 0}

    async def get_lv_knowledge_extraction_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve history of LV knowledge extractions

        Args:
            limit: Maximum number of records

        Returns:
            List of extraction records
        """
        try:
            query = """
            MATCH (extraction:LVKnowledgeExtraction)
            RETURN extraction {
                .session_id,
                .source_document,
                .num_entities,
                .num_relations,
                .extracted_at,
                .extraction_method
            } as extraction_data
            ORDER BY extraction.extracted_at DESC
            LIMIT $limit
            """

            async with self.neo4j as session:
                result = await session.run(query, limit=limit)
                records = await result.data()

                history = [record['extraction_data'] for record in records]
                logger.info(f"Retrieved {len(history)} LV extraction records")
                return history

        except Exception as e:
            logger.error(f"Failed to retrieve LV extraction history: {e}")
            return []

    # ========================================
    # LV Template Management
    # ========================================

    async def register_lv_templates(self) -> bool:
        """
        Register LV-enhanced templates in Neo4j ActionTemplate system

        Returns:
            bool: Success status
        """
        try:
            lv_templates = [
                {
                    'keyword': 'KNOWLEDGE_EXTRACT_LV',
                    'name': 'LV-Enhanced Knowledge Extraction',
                    'description': 'Extract knowledge using ecological dynamics for strategy diversity',
                    'category': 'knowledge_management',
                    'version': '1.0',
                    'steps': [
                        'Analyze document entropy and complexity',
                        'Generate multiple extraction strategies using LV dynamics',
                        'Select optimal strategies based on ecosystem balance',
                        'Execute extractions with diversity preservation',
                        'Store results in Neo4j and Qdrant with full attribution',
                        'Record LV session metrics for continuous learning'
                    ],
                    'lv_enhanced': True
                },
                {
                    'keyword': 'KNOWLEDGE_QUERY_LV',
                    'name': 'LV-Enhanced Knowledge Query',
                    'description': 'Query knowledge using multi-perspective LV-guided search',
                    'category': 'knowledge_management',
                    'version': '1.0',
                    'steps': [
                        'Estimate query entropy and context complexity',
                        'Generate diverse search strategies across Neo4j and Qdrant',
                        'Apply LV selection to prevent search mode collapse',
                        'Execute multi-perspective knowledge synthesis',
                        'Provide results with full source attribution',
                        'Record diversity metrics and performance data'
                    ],
                    'lv_enhanced': True
                },
                {
                    'keyword': 'LV_SELECT',
                    'name': 'Generic LV Enhancement',
                    'description': 'Apply LV dynamics to any workflow for diversity preservation',
                    'category': 'workflow_enhancement',
                    'version': '1.0',
                    'steps': [
                        'Calculate prompt entropy for enhancement decision',
                        'Generate multiple execution strategies for any template',
                        'Apply Lotka-Volterra dynamics for strategy selection',
                        'Execute selected strategies with ecosystem balance',
                        'Synthesize results maintaining diversity',
                        'Store execution analytics for system optimization'
                    ],
                    'lv_enhanced': True
                }
            ]

            template_query = """
            UNWIND $templates as template
            MERGE (t:ActionTemplate {keyword: template.keyword})
            SET t += template,
                t.isCurrent = true,
                t.registered_at = datetime(),
                t.framework = 'LV_Ecosystem'
            """

            async with self.neo4j as session:
                await session.run(template_query, templates=lv_templates)

            logger.info(f"Registered {len(lv_templates)} LV-enhanced templates")
            return True

        except Exception as e:
            logger.error(f"Failed to register LV templates: {e}")
            return False


# Export main storage class
__all__ = ['LVNeo4jStorage']
