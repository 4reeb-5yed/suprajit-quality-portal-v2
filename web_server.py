import logging
from waitress import serve
from app import create_app
from app.config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('waitress')

if __name__ == '__main__':
    app = create_app()
    cfg = get_config()
    
    logger.info(f"Starting Waitress production server on {cfg.HOST}:{cfg.PORT}")
    serve(app, host=cfg.HOST, port=cfg.PORT, threads=8)
