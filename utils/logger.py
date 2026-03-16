"""
Logging configuration.

Sets up a RotatingFileHandler writing to logs/app.log (max 5 MB, 3 backups)
and a StreamHandler for console output.

Log level: DEBUG in development (LOG_LEVEL=DEBUG env var), WARNING in production.

Usage:
  from utils.logger import get_logger
  logger = get_logger(__name__)
  logger.info("Fetching 50 symbols")
  logger.warning("Missing P/E for SMALLCAP.NS")
  logger.error("HTTP 429 from Yahoo Finance — backing off")
"""
