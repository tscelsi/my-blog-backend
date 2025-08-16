import logging

from cedarpy import AuthzResult, is_authorized  # type: ignore

from entities.account import Account
from entities.memory import Memory
from entities.user import User
from paths import SRC_DIR

logger = logging.getLogger(__name__)
with open(SRC_DIR / "utils" / "permissions" / "policies.cedar", "r") as f:
    policies = f.read()


class AuthorisationError(Exception):
    def __init__(self, message: str, _result: AuthzResult):
        super().__init__(message)
        self.detail = _result


def inline_authorise(principal: User, action: str, resource: Memory | Account):
    res = is_authorized(
        {
            "principal": principal.cedar_eid(True),
            "action": action,
            "resource": resource.cedar_eid(True),
            "context": {},
        },
        policies,
        [principal.cedar_schema(), resource.cedar_schema()],
    )
    if not res.allowed:
        logger.warning(res)
        raise AuthorisationError(
            f"User {principal.id} not authorised to perform action {action} on resource {resource.id}",  # noqa: E501
            _result=res,
        )
