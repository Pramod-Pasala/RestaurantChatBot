import re

def get_session_id(session_string: str):
    match = re.search(r"/sessions/(.*?)/contexts/",session_string)
    if match:
        return match.group(1)
    
    return ""

