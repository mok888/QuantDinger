"""
Analysis API routes (local-only).
Implements multi-dimensional analysis plus lightweight task/history APIs for the frontend.
"""
from flask import Blueprint, request, jsonify, Response, g
import json
import traceback
import time

from app.services.analysis import AnalysisService, reflect_analysis
from app.utils.logger import get_logger
from app.utils.db import get_db_connection
from app.utils.language import detect_request_language
from app.utils.auth import login_required

logger = get_logger(__name__)

analysis_bp = Blueprint('analysis', __name__)

def _now_ts() -> int:
    return int(time.time())

def _normalize_symbol(symbol: str) -> str:
    return (symbol or '').strip().upper()

def _store_task(user_id: int, market: str, symbol: str, model: str, language: str, status: str, result: dict = None, error_message: str = "") -> int:
    """Create a new task record. For pending tasks, completed_at is NULL."""
    result_json = json.dumps(result or {}, ensure_ascii=False)
    with get_db_connection() as db:
        cur = db.cursor()
        if status in ['completed', 'failed']:
            cur.execute(
                """
                INSERT INTO qd_analysis_tasks (user_id, market, symbol, model, language, status, result_json, error_message, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
                """,
                (user_id, market, symbol, model or '', language or 'en-US', status, result_json, error_message or '')
            )
        else:
            cur.execute(
                """
                INSERT INTO qd_analysis_tasks (user_id, market, symbol, model, language, status, result_json, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW())
                """,
                (user_id, market, symbol, model or '', language or 'en-US', status, result_json, error_message or '')
            )
        task_id = cur.lastrowid
        db.commit()
        cur.close()
    return int(task_id)


def _update_task(task_id: int, status: str, result: dict = None, error_message: str = "") -> bool:
    """Update an existing task with result and status."""
    try:
        result_json = json.dumps(result or {}, ensure_ascii=False)
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute(
                """
                UPDATE qd_analysis_tasks 
                SET status = ?, result_json = ?, error_message = ?, completed_at = NOW()
                WHERE id = ?
                """,
                (status, result_json, error_message or '', task_id)
            )
            db.commit()
            cur.close()
        return True
    except Exception as e:
        logger.error(f"_update_task failed: {e}")
        return False

