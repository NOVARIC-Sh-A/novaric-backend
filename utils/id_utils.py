import re
from typing import Optional, Union

def vip_to_int(v: Union[str, int, None]) -> Optional[int]:
    if v is None:
        return None
    if isinstance(v, int):
        return v
    m = re.search(r"(\d+)$", str(v).strip(), flags=re.IGNORECASE)
    return int(m.group(1)) if m else None

def int_to_vip(pid: int) -> str:
    return f"vip{int(pid)}"
