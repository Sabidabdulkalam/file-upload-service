"""
Temporary smoke test for logger.py
"""

from src.app.logger import get_logger   # absolute import

log = get_logger(__name__)

def main() -> None:
    log.info("Logger is alive.")
    log.error("This is a test error message.")

if __name__ == "__main__":
    main()