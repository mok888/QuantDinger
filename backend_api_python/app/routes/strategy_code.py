"""
Indicator-analysis Strategy APIs (local-first).

These "strategies" are user-authored Python scripts used on `/indicator-analysis`:
- visualize signals on Kline (via output.plots/output.signals)
- optionally support backtest engine expectations (df signal columns)

They are different from the live trading executor strategies in `app/routes/strategy.py`.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict

import requests
from flask import Blueprint, Response, jsonify, request

from app.utils.db import get_db_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)

strategy_code_bp = Blueprint("strategy_code", __name__)


def _now_ts() -> int:
    return int(time.time())


def _extract_meta_from_code(code: str) -> Dict[str, str]:
    if not code or not isinstance(code, str):
        return {"name": "", "description": ""}
    name_match = re.search(r'^\s*my_indicator_name\s*=\s*([\'"])(.*?)\1\s*$', code, re.MULTILINE)
    desc_match = re.search(r'^\s*my_indicator_description\s*=\s*([\'"])(.*?)\1\s*$', code, re.MULTILINE)
    name = (name_match.group(2).strip() if name_match else "")[:100]
    description = (desc_match.group(2).strip() if desc_match else "")[:500]
    return {"name": name, "description": description}


@strategy_code_bp.route("/strategy/getStrategies", methods=["GET"])
def get_strategies():
    try:
        user_id = int(request.args.get("userid") or 1)
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute(
                "SELECT id, user_id, name, code, description, createtime, updatetime FROM qd_strategy_codes WHERE user_id = ? ORDER BY id DESC",
                (user_id,),
            )
            rows = cur.fetchall() or []
            cur.close()
        return jsonify({"code": 1, "msg": "success", "data": rows})
    except Exception as e:
        logger.error(f"get_strategies failed: {e}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e), "data": []}), 500


@strategy_code_bp.route("/strategy/saveStrategy", methods=["POST"])
def save_strategy():
    try:
        data = request.get_json() or {}
        user_id = int(data.get("userid") or 1)
        strategy_id = int(data.get("id") or 0)
        code = data.get("code") or ""
        if not str(code).strip():
            return jsonify({"code": 0, "msg": "code is required", "data": None}), 400

        name = (data.get("name") or "").strip()
        description = (data.get("description") or "").strip()
        if not name or not description:
            meta = _extract_meta_from_code(code)
            if not name:
                name = meta.get("name") or ""
            if not description:
                description = meta.get("description") or ""
        if not name:
            name = "Custom Strategy"

        now = _now_ts()
        with get_db_connection() as db:
            cur = db.cursor()
            if strategy_id and strategy_id > 0:
                cur.execute(
                    "UPDATE qd_strategy_codes SET name = ?, code = ?, description = ?, updatetime = ? WHERE id = ? AND user_id = ?",
                    (name, code, description, now, strategy_id, user_id),
                )
            else:
                cur.execute(
                    "INSERT INTO qd_strategy_codes (user_id, name, code, description, createtime, updatetime) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, name, code, description, now, now),
                )
                strategy_id = int(cur.lastrowid or 0)
            db.commit()
            cur.close()

        return jsonify({"code": 1, "msg": "success", "data": {"id": strategy_id, "userid": user_id}})
    except Exception as e:
        logger.error(f"save_strategy failed: {e}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e), "data": None}), 500


@strategy_code_bp.route("/strategy/deleteStrategy", methods=["POST"])
def delete_strategy():
    try:
        data = request.get_json() or {}
        user_id = int(data.get("userid") or 1)
        strategy_id = int(data.get("id") or 0)
        if not strategy_id:
            return jsonify({"code": 0, "msg": "id is required", "data": None}), 400
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute("DELETE FROM qd_strategy_codes WHERE id = ? AND user_id = ?", (strategy_id, user_id))
            db.commit()
            cur.close()
        return jsonify({"code": 1, "msg": "success", "data": None})
    except Exception as e:
        logger.error(f"delete_strategy failed: {e}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e), "data": None}), 500


@strategy_code_bp.route("/strategy/aiGenerate", methods=["POST"])
def ai_generate_strategy():
    """
    SSE code generation for strategy scripts (local-first, no QDT deduction).
    """
    data = request.get_json() or {}
    prompt = (data.get("prompt") or "").strip()
    existing = (data.get("existingCode") or "").strip()

    if not prompt:
        def _err_stream():
            yield "data: " + json.dumps({"error": "提示词不能为空"}, ensure_ascii=False) + "\n\n"
            yield "data: [DONE]\n\n"

        return Response(_err_stream(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    SYSTEM_PROMPT = """# Role

You are an expert Python quantitative trading developer.

# Environment
- Runs in browser (Pyodide): NO network access, no pip, no requests.
- pandas is already imported as pd, numpy as np. DO NOT import them.
- Input: df with columns time/open/high/low/close/volume.

# Required output (STRICT)
- You MUST define:
  - my_indicator_name = "..."
  - my_indicator_description = "..."
  - output = {"name":..., "plots":[...], "signals":[...]}