def _get_task(task_id: int, user_id: int) -> dict:
    with get_db_connection() as db:
        cur = db.cursor()
        cur.execute("SELECT * FROM qd_analysis_tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        row = cur.fetchone()
        cur.close()
    return row or None

def _parse_result_json(row: dict) -> dict:
    if not row:
        return {}
    raw = row.get('result_json') or ''
    try:
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


@analysis_bp.route('/multi', methods=['POST'])
@analysis_bp.route('/multiAnalysis', methods=['POST'])  # compatibility with legacy naming
@login_required
def multi_analysis():
    """
    Multi-dimensional analysis for the current user.

    Request body:
        market: Market (AShare, USStock, HShare, Crypto, Forex, Futures)
        symbol: Symbol
        language: Optional; if omitted we will detect from request headers (X-App-Lang / Accept-Language)
    """
    task_id = None
    user_id = None
    market = ''
    symbol = ''
    model = None
    language = 'en-US'
    
    try:
        user_id = g.user_id
        data = request.get_json()
        if not data:
            return jsonify({
                'code': 0,
                'msg': 'Request body is required',
                'data': None
            }), 400
        
        market = data.get('market', '')
        symbol = data.get('symbol', '')
        language = detect_request_language(request, body=data, default='en-US')
        model = data.get('model', None)
        use_multi_agent = data.get('use_multi_agent', None)  # None -> use backend default
        timeframe = data.get('timeframe', '1D')
        
        if not symbol or not market:
            return jsonify({
                'code': 0,
                'msg': 'Missing required parameters',
                'data': None
            }), 400
        
        # Normalize/defend input for local-only mode.
        market = str(market).strip()
        symbol = _normalize_symbol(symbol)
        language = str(language or 'en-US')
        model = str(model) if model else None

        logger.info(f"Analyze request: {market}:{symbol}, use_multi_agent={use_multi_agent}, model={model}")
        
        # Step 0: Check billing (计费检查)
        from app.services.billing_service import get_billing_service
        billing_success, billing_msg = get_billing_service().check_and_consume(
            user_id=user_id,
            feature='ai_analysis',
            reference_id=f'{market}:{symbol}'
        )
        if not billing_success:
            if 'insufficient_credits' in billing_msg:
                parts = billing_msg.split(':')
                current = parts[1] if len(parts) > 1 else '0'
                required = parts[2] if len(parts) > 2 else '?'
                return jsonify({
                    'code': 0,
                    'msg': f'Insufficient credits. Current: {current}, Required: {required}',
                    'data': {'error_type': 'insufficient_credits', 'current': current, 'required': required}
                }), 402
            return jsonify({'code': 0, 'msg': billing_msg, 'data': None}), 400
        
        # Step 1: Create a "pending" task record first (so user can see progress in history)
        task_id = _store_task(user_id, market, symbol, model or '', language, 'pending', result={}, error_message='')
        
        # Step 2: Run analysis in background thread (so user can navigate away)
        import threading
        
        def run_analysis_background(task_id_inner, market_inner, symbol_inner, language_inner, model_inner, timeframe_inner, use_multi_agent_inner):
            """Execute analysis in background and update task when done."""
            try:
                service = AnalysisService(use_multi_agent=use_multi_agent_inner)
                result = service.analyze(market_inner, symbol_inner, language_inner, model=model_inner, timeframe=timeframe_inner)
                _update_task(task_id_inner, 'completed', result=result, error_message='')
                logger.info(f"Background analysis completed for task {task_id_inner}")
            except Exception as e:
                logger.error(f"Background analysis failed for task {task_id_inner}: {e}")
                _update_task(task_id_inner, 'failed', result={}, error_message=str(e))
        
        analysis_thread = threading.Thread(
            target=run_analysis_background,
            args=(task_id, market, symbol, language, model, timeframe, use_multi_agent),
            daemon=False  # Keep running even if main request thread ends
        )
        analysis_thread.start()

        # Step 3: Return immediately with task_id (frontend will poll for results)
        return jsonify({'code': 1, 'msg': 'success', 'data': {'task_id': task_id, 'status': 'pending'}})
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update existing task as "failed", or create a new failed record if task_id doesn't exist
        try:
            if task_id:
                _update_task(task_id, 'failed', result={}, error_message=str(e))
            elif user_id:
                _store_task(user_id, market, symbol, model or '', language, 'failed', result={}, error_message=str(e))
        except Exception:
            pass
            
        return jsonify({
            'code': 0,
            'msg': f'Analysis failed: {str(e)}',
            'data': {'task_id': task_id} if task_id else None
        }), 500


@analysis_bp.route('/getTaskStatus', methods=['GET'])
@login_required
def get_task_status():
    """Frontend compatibility: return task status + result by task_id for the current user."""
    try:
        user_id = g.user_id
        task_id = int(request.args.get('task_id') or 0)
        if not task_id:
            return jsonify({'code': 0, 'msg': 'Missing task_id', 'data': None}), 400

        row = _get_task(task_id, user_id)
        if not row:
            return jsonify({'code': 0, 'msg': 'Task not found', 'data': None}), 404

        payload = {
            'id': row.get('id'),
            'market': row.get('market'),
            'symbol': row.get('symbol'),
            'status': row.get('status'),
            'error_message': row.get('error_message') or '',
            'result': _parse_result_json(row)
        }
        return jsonify({'code': 1, 'msg': 'success', 'data': payload})
    except Exception as e:
        logger.error(f"get_task_status failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@analysis_bp.route('/getHistoryList', methods=['GET'])
@login_required
def get_history_list():
    """Frontend compatibility: paginated analysis history for the current user."""
    try:
        user_id = g.user_id
        page = int(request.args.get('page') or 1)
        pagesize = int(request.args.get('pagesize') or 20)
        page = max(page, 1)
        pagesize = min(max(pagesize, 1), 100)
        offset = (page - 1) * pagesize

        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute("SELECT COUNT(1) as cnt FROM qd_analysis_tasks WHERE user_id = ?", (user_id,))
            total = int((cur.fetchone() or {}).get('cnt') or 0)
            cur.execute(
                """
                SELECT id, market, symbol, model, status, error_message, created_at, completed_at, result_json
                FROM qd_analysis_tasks
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, pagesize, offset)
            )
            rows = cur.fetchall() or []
            cur.close()

        out = []
        for r in rows:
            has_result = bool((r.get('result_json') or '').strip())
            # Convert datetime to Unix timestamp for frontend compatibility
            created_at = r.get('created_at')
            completed_at = r.get('completed_at')
            createtime = int(created_at.timestamp()) if created_at else 0
            completetime = int(completed_at.timestamp()) if completed_at else None
            out.append({
                'id': r.get('id'),
                'market': r.get('market'),
                'symbol': r.get('symbol'),
                'model': r.get('model') or '',
                'status': r.get('status'),
                'has_result': has_result,
                'error_message': r.get('error_message') or '',
                'createtime': createtime,
                'completetime': completetime
            })

        return jsonify({'code': 1, 'msg': 'success', 'data': {'list': out, 'total': total}})
    except Exception as e:
        logger.error(f"get_history_list failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': {'list': [], 'total': 0}}), 500


@analysis_bp.route('/deleteTask', methods=['POST'])
@login_required
def delete_task():
    """Delete an analysis task by task_id for the current user."""
    try:
        user_id = g.user_id
        data = request.get_json() or {}
        task_id = int(data.get('task_id') or 0)
        
        if not task_id:
            return jsonify({'code': 0, 'msg': 'Missing task_id', 'data': None}), 400
        
        # Verify task belongs to user
        row = _get_task(task_id, user_id)
        if not row:
            return jsonify({'code': 0, 'msg': 'Task not found', 'data': None}), 404
        
        # Delete the task
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute("DELETE FROM qd_analysis_tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
            db.commit()
            cur.close()
        
        return jsonify({'code': 1, 'msg': 'success', 'data': {'deleted_id': task_id}})
    except Exception as e:
        logger.error(f"delete_task failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@analysis_bp.route('/createTask', methods=['POST'])
@login_required
def create_task():
    """
    Compatibility endpoint for legacy frontend.
    In local-only mode we do not run a separate async worker; we create a completed task record immediately.
    """
    try:
        user_id = g.user_id
        data = request.get_json() or {}
        market = str((data.get('market') or '')).strip()
        symbol = _normalize_symbol(data.get('symbol'))
        language = detect_request_language(request, body=data, default='en-US')
        model = data.get('model') or ''

        if not market or not symbol:
            return jsonify({'code': 0, 'msg': 'Missing market or symbol', 'data': None}), 400

        # Create a placeholder "pending" task so frontend can show task_id if it needs it.
        task_id = _store_task(user_id, market, symbol, str(model), language, 'pending', result={}, error_message='')
        return jsonify({'code': 1, 'msg': 'success', 'data': {'task_id': task_id, 'status': 'pending'}})
    except Exception as e:
        logger.error(f"create_task failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@analysis_bp.route('/reflect', methods=['POST'])
@login_required
def reflect():
    """
    Reflection API.
    Learn from post-trade outcomes and update agent memory (local-only).

    Body:
        market: Market
        symbol: Symbol
        decision: BUY/SELL/HOLD
        returns: Optional return percentage
        result: Optional free-text outcome
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'code': 0,
                'msg': 'Request body is required',
                'data': None
            }), 400
        
        market = data.get('market', '')
        symbol = data.get('symbol', '')
        decision = data.get('decision', '')
        returns = data.get('returns', None)
        result = data.get('result', None)
        
        if not symbol or not market or not decision:
            return jsonify({
                'code': 0,
                'msg': 'Missing required parameters (market, symbol, decision)',
                'data': None
            }), 400
        
        logger.info(f"Reflection: {market}:{symbol}, decision={decision}, returns={returns}")
        
        reflect_analysis(market, symbol, decision, returns, result)
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': None
        })
        
    except Exception as e:
        logger.error(f"Reflection failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'code': 0,
            'msg': f'Reflection failed: {str(e)}',
            'data': None
        }), 500

