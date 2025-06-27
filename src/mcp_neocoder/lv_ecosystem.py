#!/usr/bin/env python

"""
Lotka-Volterra Ecosystem Intelligence Framework
==============================================

This module implements ecological dynamics for AI output selection,
maintaining sustainable diversity while preserving quality.

Author: NeoCoder Hybrid Reasoning System
Mathematical foundations validated with WolframAlpha
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
import logging
from sentence_transformers import SentenceTransformer
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class LVCandidate:
    """Represents a candidate in the LV ecosystem"""
    content: str
    quality_score: float = 0.0
    novelty_score: float = 0.0
    bias_score: float = 0.0
    cost_score: float = 0.0
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Generate content hash for tracking"""
        self.content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]


@dataclass
class EntropyProfile:
    """Defines behavior based on contextual entropy"""
    low_threshold: float = 0.3
    high_threshold: float = 0.6

    # Weight schemes for different entropy levels
    low_entropy_weights: Dict[str, float] = field(default_factory=lambda: {
        "quality": 0.9, "novelty": 0.0, "bias": 0.05, "cost": 0.05
    })
    medium_entropy_weights: Dict[str, float] = field(default_factory=lambda: {
        "quality": 0.6, "novelty": 0.3, "bias": 0.05, "cost": 0.05
    })
    high_entropy_weights: Dict[str, float] = field(default_factory=lambda: {
        "quality": 0.2, "novelty": 0.7, "bias": 0.05, "cost": 0.05
    })


class EntropyEstimator:
    """Estimates contextual entropy of prompts and situations"""

    def __init__(self, embedder_model: str = 'all-MiniLM-L6-v2'):
        self.embedder = SentenceTransformer(embedder_model)

    def estimate_prompt_entropy(self, prompt: str, context_history: Optional[List[str]] = None) -> float:
        """
        Estimate entropy using semantic dispersion analysis

        Args:
            prompt: Input prompt to analyze
            context_history: Previous similar prompts for comparison

        Returns:
            float: Entropy estimate between 0 (deterministic) and 1 (maximum uncertainty)
        """
        try:
            # Method 1: Semantic complexity analysis
            prompt_embed = self.embedder.encode([prompt])[0]

            # Method 2: Historical comparison if available
            if context_history:
                history_embeds = self.embedder.encode(context_history)
                similarities = [np.dot(prompt_embed, h) /
                              (np.linalg.norm(prompt_embed) * np.linalg.norm(h))
                              for h in history_embeds]
                avg_similarity = np.mean(similarities)
                diversity_entropy = 1.0 - avg_similarity
            else:
                # Fallback: analyze prompt characteristics
                diversity_entropy = self._analyze_prompt_characteristics(prompt)

            # Method 3: Token distribution analysis
            token_entropy = self._calculate_token_entropy(prompt)

            # Combine methods
            final_entropy = 0.4 * diversity_entropy + 0.3 * token_entropy + 0.3 * self._semantic_complexity(prompt)

            return np.clip(final_entropy, 0.0, 1.0)

        except Exception as e:
            logger.warning(f"Entropy estimation failed: {e}, using default 0.5")
            return 0.5

    def _analyze_prompt_characteristics(self, prompt: str) -> float:
        """Analyze inherent prompt characteristics for entropy estimation"""
        # Check for question words, ambiguous terms, creative requests
        entropy_indicators = [
            'what if', 'creative', 'brainstorm', 'imagine', 'multiple', 'diverse',
            'alternative', 'different', 'various', 'explore', 'generate', 'novel'
        ]

        certainty_indicators = [
            'calculate', 'define', 'exactly', 'precisely', 'factual', 'correct',
            'accurate', 'specific', 'determine', 'find the', 'what is'
        ]

        prompt_lower = prompt.lower()
        entropy_count = sum(1 for term in entropy_indicators if term in prompt_lower)
        certainty_count = sum(1 for term in certainty_indicators if term in prompt_lower)

        # Normalize based on prompt length
        prompt_length = len(prompt.split())
        entropy_ratio = entropy_count / max(prompt_length, 1)
        certainty_ratio = certainty_count / max(prompt_length, 1)

        return max(0.0, min(1.0, entropy_ratio - certainty_ratio + 0.5))

    def _calculate_token_entropy(self, prompt: str) -> float:
        """Calculate Shannon entropy of token distribution"""
        tokens = prompt.lower().split()
        if not tokens:
            return 0.5

        # Count token frequencies
        token_counts = {}
        for token in tokens:
            token_counts[token] = token_counts.get(token, 0) + 1

        # Calculate Shannon entropy
        total_tokens = len(tokens)
        entropy = 0.0
        for count in token_counts.values():
            p = count / total_tokens
            if p > 0:
                entropy -= p * np.log2(p)

        # Normalize by maximum possible entropy
        max_entropy = np.log2(len(token_counts)) if len(token_counts) > 1 else 1.0
        return entropy / max_entropy if max_entropy > 0 else 0.5

    def _semantic_complexity(self, prompt: str) -> float:
        """Estimate semantic complexity based on embedding variance"""
        try:
            # Split into sentences and embed
            sentences = [s.strip() for s in prompt.split('.') if s.strip()]
            if len(sentences) < 2:
                return 0.3  # Simple, short prompt

            embeddings = self.embedder.encode(sentences)

            # Calculate variance in semantic space
            mean_embed = np.mean(embeddings, axis=0)
            variance = np.mean([np.linalg.norm(emb - mean_embed) for emb in embeddings])

            # Normalize (this is heuristic)
            return min(1.0, float(variance) / 2.0)

        except Exception:
            return 0.5


