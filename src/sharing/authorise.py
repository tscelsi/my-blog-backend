import logging

from cedarpy import is_authorized  # type: ignore[import]

from api.service_manager import ServiceManager
from entities.account import Account
from entities.memory import Memory
from entities.user import User
from paths import SRC_DIR

from .exceptions import AuthorisationError

logger = logging.getLogger(__name__)
with open(SRC_DIR / "sharing" / "policies.cedar", "r") as f:
    policies = f.read()


def inline_authorise(principal: User, action: str, resource: Memory | Account):
    res = is_authorized(
        {
            "principal": principal.cedar_eid_str(),
            "action": action,
            "resource": resource.cedar_eid_str(),
            "context": {},
        },
        policies,
        [principal.cedar_schema(), resource.cedar_schema()],
    )
    if not res.allowed:
        logger.warning(res)
        raise AuthorisationError(
            f"User {principal.id} not authorised to perform action {action} on resource {resource.id}",  # noqa: E501
            detail=res,
        )


def authorise(
    principal: User,
    action: str,
    resource_eid: str,
    service_manager: ServiceManager,
):
    resource = service_manager.permissions_manager.get_resource(resource_eid)
    res = is_authorized(
        {
            "principal": principal.cedar_eid_str(),
            "action": action,
            "resource": resource_eid,
            "context": {},
        },
        policies,
        [principal.cedar_schema(), resource.cedar_schema()],
    )
    if not res.allowed:
        logger.warning(res)
        raise AuthorisationError(
            f"User {principal.id} not authorised to perform action {action} on resource {resource.id}",  # noqa: E501
            detail=res,
        )
