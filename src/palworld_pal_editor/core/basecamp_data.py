from typing import Optional

from palworld_save_tools.gvas import GvasFile
from palworld_save_tools.archive import UUID

from palworld_pal_editor.utils import LOGGER


class PalBaseCamp:
    def __init__(self, camp_obj: dict):
        self._camp_obj: dict = camp_obj
        self._camp_param: dict = camp_obj["value"]["RawData"]["value"]
        self._camp_id: Optional[UUID] = camp_obj.get("key") or self._camp_param.get(
            "id"
        )

        if (not self.id) or (not self.owner_group_id):
            LOGGER.warning(str(self._camp_param))
            raise ValueError("possible broken camp object")

        raw_camp_id = self._camp_param.get("id")
        if raw_camp_id and str(raw_camp_id) != str(self.id):
            LOGGER.warning(
                f"Base camp entry key {self.id} does not match RawData id "
                f"{raw_camp_id}; using entry key"
            )

    def __str__(self) -> str:
        return f"{self.id} - {self.name} - Owner Guild: {self.owner_group_id} - Container: {self.container_id}"

    @property
    def id(self) -> Optional[UUID]:
        return self._camp_id

    @property
    def name(self) -> Optional[str]:
        return self._camp_param.get("name")

    @property
    def owner_group_id(self) -> Optional[UUID]:
        return self._camp_param.get("group_id_belong_to")

    @property
    def container_id(self) -> Optional[UUID]:
        try:
            raw_data = self._camp_obj["value"]["WorkerDirector"]["value"][
                "RawData"
            ]["value"]
        except (KeyError, TypeError):
            return None
        return raw_data.get("container_id") if isinstance(raw_data, dict) else None

    @property
    def world_translation(self) -> Optional[dict]:
        transform = self._camp_param.get("transform")
        if not isinstance(transform, dict):
            return None
        translation = transform.get("translation")
        return translation if isinstance(translation, dict) else None


class BaseCampData:
    def __init__(self, gvas_file: GvasFile) -> None:
        self.camp_map = {}

        self._wsd = gvas_file.properties["worldSaveData"]["value"]
        if "BaseCampSaveData" not in self._wsd:
            LOGGER.info("No Base Camp Found")
            return
        self._BCSD = self._wsd["BaseCampSaveData"]

        for camp in self._BCSD["value"]:
            camp_id: UUID = camp.get("key")
            if not camp_id:
                continue

            try:
                camp_entity = PalBaseCamp(camp)
            except (KeyError, TypeError, ValueError) as e:
                LOGGER.warning(f"Invalid Base Camp: {e}, skipping")
                continue

            self.camp_map[str(camp_id)] = camp_entity
            LOGGER.info(f"BaseCamp found: {camp_entity}")

    def get_camp(self, camp_id: UUID | str | None) -> Optional[PalBaseCamp]:
        if camp_id is None:
            return None
        return self.camp_map.get(str(camp_id))

    def get_camps(self) -> list[PalBaseCamp]:
        return list(self.camp_map.values())

    def get_owned_camp(self, group_id: UUID | str) -> list[PalBaseCamp]:
        return [
            camp
            for camp in self.get_camps()
            if str(camp.owner_group_id) == str(group_id)
        ]