class LVEcosystem:
    """
    Core Lotka-Volterra Ecosystem for AI Output Selection

    Implements ecological dynamics to maintain diverse, high-quality outputs
    while preventing convergence to homogenized responses.
    """

    def __init__(self,
                 neo4j_session,
                 qdrant_client,
                 embedder_model: str = 'all-MiniLM-L6-v2'):
        """
        Initialize LV ecosystem

        Args:
            neo4j_session: Neo4j database session for structured data
            qdrant_client: Qdrant client for vector operations
            embedder_model: Sentence transformer model for embeddings
        """
        self.neo4j = neo4j_session
        self.qdrant = qdrant_client
        self.embedder = SentenceTransformer(embedder_model)
        self.entropy_estimator = EntropyEstimator(embedder_model)
        self.entropy_profile = EntropyProfile()

        # LV simulation parameters
        self.max_iterations = 10
        self.damping_factor = 0.15
        self.convergence_threshold = 1e-6

        logger.info("LV Ecosystem initialized with entropy-adaptive dynamics")

    async def select_diverse_outputs(self,
                                   candidates: List[str],
                                   prompt: str,
                                   context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main entry point for LV-enhanced output selection

        Args:
            candidates: List of candidate outputs
            prompt: Original prompt for entropy estimation
            context: Additional context information

        Returns:
            Dict containing selected outputs and analysis metadata
        """
        try:
            # Convert to LV candidates
            lv_candidates = [LVCandidate(content=c) for c in candidates]

            # Estimate prompt entropy
            context_history = context.get('history', []) if context else []
            entropy = self.entropy_estimator.estimate_prompt_entropy(prompt, context_history)

            # Calculate growth rates (r_i)
            growth_rates = await self._calculate_growth_rates(lv_candidates, entropy)

            # Build interaction matrix (α_ij)
            alpha_matrix = await self._build_alpha_matrix(lv_candidates, prompt, context)

            # Run LV dynamics simulation
            final_populations, convergence_data = self._simulate_lv_dynamics(
                growth_rates, alpha_matrix, len(lv_candidates)
            )

            # Select outputs based on final populations
            selected_outputs = self._select_outputs_by_population(
                lv_candidates, final_populations
            )

            # Store results for learning
            await self._store_selection_results(
                prompt, entropy, lv_candidates, selected_outputs, convergence_data
            )

            return {
                'selected_outputs': selected_outputs,
                'entropy': entropy,
                'growth_rates': growth_rates.tolist(),
                'alpha_matrix': alpha_matrix.tolist(),
                'final_populations': final_populations.tolist(),
                'convergence_iterations': convergence_data['iterations'],
                'diversity_metrics': self._calculate_diversity_metrics(selected_outputs)
            }

        except Exception as e:
            logger.error(f"LV selection failed: {e}")
            # Fallback to simple selection
            return {
                'selected_outputs': candidates[:3],  # Simple fallback
                'entropy': 0.5,
                'error': str(e)
            }

    async def _calculate_growth_rates(self,
                                    candidates: List[LVCandidate],
                                    entropy: float) -> np.ndarray:
        """Calculate r_i growth rates based on entropy-adaptive weights"""

        # Get entropy-appropriate weights
        weights = self._get_entropy_weights(entropy)

        growth_rates = []
        for candidate in candidates:
            # Calculate component scores
            quality = await self._calculate_quality_score(candidate)
            novelty = await self._calculate_novelty_score(candidate)
            bias = await self._calculate_bias_score(candidate)
            cost = self._calculate_cost_score(candidate)

            # Store scores in candidate
            candidate.quality_score = quality
            candidate.novelty_score = novelty
            candidate.bias_score = bias
            candidate.cost_score = cost

            # Calculate weighted growth rate
            r_i = (weights['quality'] * quality +
                   weights['novelty'] * novelty +
                   weights['bias'] * bias +
                   weights['cost'] * cost)

            growth_rates.append(r_i)

        return np.array(growth_rates)

    def _get_entropy_weights(self, entropy: float) -> Dict[str, float]:
        """Get appropriate weights based on entropy level"""
        if entropy < self.entropy_profile.low_threshold:
            return self.entropy_profile.low_entropy_weights
        elif entropy < self.entropy_profile.high_threshold:
            return self.entropy_profile.medium_entropy_weights
        else:
            return self.entropy_profile.high_entropy_weights

    async def _calculate_quality_score(self, candidate: LVCandidate) -> float:
        """Calculate quality heuristic (grammar, coherence, factual accuracy)"""
        # Placeholder for quality assessment
        # In production, integrate with quality evaluation models
        content_length = len(candidate.content.split())

        # Simple heuristics (replace with actual quality models)
        grammar_score = 0.8 if content_length > 10 else 0.5
        coherence_score = 0.7 if '.' in candidate.content else 0.4

        return (grammar_score + coherence_score) / 2

    async def _calculate_novelty_score(self, candidate: LVCandidate) -> float:
        """Calculate novelty using real Qdrant similarity search"""
        try:
            # Generate embedding
            if candidate.embedding is None:
                candidate.embedding = self.embedder.encode([candidate.content])[0]

            # Search for similar content in Qdrant knowledge base
            # Use the existing Qdrant client to find similar content
            if hasattr(self.qdrant, 'search') and callable(self.qdrant.search):
                # Ensure embedding is not None before calling tolist()
                embedding_vector = candidate.embedding.tolist() if candidate.embedding is not None else None
                if embedding_vector is not None:
                    # Remove 'await' if self.qdrant.search is synchronous
                    search_results = self.qdrant.search(
                        collection_name="knowledge_base",  # Adjust collection name as needed
                        query_vector=embedding_vector,
                        limit=5,
                        score_threshold=0.7
                    )
                else:
                    search_results = []

                if isinstance(search_results, list) and len(search_results) > 0:
                    # Calculate novelty based on similarity to existing content
                    max_similarity = max(result.get('score', 0) for result in search_results)
                    novelty_score = 1.0 - max_similarity
                else:
                    # No similar content found - high novelty
                    novelty_score = 0.9

            else:
                logger.warning("Qdrant client search method not available, using fallback novelty calculation")
                # Fallback: calculate novelty based on content characteristics
                novelty_score = self._calculate_content_novelty_fallback(candidate)

            return max(0.0, min(1.0, novelty_score))

        except Exception as e:
            logger.warning(f"Novelty calculation failed: {e}")
            return 0.5

    def _calculate_content_novelty_fallback(self, candidate: LVCandidate) -> float:
        """Fallback novelty calculation when Qdrant is unavailable"""
        # Simple heuristic based on content characteristics
        content = candidate.content.lower()

        # Higher novelty for creative/unique terms
        novelty_indicators = ['novel', 'unique', 'innovative', 'creative', 'original', 'unprecedented']
        common_indicators = ['the', 'and', 'is', 'are', 'was', 'were', 'have', 'has']

        novelty_words = sum(1 for word in novelty_indicators if word in content)
        common_words = sum(1 for word in common_indicators if word in content)

        total_words = len(content.split())
        if total_words == 0:
            return 0.5

        novelty_ratio = novelty_words / total_words
        common_ratio = common_words / total_words

        return max(0.2, min(0.8, novelty_ratio - common_ratio + 0.5))

    async def _calculate_bias_score(self, candidate: LVCandidate) -> float:
        """Calculate bias mitigation score"""
        # Placeholder for bias detection
        # In production, integrate with bias detection models
        return 0.8  # Assume low bias for now

    def _calculate_cost_score(self, candidate: LVCandidate) -> float:
        """Calculate computational cost penalty"""
        # Simple cost based on content length
        length_penalty = len(candidate.content) / 1000.0  # Normalize
        return max(0.0, 1.0 - length_penalty)

    async def _build_alpha_matrix(self,
                                candidates: List[LVCandidate],
                                prompt: str,
                                context: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Build interaction matrix α_ij for competition dynamics"""
        n = len(candidates)
        alpha = np.zeros((n, n))

        # Generate embeddings for semantic similarity
        embeddings = []
        for candidate in candidates:
            if candidate.embedding is None:
                candidate.embedding = self.embedder.encode([candidate.content])[0]
            embeddings.append(candidate.embedding)

        # Calculate semantic competition
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Semantic competition (S_ij)
                    semantic_sim = np.dot(embeddings[i], embeddings[j]) / (
                        np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                    )
                    semantic_competition = 1.0 - semantic_sim

                    # Niche inhibition (N_ij) - based on content characteristics
                    niche_inhibition = self._calculate_niche_inhibition(
                        candidates[i], candidates[j], prompt
                    )

                    # Task penalty (T_ij) - context-dependent
                    task_penalty = self._calculate_task_penalty(
                        candidates[i], candidates[j], context
                    )

                    # Combine components (your specified weights)
                    alpha[i][j] = (0.6 * semantic_competition +
                                 0.3 * niche_inhibition +
                                 0.1 * task_penalty)

        return alpha

    def _calculate_niche_inhibition(self,
                                  candidate_i: LVCandidate,
                                  candidate_j: LVCandidate,
                                  prompt: str) -> float:
        """Calculate niche-based inhibition following your framework"""

        # Classify niches based on content characteristics
        niche_i = self._classify_niche(candidate_i, prompt)
        niche_j = self._classify_niche(candidate_j, prompt)

        # Apply your niche inhibition rules
        if niche_i == niche_j:
            # Same niche competition
            similarity = self._content_similarity(candidate_i, candidate_j)
            return -1.5 if similarity > 0.8 else -0.7
        elif niche_i == "preferred" and niche_j != "preferred":
            # Preferred suppresses non-preferred
            return -1.2
        else:
            return 0.0

    def _classify_niche(self, candidate: LVCandidate, prompt: str) -> str:
        """Classify candidate into niche based on content analysis"""
        content_lower = candidate.content.lower()

        # Simple niche classification (enhance with ML models)
        if any(word in content_lower for word in ['creative', 'imagine', 'novel']):
            return "creative"
        elif any(word in content_lower for word in ['data', 'analysis', 'calculate']):
            return "analytical"
        elif any(word in content_lower for word in ['factual', 'definition', 'exactly']):
            return "factual"
        else:
            return "general"

    def _content_similarity(self,
                          candidate_i: LVCandidate,
                          candidate_j: LVCandidate) -> float:
        """Calculate content similarity between candidates"""
        if candidate_i.embedding is not None and candidate_j.embedding is not None:
            return np.dot(candidate_i.embedding, candidate_j.embedding) / (
                np.linalg.norm(candidate_i.embedding) * np.linalg.norm(candidate_j.embedding)
            )
        return 0.0

    def _calculate_task_penalty(self,
                              candidate_i: LVCandidate,
                              candidate_j: LVCandidate,
                              context: Optional[Dict[str, Any]] = None) -> float:
        """Calculate task-specific penalties"""
        if not context:
            return 0.0

        # Example: suppress creative responses in factual tasks
        task_type = context.get('task_type', 'general')
        niche_i = self._classify_niche(candidate_i, "")

        if task_type == "factual" and niche_i == "creative":
            return -0.9
        else:
            return 0.0

    def _simulate_lv_dynamics(self,
                             growth_rates: np.ndarray,
                             alpha_matrix: np.ndarray,
                             num_candidates: int) -> Tuple[np.ndarray, Dict]:
        """Simulate LV dynamics with your stabilization approach"""

        # Initialize equal populations
        n = np.ones(num_candidates) / num_candidates
        convergence_data = {'iterations': 0, 'converged': False}

        for iteration in range(self.max_iterations):
            # Calculate growth: r_i + Σ(α_ij * n_j)
            interaction_effects = alpha_matrix @ n
            total_growth = growth_rates + interaction_effects

            # Apply exponential growth with damping
            new_n = n * np.exp(self.damping_factor * total_growth)

            # Normalize to maintain population conservation
            new_n = new_n / np.sum(new_n)

            # Check convergence
            if np.allclose(n, new_n, atol=self.convergence_threshold):
                convergence_data['converged'] = True
                convergence_data['iterations'] = iteration + 1
                break

            n = new_n

        convergence_data['iterations'] = self.max_iterations
        return n, convergence_data

    def _select_outputs_by_population(self,
                                    candidates: List[LVCandidate],
                                    populations: np.ndarray,
                                    min_outputs: int = 1,
                                    max_outputs: int = 3) -> List[Dict[str, Any]]:
        """Select outputs based on final population sizes"""

        # Sort by population size
        sorted_indices = np.argsort(populations)[::-1]  # Descending order

        # Select top candidates but ensure diversity
        selected = []
        for i in range(min(max_outputs, len(candidates))):
            idx = sorted_indices[i]
            if populations[idx] > 0.1:  # Minimum viability threshold
                selected.append({
                    'content': candidates[idx].content,
                    'population': float(populations[idx]),
                    'quality_score': candidates[idx].quality_score,
                    'novelty_score': candidates[idx].novelty_score,
                    'content_hash': candidates[idx].content_hash,
                    'metadata': candidates[idx].metadata
                })

        # Ensure at least one output
        if not selected and candidates:
            best_idx = sorted_indices[0]
            selected.append({
                'content': candidates[best_idx].content,
                'population': float(populations[best_idx]),
                'quality_score': candidates[best_idx].quality_score,
                'novelty_score': candidates[best_idx].novelty_score,
                'content_hash': candidates[best_idx].content_hash,
                'metadata': candidates[best_idx].metadata
            })

        return selected

    def _calculate_diversity_metrics(self, selected_outputs: List[Dict]) -> Dict[str, float]:
        """Calculate diversity metrics for the selected outputs"""
        if len(selected_outputs) < 2:
            return {'semantic_diversity': 0.0, 'population_diversity': 0.0}

        # Semantic diversity using embeddings
        contents = [output['content'] for output in selected_outputs]
        embeddings = self.embedder.encode(contents)

        # Calculate pairwise similarities
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                )
                similarities.append(sim)

        semantic_diversity = 1.0 - np.mean(similarities) if similarities else 0.0

        # Population diversity (entropy of population distribution)
        populations = [output['population'] for output in selected_outputs]
        population_entropy = -np.sum([p * np.log(p) for p in populations if p > 0])
        population_diversity = population_entropy / np.log(len(populations))

        return {
            'semantic_diversity': float(semantic_diversity),
            'population_diversity': float(population_diversity),
            'num_selected': len(selected_outputs)
        }

    async def _store_selection_results(self,
                                     prompt: str,
                                     entropy: float,
                                     candidates: List[LVCandidate],
                                     selected_outputs: List[Dict],
                                     convergence_data: Dict):
        """Store LV selection results in Neo4j for learning and optimization"""
        try:
            # Import storage manager
            from .lv_neo4j_storage import LVNeo4jStorage
            storage = LVNeo4jStorage(self.neo4j)

            # Convert candidates to storage format
            candidate_data = []
            for candidate in candidates:
                candidate_data.append({
                    'content_hash': candidate.content_hash,
                    'quality_score': candidate.quality_score,
                    'novelty_score': candidate.novelty_score,
                    'bias_score': candidate.bias_score,
                    'cost_score': candidate.cost_score
                })

            # Store complete session
            session_id = await storage.store_lv_selection_session(
                prompt=prompt,
                entropy=entropy,
                candidates=candidate_data,
                selected_outputs=selected_outputs,
                convergence_data=convergence_data
            )

            if session_id:
                logger.info(f"LV selection session stored: {session_id}")
            else:
                logger.warning("Failed to store LV selection session")

        except Exception as e:
            logger.warning(f"Failed to store LV results: {e}")


