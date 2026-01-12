"""
API 路由模块
"""
from flask import Flask


def register_routes(app: Flask):
    """注册所有 API 路由蓝图"""
    from app.routes.kline import kline_bp
    from app.routes.analysis import analysis_bp
    from app.routes.backtest import backtest_bp
    from app.routes.health import health_bp
    from app.routes.market import market_bp
    from app.routes.strategy import strategy_bp
    from app.routes.credentials import credentials_bp
    from app.routes.auth import auth_bp
    from app.routes.ai_chat import ai_chat_bp
    from app.routes.indicator import indicator_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.settings import settings_bp
    from app.routes.portfolio import portfolio_bp
    from app.routes.ibkr import ibkr_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/user')  # 兼容前端 /api/user/login
    app.register_blueprint(kline_bp, url_prefix='/api/indicator')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(backtest_bp, url_prefix='/api/indicator')
    app.register_blueprint(market_bp, url_prefix='/api/market')
    app.register_blueprint(ai_chat_bp, url_prefix='/api/ai')
    app.register_blueprint(indicator_bp, url_prefix='/api/indicator')
    app.register_blueprint(strategy_bp, url_prefix='/api')
    app.register_blueprint(credentials_bp, url_prefix='/api/credentials')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
    app.register_blueprint(ibkr_bp, url_prefix='/api/ibkr')

