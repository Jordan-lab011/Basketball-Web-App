from datetime import datetime
import math

##AVAILABLE FUNCTIONS
# clean_nans(obj)
# get_season_string(date: datetime.date = datetime.now())

_TEAM_MAP = { 
    1610612737: "ATL", 1610612738: "BOS", 1610612751: "BKN", 1610612766: "CHA", 1610612741: "CHI",
    1610612739: "CLE", 1610612742: "DAL", 1610612743: "DEN", 1610612765: "DET", 1610612744: "GSW", 
    1610612745: "HOU", 1610612754: "IND", 1610612746: "LAC", 1610612747: "LAL", 1610612763: "MEM", 
    1610612748: "MIA", 1610612749: "MIL", 1610612750: "MIN", 1610612740: "NOP", 1610612752: "NYK", 
    1610612760: "OKC", 1610612753: "ORL", 1610612755: "PHI", 1610612756: "PHX", 1610612757: "POR", 
    1610612758: "SAC", 1610612759: "SAS", 1610612761: "TOR", 1610612762: "UTA", 1610612764: "WAS" 
}

def clean_nans(obj):
    """Recursively replace NaN/Infinity with 'Nil'."""
    if isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nans(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return "Nil"   # ✅ instead of None
        return obj
    return obj

def get_season_string(date: datetime.date = datetime.now()) -> str:
    """
    Defaults to today's date
    Given a date, return the NBA season string like '2024-25'.
    NBA season starts in October and ends in June/July.
    """
    year = date.year
    if date.month >= 10:  # October or later → season starts this year
        return f"{year}-{str(year + 1)[-2:]}"
    else:  # Before October → season started the previous year
        return f"{year - 1}-{str(year)[-2:]}"