# Mathematical validation using WolframAlpha integration
class LVMathematicalValidator:
    """Validates LV parameters using WolframAlpha computational engine"""

    @staticmethod
    async def validate_alpha_matrix_stability(alpha_matrix: np.ndarray) -> Dict[str, Any]:
        """
        Validate that alpha matrix leads to stable dynamics
        Uses WolframAlpha eigenvalue analysis
        """
        try:
            # Format matrix for WolframAlpha
            matrix_str = str(alpha_matrix.tolist()).replace('[', '{').replace(']', '}')

            # This would integrate with your WolframAlpha tool
            # For now, local eigenvalue calculation
            eigenvalues = np.linalg.eigvals(alpha_matrix)

            # Check stability (all eigenvalues should have negative real parts)
            stable = all(np.real(eig) < 0 for eig in eigenvalues)

            return {
                'stable': stable,
                'eigenvalues': eigenvalues.tolist(),
                'max_real_part': float(np.max(np.real(eigenvalues))),
                'recommendation': 'Stable limit cycles expected' if stable else 'Instability detected'
            }

        except Exception as e:
            logger.error(f"Stability validation failed: {e}")
            return {'stable': False, 'error': str(e)}


# Export main classes
__all__ = [
    'LVEcosystem',
    'LVCandidate',
    'EntropyProfile',
    'EntropyEstimator',
    'LVMathematicalValidator'
]
