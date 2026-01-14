"""
Auto-reflection and verification service (PostgreSQL).

Records analysis predictions and auto-verifies results in the future
to achieve closed-loop learning for AI agents.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.utils.logger import get_logger
from app.utils.db import get_db_connection
from .memory import AgentMemory
from .tools import AgentTools

logger = get_logger(__name__)


class ReflectionService:
    """Reflection service: manages storage and verification of analysis records."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize reflection service.
        
        Args:
            db_path: Deprecated parameter, kept for backward compatibility
        """
        self.tools = AgentTools()

    def record_analysis(
        self,
        market: str,
        symbol: str,
        price: float,
        decision: str,
        confidence: int,
        reasoning: str,
        check_days: int = 7
    ):
        """
        Record an analysis for future verification.
        
        Args:
            market: Market type
            symbol: Symbol code
            price: Current price
            decision: Decision (BUY/SELL/HOLD)
            confidence: Confidence level (0-100)
            reasoning: Reasoning text
            check_days: Days until verification (default 7)
        """
        try:
            target_date = datetime.now() + timedelta(days=check_days)
            
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO qd_reflection_records 
                    (market, symbol, initial_price, decision, confidence, reasoning, target_check_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (market, symbol, price, decision, confidence, reasoning, target_date)
                )
                conn.commit()
                cur.close()
            logger.info(f"Recorded analysis for reflection: {market}:{symbol}, will verify after {check_days} day(s)")
        except Exception as e:
            logger.error(f"Failed to record analysis: {e}")

    def run_verification_cycle(self):
        """
        Execute verification cycle: check due records, verify results, and write to memory.
        """
        logger.info("Starting auto-reflection verification cycle...")
        
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # 1. Find all due and pending records
                cur.execute(
                    """
                    SELECT id, market, symbol, initial_price, decision, confidence, reasoning, analysis_date 
                    FROM qd_reflection_records 
                    WHERE status = 'PENDING' AND target_check_date <= NOW()
                    """
                )
                records = cur.fetchall() or []
                
                if not records:
                    logger.info("No records to verify")
                    cur.close()
                    return
                
                logger.info(f"Found {len(records)} records to verify")
                
                # Initialize memory system for writing verification results
                trader_memory = AgentMemory('trader_agent')
                
                for record in records:
                    record_id = record['id']
                    market = record['market']
                    symbol = record['symbol']
                    initial_price = record['initial_price']
                    decision = record['decision']
                    confidence = record['confidence']
                    reasoning = record['reasoning']
                    analysis_date = record['analysis_date']
                    
                    try:
                        # 2. Get current price
                        current_price_data = self.tools.get_current_price(market, symbol)
                        current_price = current_price_data.get('price')
                        
                        if not current_price:
                            logger.warning(f"Cannot get current price for {market}:{symbol}, skipping")
                            continue
                        
                        # 3. Calculate return and result
                        if not initial_price or initial_price == 0:
                            actual_return = 0.0
                        else:
                            actual_return = (current_price - initial_price) / initial_price * 100
                        
                        # Evaluate result
                        result_desc = ""
                        is_good_prediction = False
                        
                        if decision == "BUY":
                            if actual_return > 2.0:
                                result_desc = "Correct: price rose after BUY"
                                is_good_prediction = True
                            elif actual_return < -2.0:
                                result_desc = "Wrong: price fell after BUY"
                            else:
                                result_desc = "Neutral: limited price movement"
                        elif decision == "SELL":
                            if actual_return < -2.0:
                                result_desc = "Correct: price fell after SELL"
                                is_good_prediction = True
                            elif actual_return > 2.0:
                                result_desc = "Wrong: price rose after SELL"
                            else:
                                result_desc = "Neutral: limited price movement"
                        else:  # HOLD
                            if -2.0 <= actual_return <= 2.0:
                                result_desc = "Correct: limited movement during HOLD"
                                is_good_prediction = True
                            else:
                                result_desc = f"Deviated: large movement during HOLD ({actual_return:.2f}%)"

                        # 4. Write to memory system (agent learning)
                        memory_situation = f"{market}:{symbol} auto-verified (analysis_date: {analysis_date})"
                        memory_recommendation = f"Decision: {decision} (confidence {confidence}), reasoning: {(reasoning or '')[:120]}"
                        memory_result = f"Verification: {result_desc}; return={actual_return:.2f}% (initial {initial_price} -> final {current_price})"
                        
                        trader_memory.add_memory(
                            memory_situation,
                            memory_recommendation,
                            memory_result,
                            actual_return,
                            metadata={
                                "market": market,
                                "symbol": symbol,
                                "timeframe": "1D",
                                "features": {
                                    "source": "auto_verify",
                                    "decision": decision,
                                    "confidence": confidence,
                                    "initial_price": initial_price,
                                    "final_price": current_price,
                                    "analysis_date": str(analysis_date),
                                    "result_desc": result_desc,
                                    "is_good_prediction": bool(is_good_prediction),
                                },
                            }
                        )
                        
                        # 5. Update record status
                        cur.execute(
                            """
                            UPDATE qd_reflection_records 
                            SET status = 'COMPLETED', final_price = ?, actual_return = ?, check_result = ?
                            WHERE id = ?
                            """,
                            (current_price, actual_return, result_desc, record_id)
                        )
                        conn.commit()
                        logger.info(f"Verification completed {market}:{symbol}: {result_desc}")
                        
                    except Exception as inner_e:
                        logger.error(f"Failed to process record {record_id}: {inner_e}")
                        # Optionally mark as failed to avoid repeated processing
                        # cur.execute("UPDATE qd_reflection_records SET status = 'FAILED' WHERE id = ?", (record_id,))
                        # conn.commit()
                
                cur.close()
            logger.info("Reflection verification cycle completed")
            
        except Exception as e:
            logger.error(f"Failed to execute verification cycle: {e}")

    def get_pending_count(self) -> int:
        """Get count of pending verification records."""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) as cnt FROM qd_reflection_records WHERE status = 'PENDING'")
                count = cur.fetchone()['cnt']
                cur.close()
                return count
        except Exception as e:
            logger.error(f"Failed to get pending count: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get reflection statistics."""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                cur.execute("SELECT COUNT(*) as cnt FROM qd_reflection_records")
                total = cur.fetchone()['cnt']
                
                cur.execute("SELECT COUNT(*) as cnt FROM qd_reflection_records WHERE status = 'PENDING'")
                pending = cur.fetchone()['cnt']
                
                cur.execute("SELECT COUNT(*) as cnt FROM qd_reflection_records WHERE status = 'COMPLETED'")
                completed = cur.fetchone()['cnt']
                
                cur.execute(
                    "SELECT AVG(actual_return) as avg_ret FROM qd_reflection_records WHERE status = 'COMPLETED' AND actual_return IS NOT NULL"
                )
                avg_return = cur.fetchone()['avg_ret'] or 0
                
                cur.close()
                
            return {
                'total_records': total,
                'pending_records': pending,
                'completed_records': completed,
                'average_return': round(avg_return, 2)
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