# Chart signal rules (MUST)
- output["signals"] MAY exist, but if present it MUST contain ONLY two types: "buy" and "sell".
- Signals must be aligned with df length: signals[].data length == len(df), use None for "no signal".
- Default signal text MUST be English (recommended "B"/"S" or "Buy"/"Sell"). Do NOT output Chinese text.

# Execution/backtest compatibility (MUST)
- You MUST set boolean columns:
  - df["buy"] and df["sell"]
- Backend will normalize buy/sell into open/close long/short actions based on trade_direction and current position.
- Do NOT emit open_long/close_long/open_short/close_short/add_* in output["signals"].
- Do NOT implement position sizing, TP/SL, trailing, pyramiding in the script. Those belong to strategy_config / backend.
- Signals are typically confirmed on bar close and executed by backtest on the next bar open (to avoid look-ahead bias).

# Robustness requirements (IMPORTANT)
- Always handle division-by-zero and NaN/inf when computing indicators (e.g., RSV denominator can be 0).
- Avoid overly restrictive entry conditions that result in zero buys or zero sells. Prefer crossover/event-based signals.
- For multi-indicator strategies, avoid requiring a crossover AND extreme RSI/BB condition on the same bar unless explicitly requested.
- Prefer edge-triggered signals (one-shot) to avoid repeated consecutive buy/sell bars:
  buy = raw_buy & ~raw_buy.shift(1).fillna(False)
  sell = raw_sell & ~raw_sell.shift(1).fillna(False)

# Execution rule (IMPORTANT)
- The backtest engine may apply parameterized scaling (scale-in/out) from strategy_config.
- If a candle has a main signal (buy/sell mapped to open/close/reverse), scaling in/out is skipped on the same candle.

# Output style
- Output Python code only. No markdown code blocks. No extra explanations.
- Keep code comments and default strings in English.
"""

    def _openrouter_base_and_key() -> tuple[str, str]:
        key = os.getenv("OPENROUTER_API_KEY", "").strip()
        base = os.getenv("OPENROUTER_BASE_URL", "").strip()
        if not base:
            api_url = os.getenv("OPENROUTER_API_URL", "").strip()
            if api_url.endswith("/chat/completions"):
                base = api_url[: -len("/chat/completions")]
        if not base:
            base = "https://openrouter.ai/api/v1"
        return base, key

    def _template_code() -> str:
        return (
            f'my_indicator_name = "Custom Strategy"\n'
            f'my_indicator_description = "{prompt.replace("\\n", " ")[:200]}"\n\n'
            "# Buy/Sell only. Execution is normalized in backend.\n"
            "df = df.copy()\n"
            "sma = df['close'].rolling(14).mean()\n"
            "raw_buy = (df['close'] > sma) & (df['close'].shift(1) <= sma.shift(1))\n"
            "raw_sell = (df['close'] < sma) & (df['close'].shift(1) >= sma.shift(1))\n"
            "# Edge-triggered signals (avoid repeated consecutive signals)\n"
            "buy = raw_buy.fillna(False) & (~raw_buy.shift(1).fillna(False))\n"
            "sell = raw_sell.fillna(False) & (~raw_sell.shift(1).fillna(False))\n"
            "df['buy'] = buy.astype(bool)\n"
            "df['sell'] = sell.astype(bool)\n"
            "\n"
            "buy_marks = [df['low'].iloc[i]*0.995 if bool(df['buy'].iloc[i]) else None for i in range(len(df))]\n"
            "sell_marks = [df['high'].iloc[i]*1.005 if bool(df['sell'].iloc[i]) else None for i in range(len(df))]\n"
            "output = {\n"
            "  'name': my_indicator_name,\n"
            "  'plots': [ {'name':'SMA 14','data': sma.tolist(),'color':'#1890ff','overlay': True} ],\n"
            "  'signals': [\n"
            "    {'type':'buy','text':'B','data': buy_marks,'color':'#00E676'},\n"
            "    {'type':'sell','text':'S','data': sell_marks,'color':'#FF5252'}\n"
            "  ]\n"
            "}\n"
        )

    def _generate() -> str:
        base_url, api_key = _openrouter_base_and_key()
        if not api_key:
            return _template_code()

        model = (os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini") or "").strip() or "openai/gpt-4o-mini"
        temperature = float(os.getenv("OPENROUTER_TEMPERATURE", "0.7") or 0.7)

        user_prompt = prompt
        if existing:
            user_prompt = (
                "# Existing Code (modify based on this):\n\n```python\n"
                + existing.strip()
                + "\n```\n\n# Modification Requirements:\n\n"
                + prompt
                + "\n\nPlease generate complete new Python code based on the existing code above and my modification requirements. Output the complete Python code directly, without explanations, without segmentation."
            )

        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": temperature,
                "stream": False,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=120,
        )
        resp.raise_for_status()
        j = resp.json()
        content = (((j.get("choices") or [{}])[0]).get("message") or {}).get("content") or ""
        return content.strip() or _template_code()

    def stream():
        try:
            code_text = _generate()
        except Exception as e:
            logger.warning(f"strategy aiGenerate failed, fallback template: {e}")
            code_text = _template_code()

        chunk_size = 200
        for i in range(0, len(code_text), chunk_size):
            yield "data: " + json.dumps({"content": code_text[i : i + chunk_size]}, ensure_ascii=False) + "\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


