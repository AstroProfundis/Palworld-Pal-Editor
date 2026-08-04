from typing import Optional

from palworld_save_tools.gvas import GvasFile
from palworld_save_tools.archive import UUID

from palworld_pal_editor.utils import LOGGER
from palworld_pal_editor.utils.data_provider import DataProvider

# The save format's sentinel for "no active research on the lab bench".
# Verified against a real save (GuildExtraSaveDataMap[*].Lab.RawData.current_research_id):
# guilds that never picked a target store the literal string "None", while an in-progress
# guild stores the actual research id (e.g. "Seeding2"). Writers must reuse this exact
# sentinel rather than "" so the field stays consistent with what the game itself writes.
NO_CURRENT_RESEARCH_ID = "None"


class PalGuildLab:
    """Wraps one guild's decoded `Lab.value.RawData.value` dict.

    That dict has the shape `{research_info: [{research_id, work_amount}, ...],
    current_research_id, trailing_bytes}`. Only `research_info` entries and
    `current_research_id` are mutated here; `trailing_bytes` is preserved untouched.
    """

    def __init__(self, lab_raw_data: dict):
        self._raw_data: dict = lab_raw_data
        self._research_index: dict[str, dict] = {
            entry["research_id"]: entry for entry in self.research_info
        }

    @property
    def research_info(self) -> list[dict]:
        return self._raw_data.setdefault("research_info", [])

    @property
    def current_research_id(self) -> str:
        return self._raw_data.get("current_research_id", NO_CURRENT_RESEARCH_ID)

    @current_research_id.setter
    def current_research_id(self, value: str) -> None:
        self._raw_data["current_research_id"] = value

    def get_work_amount(self, research_id: str) -> float:
        entry = self._research_index.get(research_id)
        return entry["work_amount"] if entry else 0.0

    def set_work_amount(self, research_id: str, amount: float) -> None:
        # Store as float to stay consistent with the save's native work_amount type
        # (the field is encoded as a float; catalog WorkAmount is an int).
        amount = float(amount)
        entry = self._research_index.get(research_id)
        if entry is None:
            entry = {"research_id": research_id, "work_amount": amount}
            self._research_index[research_id] = entry
            self.research_info.append(entry)
            return
        entry["work_amount"] = amount

    def is_completed(self, research_id: str) -> bool:
        required = DataProvider.get_research_work_amount(research_id)
        return required > 0 and self.get_work_amount(research_id) >= required

    def completed_research_ids(self) -> list[str]:
        return [
            research_id
            for research_id in self._research_index
            if self.is_completed(research_id)
        ]

    def toggle_research(self, research_id: str, status: bool) -> None:
        if status:
            self._unlock(research_id)
        else:
            self._cancel(research_id)

    def _unlock(self, research_id: str) -> None:
        if self.is_completed(research_id):
            LOGGER.warning(f"Research {research_id} is already completed, skipping")
            return

        unlocked: list[str] = []
        for target_id in (*DataProvider.get_research_ancestors(research_id), research_id):
            if self.is_completed(target_id):
                continue
            required = DataProvider.get_research_work_amount(target_id)
            if required <= 0:
                LOGGER.warning(
                    f"Research {target_id} has no catalog WorkAmount, skipping"
                )
                continue
            self.set_work_amount(target_id, required)
            unlocked.append(target_id)
            # A completed research can't remain the bench's active target.
            if self.current_research_id == target_id:
                self.current_research_id = NO_CURRENT_RESEARCH_ID

        LOGGER.info(f"Unlocked research {research_id}, cascaded ancestors: {unlocked}")

    def _cancel(self, research_id: str) -> None:
        if self.get_work_amount(research_id) <= 0:
            LOGGER.warning(f"Research {research_id} is already locked, skipping")
            return

        descendants = DataProvider.get_research_descendants(research_id)
        targets = (research_id, *descendants)
        for target_id in targets:
            self.set_work_amount(target_id, 0.0)
        if self.current_research_id in targets:
            self.current_research_id = NO_CURRENT_RESEARCH_ID

        LOGGER.info(f"Cancelled research {research_id}, cascaded descendants: {descendants}")

    def unlock_all_research(self) -> None:
        for research_id, _ in DataProvider.iter_displayable_research():
            required = DataProvider.get_research_work_amount(research_id)
            if required > 0:
                self.set_work_amount(research_id, required)
        self.current_research_id = NO_CURRENT_RESEARCH_ID
        LOGGER.info("Unlocked all research")


class GuildExtraData:
    def __init__(self, gvas_file: GvasFile) -> None:
        self.guild_lab_map: dict[str, PalGuildLab] = {}
        wsd = gvas_file.properties["worldSaveData"]["value"]
        if "GuildExtraSaveDataMap" not in wsd:
            LOGGER.info("No Guild Extra Data Found")
            return

        for entry in wsd["GuildExtraSaveDataMap"]["value"]:
            guild_id: UUID = entry.get("key")
            if not guild_id:
                continue

            lab_property = entry.get("value", {}).get("Lab")
            if lab_property is None:
                continue
            raw_data_property = lab_property.get("value", {}).get("RawData")
            if raw_data_property is None:
                continue
            raw_data = raw_data_property.get("value")
            if not isinstance(raw_data, dict) or "research_info" not in raw_data:
                LOGGER.warning(f"Guild {guild_id} has an undecoded Lab.RawData, skipping")
                continue

            self.guild_lab_map[str(guild_id)] = PalGuildLab(raw_data)
            LOGGER.info(f"Guild Lab Found: {guild_id}")

    def get_guild_lab(self, guild_id: UUID | str | None) -> Optional[PalGuildLab]:
        if guild_id is None:
            return None
        return self.guild_lab_map.get(str(guild_id))

    def get_guild_labs(self) -> list[PalGuildLab]:
        return list(self.guild_lab_map.values())
