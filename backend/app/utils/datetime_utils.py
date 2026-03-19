from datetime import datetime,timezone

class DateTimeUtils:
    
    @staticmethod
    def local_wo_micr() -> datetime:
        return datetime.now().replace(microsecond=0)
    
    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)
    
    @staticmethod
    def now_utc_wo_micr() -> datetime:
        return datetime.now(timezone.utc).replace(microsecond=0)
    
    @staticmethod
    def now_str() -> str:
        return datetime.now().strftime("%Y%m%d%H%M%S")