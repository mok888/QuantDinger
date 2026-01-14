"""
Agent memory system (PostgreSQL).

This module stores agent experiences in PostgreSQL and retrieves relevant past cases
to inject into prompts (RAG-style). It does NOT finetune model weights.

Retrieval (configurable):
- Vector similarity via deterministic local embeddings (default)
- Fallback to difflib text similarity when embeddings are missing

Ranking combines:
- similarity
- recency decay (half-life)
- optional returns weight
"""

import json
import os
import math
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import difflib

from app.utils.logger import get_logger
from app.utils.db import get_db_connection
from .embedding import EmbeddingService, cosine_sim

logger = get_logger(__name__)


class AgentMemory:
    """Agent memory system using PostgreSQL"""
    
    def __init__(self, agent_name: str, db_path: Optional[str] = None):
        """
        Initialize memory system.
        
        Args:
            agent_name: Agent identifier (e.g., 'trader_agent', 'risk_analyst')
            db_path: Deprecated parameter, kept for backward compatibility
        """
        self.agent_name = agent_name
        self.embedder = EmbeddingService()
        self.enable_vector = os.getenv("AGENT_MEMORY_ENABLE_VECTOR", "true").lower() == "true"
        self.candidate_limit = int(os.getenv("AGENT_MEMORY_CANDIDATE_LIMIT", "500") or 500)
        self.half_life_days = float(os.getenv("AGENT_MEMORY_HALF_LIFE_DAYS", "30") or 30)
        self.w_sim = float(os.getenv("AGENT_MEMORY_W_SIM", "0.75") or 0.75)
        self.w_recency = float(os.getenv("AGENT_MEMORY_W_RECENCY", "0.20") or 0.20)
        self.w_returns = float(os.getenv("AGENT_MEMORY_W_RETURNS", "0.05") or 0.05)

    def _now_utc(self) -> datetime:
        return datetime.now(timezone.utc)

    def _parse_ts(self, ts_val: Any) -> Optional[datetime]:
        if ts_val is None:
            return None
        if isinstance(ts_val, datetime):
            return ts_val
        s = str(ts_val)
        try:
            return datetime.fromisoformat(s.replace("Z", ""))
        except Exception:
            return None

    def _recency_score(self, created_at: Any) -> float:
        dt = self._parse_ts(created_at)
        if not dt:
            return 0.0
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_days = max(0.0, (self._now_utc() - dt).total_seconds() / 86400.0)
        hl = max(0.1, float(self.half_life_days or 30.0))
        return float(math.exp(-math.log(2.0) * (age_days / hl)))

    def _returns_score(self, returns: Any) -> float:
        try:
            r = float(returns)
        except Exception:
            return 0.0
        return float(math.tanh(r / 10.0))

    def _build_embed_text(self, situation: str, recommendation: str, result: Optional[str], features_json: Optional[str]) -> str:
        return "\n".join([
            f"situation: {situation or ''}",
            f"recommendation: {recommendation or ''}",
            f"result: {result or ''}",
            f"features: {features_json or ''}",
        ])

    def add_memory(
        self,
        situation: str,
        recommendation: str,
        result: Optional[str] = None,
        returns: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Add a memory entry.
        
        Args:
            situation: Situation description
            recommendation: Decision/recommendation made
            result: Outcome description (optional)
            returns: Return percentage (optional)
            metadata: Optional structured metadata (market/symbol/timeframe/features...)
        """
        try:
            meta = metadata or {}
            market = (meta.get("market") or "").strip() or None
            symbol = (meta.get("symbol") or "").strip() or None
            timeframe = (meta.get("timeframe") or "").strip() or None
            features = meta.get("features") if isinstance(meta, dict) else None
            try:
                features_json = json.dumps(features, ensure_ascii=False) if features is not None else None
            except Exception:
                features_json = None

            embedding_blob = None
            if self.enable_vector:
                text = self._build_embed_text(situation, recommendation, result, features_json)
                vec = self.embedder.embed(text)
                embedding_blob = self.embedder.to_bytes(vec)

            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO qd_agent_memories 
                    (agent_name, situation, recommendation, result, returns, market, symbol, timeframe, features_json, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (self.agent_name, situation, recommendation, result, returns, market, symbol, timeframe, features_json, embedding_blob)
                )
                conn.commit()
                cur.close()
            logger.info(f"{self.agent_name} added new memory")
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
    
    def get_memories(self, current_situation: str, n_matches: int = 5, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve similar memories.
        
        Args:
            current_situation: Current situation description
            n_matches: Number of matches to return
            metadata: Optional metadata for filtering/weighting
            
        Returns:
            List of matching memory entries
        """
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT id, situation, recommendation, result, returns, created_at, 
                           market, symbol, timeframe, features_json, embedding
                    FROM qd_agent_memories
                    WHERE agent_name = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (self.agent_name, int(self.candidate_limit))
                )
                all_memories = cur.fetchall() or []
                cur.close()
            
            if not all_memories:
                return []
            
            meta = metadata or {}
            tf = (meta.get("timeframe") or "").strip()
            features = meta.get("features") if isinstance(meta, dict) else None
            try:
                q_features_json = json.dumps(features, ensure_ascii=False) if features is not None else None
            except Exception:
                q_features_json = None

            query_vec = []
            if self.enable_vector:
                query_text = self._build_embed_text(current_situation, "", "", q_features_json)
                query_vec = self.embedder.embed(query_text)

            ranked = []
            for row in all_memories:
                mem_id = row['id']
                situation = row['situation']
                recommendation = row['recommendation']
                result = row['result']
                returns = row['returns']
                created_at = row['created_at']
                market = row['market']
                symbol = row['symbol']
                timeframe = row['timeframe']
                features_json = row['features_json']
                embedding_blob = row['embedding']

                sim = 0.0
                if self.enable_vector and embedding_blob:
                    try:
                        # Handle memoryview/bytes from PostgreSQL
                        if isinstance(embedding_blob, memoryview):
                            embedding_blob = bytes(embedding_blob)
                        mem_vec = self.embedder.from_bytes(embedding_blob)
                        sim = cosine_sim(query_vec, mem_vec)
                    except Exception:
                        sim = 0.0
                else:
                    sim = difflib.SequenceMatcher(None, (current_situation or "").lower(), (situation or "").lower()).ratio()

                rec = self._recency_score(created_at)
                ret = self._returns_score(returns)

                score = (self.w_sim * sim) + (self.w_recency * rec) + (self.w_returns * ret)

                if tf and timeframe and str(timeframe).strip() != tf:
                    score -= 0.15

                ranked.append({
                    'id': mem_id,
                    'matched_situation': situation,
                    'recommendation': recommendation,
                    'result': result,
                    'returns': returns,
                    'created_at': created_at,
                    'market': market,
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'features_json': features_json,
                    'score': float(score),
                    'sim': float(sim),
                    'recency': float(rec),
                })

            ranked.sort(key=lambda x: x.get('score', 0.0), reverse=True)
            return ranked[: max(0, int(n_matches or 0))]
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    def update_memory_result(self, memory_id: int, result: str, returns: Optional[float] = None):
        """
        Update memory result.
        
        Args:
            memory_id: Memory ID
            result: Outcome description
            returns: Return percentage
        """
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE qd_agent_memories
                    SET result = ?, returns = ?, updated_at = NOW()
                    WHERE id = ? AND agent_name = ?
                    """,
                    (result, returns, memory_id, self.agent_name)
                )
                conn.commit()
                cur.close()
            logger.info(f"{self.agent_name} updated memory {memory_id}")
        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics for this agent."""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                cur.execute(
                    'SELECT COUNT(*) as cnt FROM qd_agent_memories WHERE agent_name = ?',
                    (self.agent_name,)
                )
                total = cur.fetchone()['cnt']
                
                cur.execute(
                    'SELECT AVG(returns) as avg_ret FROM qd_agent_memories WHERE agent_name = ? AND returns IS NOT NULL',
                    (self.agent_name,)
                )
                avg_returns = cur.fetchone()['avg_ret'] or 0
                
                cur.execute(
                    'SELECT COUNT(*) as cnt FROM qd_agent_memories WHERE agent_name = ? AND returns > 0',
                    (self.agent_name,)
                )
                positive = cur.fetchone()['cnt']
                
                cur.close()
            
            return {
                'total_memories': total,
                'average_returns': round(avg_returns, 2),
                'positive_decisions': positive,
                'success_rate': round(positive / total * 100, 2) if total > 0 else 0
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def clear_memories(self):
        """Clear all memories for this agent (use with caution)."""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    'DELETE FROM qd_agent_memories WHERE agent_name = ?',
                    (self.agent_name,)
                )
                conn.commit()
                cur.close()
            logger.warning(f"{self.agent_name} cleared all memories")
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
