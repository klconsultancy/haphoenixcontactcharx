"""Button platform for Phoenix Contact CHARX integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity

from .entity import CharxEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CharxConfigEntry, CharxCoordinator


class CharxClearDynamicMaxCurrentButton(CharxEntity, ButtonEntity):
    """Clear the Group's Dynamic Max Current (167), so no dynamic limit applies.

    The number sets a limit; a number can't hold "no limit", so this clears it.
    """

    _attr_translation_key = "clear_dynamic_max_current"

    def __init__(self, coordinator: CharxCoordinator) -> None:
        """Clear the Group's Dynamic Max Current."""
        super().__init__(coordinator, "clear_dynamic_max_current")

    async def async_press(self) -> None:
        """Clear the limit (the library writes 65535)."""
        await self._write(lambda: self._group.set_dynamic_max_current(None), self.entity_id)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CharxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the button that clears the Group's Dynamic Max Current."""
    async_add_entities([CharxClearDynamicMaxCurrentButton(entry.runtime_data)])
