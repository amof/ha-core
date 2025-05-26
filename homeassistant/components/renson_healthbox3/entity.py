"""Entity class for Renson ventilation unit."""

from collections.abc import Callable, Coroutine
from typing import Any, Concatenate

from pyhealthbox3.healthbox3 import (
    Healthbox3ApiClientAuthenticationError,
    Healthbox3ApiClientCommunicationError,
    Healthbox3ApiClientError,
)

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import RensonHealthboxCoordinator


class RensonHealthboxEntity(CoordinatorEntity[RensonHealthboxCoordinator]):
    """Defines a base Renson Healthbox entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RensonHealthboxCoordinator) -> None:
        """Initialize Renson Healthbox entity."""
        super().__init__(coordinator)
        healthbox_data = coordinator.data.healthbox_data
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.serial_number)},
            manufacturer=MANUFACTURER,
            model=healthbox_data.description,
            model_id=healthbox_data.description,
            serial_number=coordinator.serial_number,
            sw_version=healthbox_data.firmware_version,
        )


def exception_handler[_EntityT: RensonHealthboxEntity, **_P](
    func: Callable[Concatenate[_EntityT, _P], Coroutine[Any, Any, Any]],
) -> Callable[Concatenate[_EntityT, _P], Coroutine[Any, Any, None]]:
    """Decorate Renson Healthbox calls to handle exceptions.

    A decorator that wraps the passed in function, catches Renson Healthbox errors.
    """

    async def handler(self: _EntityT, *args: _P.args, **kwargs: _P.kwargs) -> None:
        try:
            await func(self, *args, **kwargs)
        except Healthbox3ApiClientAuthenticationError as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="authentication_error",
                translation_placeholders={"error": str(error)},
            ) from error
        except Healthbox3ApiClientCommunicationError as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={"error": str(error)},
            ) from error

        except Healthbox3ApiClientError as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unknown_error",
                translation_placeholders={"error": str(error)},
            ) from error

    return handler
