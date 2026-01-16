from typing import Optional, Dict, Any


class ValidatorBase:
    name: str = "base"

    def run(
        self,
        name: Optional[str] = None,
        region: Optional[str] = None,
        account_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError()
