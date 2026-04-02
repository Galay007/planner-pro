from .workers.schedule_worker import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass 
    finally:
        import sys
        sys.exit(0) 
