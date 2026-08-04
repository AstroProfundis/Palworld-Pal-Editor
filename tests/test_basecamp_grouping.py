import unittest
from types import SimpleNamespace

from palworld_pal_editor.core.basecamp_data import BaseCampData, PalBaseCamp
from palworld_pal_editor.core.group_data import GroupData, PalGroup
from palworld_pal_editor.core.save_manager import SaveManager
from palworld_pal_editor.utils.util import world_to_game_map_coordinates


def make_camp(
    camp_id="base-entry",
    raw_id="base-raw",
    group_id="guild-id",
    container_id="worker-container",
    translation=None,
):
    raw_data = {
        "id": raw_id,
        "name": "Main Base",
        "group_id_belong_to": group_id,
        "transform": {"translation": translation or {"x": 1.0, "y": 2.0, "z": 3.0}},
    }
    return {
        "key": camp_id,
        "value": {
            "RawData": {"value": raw_data},
            "WorkerDirector": {
                "value": {"RawData": {"value": {"container_id": container_id}}}
            },
        },
    }


def make_pal(instance_id, container_id, deck_id="SheepBall", level=1):
    return SimpleNamespace(
        InstanceId=instance_id,
        ContainerId=container_id,
        PalDeckID=deck_id,
        Level=level,
    )


class BaseCampGroupingTests(unittest.TestCase):
    def test_base_camp_uses_entry_id_and_worker_director_container(self):
        camp = PalBaseCamp(make_camp())

        self.assertEqual("base-entry", camp.id)
        self.assertEqual("worker-container", camp.container_id)
        self.assertEqual({"x": 1.0, "y": 2.0, "z": 3.0}, camp.world_translation)

    def test_base_camp_missing_worker_director_and_translation_are_safe(self):
        camp_obj = make_camp()
        camp_obj["value"].pop("WorkerDirector")
        camp_obj["value"]["RawData"]["value"]["transform"] = None

        camp = PalBaseCamp(camp_obj)

        self.assertIsNone(camp.container_id)
        self.assertIsNone(camp.world_translation)

    def test_base_camp_data_normalizes_lookup_ids(self):
        camp = PalBaseCamp(make_camp(camp_id="123"))
        data = object.__new__(BaseCampData)
        data.camp_map = {"123": camp}

        self.assertIs(camp, data.get_camp(123))
        self.assertEqual([camp], data.get_camps())
        self.assertEqual([camp], data.get_owned_camp("guild-id"))

    def test_group_lookups_normalize_ids_and_expose_base_level(self):
        group = PalGroup(
            {
                "value": {
                    "RawData": {
                        "value": {
                            "group_id": "guild-id",
                            "base_ids": ["base-id"],
                            "base_camp_level": 17,
                            "players": [
                                {
                                    "player_uid": 123,
                                    "player_info": {"player_name": "Player"},
                                }
                            ],
                        }
                    }
                }
            }
        )
        data = object.__new__(GroupData)
        data.group_map = {"guild-id": group}

        self.assertTrue(group.has_player("123"))
        self.assertEqual(17, group.base_camp_level)
        self.assertIs(group, data.get_group("guild-id"))
        self.assertIsNone(data.get_group(None))

    def test_world_coordinates_match_game_rounding(self):
        self.assertEqual(
            {"x": -344, "y": 270},
            world_to_game_map_coordinates(0.0, 0.0),
        )
        self.assertEqual(
            {"x": 1, "y": 1},
            world_to_game_map_coordinates(
                -123930.0 + (0.5 * 459.0),
                157935.0 + (0.5 * 459.0),
            ),
        )

    def test_base_groups_and_unassigned_workers_partition_all_workers(self):
        base_a = PalBaseCamp(make_camp(camp_id="base-a", container_id="container-a"))
        base_b = PalBaseCamp(make_camp(camp_id="base-b", container_id="container-b"))
        base_empty_obj = make_camp(camp_id="base-empty")
        base_empty_obj["value"].pop("WorkerDirector")
        base_empty = PalBaseCamp(base_empty_obj)
        camp_data = object.__new__(BaseCampData)
        camp_data.camp_map = {
            "base-a": base_a,
            "base-b": base_b,
            "base-empty": base_empty,
        }

        manager = object.__new__(SaveManager)
        manager.camp_data = camp_data
        manager.baseworker_mapping = {
            "a": make_pal("a", "container-a", level=2),
            "b": make_pal("b", "container-b", level=3),
            "legacy": make_pal("legacy", "unknown-container", level=4),
            "missing": make_pal("missing", None, level=5),
        }

        base_a_ids = {pal.InstanceId for pal in manager.get_base_working_pals("base-a")}
        base_b_ids = {pal.InstanceId for pal in manager.get_base_working_pals("base-b")}
        unassigned_ids = {pal.InstanceId for pal in manager.get_unassigned_working_pals()}

        self.assertEqual({"a"}, base_a_ids)
        self.assertEqual({"b"}, base_b_ids)
        self.assertEqual({"legacy", "missing"}, unassigned_ids)
        self.assertFalse(base_a_ids & base_b_ids)
        self.assertFalse((base_a_ids | base_b_ids) & unassigned_ids)
        self.assertEqual(
            set(manager.baseworker_mapping),
            base_a_ids | base_b_ids | unassigned_ids,
        )
        self.assertEqual([], manager.get_base_working_pals("base-empty"))
        self.assertIsNone(manager.get_base_working_pals("unknown-base"))


if __name__ == "__main__":
    unittest.main()
