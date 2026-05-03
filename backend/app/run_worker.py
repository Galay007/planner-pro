from .workers.schedule_worker import main
import logging

logging.basicConfig(
    level=logging.WARNING, # (DEBUG, INFO, WARNING, ERROR)
    format="%(asctime)s | %(levelname)s | %(threadName)s | %(message)s",
)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass 
    finally:
        import sys
        sys.exit(0) 
