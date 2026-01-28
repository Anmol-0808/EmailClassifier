from datetime import datetime,timedelta

ALLOWED_RANGES={
    "7d":7,
    "15d":15,
    "30d":30
}

def get_time_cutoff(range_str:str)->datetime:
    if range_str not in ALLOWED_RANGES:
        raise ValueError("Invalid range.Allowed 7d ,15d,30d")
    
    days=ALLOWED_RANGES[range_str]
    cutoff_time=datetime.utcnow()-timedelta(days=days)

    return cutoff_time