from typing import Optional, Dict, Any


class ValidatorBase:
    name: str = 'base'

    def run(self, name: str, region: Optional[str] = None, account_id: Optional[str] = None, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError()
