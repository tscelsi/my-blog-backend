import logging

from cedarpy import is_authorized  # type: ignore[import]

from api.service_manager import ServiceManager
from entities.user import User
from paths import SRC_DIR
from sharing.exceptions import AuthorisationError
from sharing.resources import CedarUser

logger = logging.getLogger(__name__)
with open(SRC_DIR / "sharing" / "policies.cedar", "r") as f:
    policies = f.read()


def authorise(
    principal: User,
    action: str,
    resource_eid: str,
    service_manager: ServiceManager,
):
    cedar_principal = CedarUser.from_user(principal)
    resource = service_manager.permissions_manager.get_resource(resource_eid)
    res = is_authorized(
        {
            "principal": cedar_principal.cedar_eid_str(),
            "action": action,
            "resource": resource_eid,
            "context": {},
        },
        policies,
        [cedar_principal.cedar_schema(), resource.cedar_schema()],
    )
    if not res.allowed:
        logger.warning(res)
        raise AuthorisationError(
            f"User {principal.id} not authorised to perform action {action} on resource {resource.id}",  # noqa: E501
            detail=res,
        )
