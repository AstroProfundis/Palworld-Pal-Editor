import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from palworld_pal_editor.api.pal import _pal_data
from palworld_pal_editor.core.pal_entity import PalEntity
from palworld_pal_editor.core.pal_objects import PalObjects
from palworld_pal_editor.core.save_manager import SaveManager
from palworld_pal_editor.utils.data_provider import DataProvider


SAVE = (
    Path(__file__).parents[1]
    / "tests/saves/1.0/8C439FF04713B5F986F9CAB485575089"
)


class PalUpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = SaveManager()
        if cls.manager.open(str(SAVE)) is None:
            raise AssertionError("1.0 fixture failed to load")
        cls.pals = [
            pal
            for player in cls.manager.get_players()
            for pal in player._palbox.values()
        ] + list(cls.manager.baseworker_mapping.values())

    def test_level_80_assignment_preserves_existing_exp(self):
        self.assertEqual(80, PalEntity.MAX_LEVEL)
        pal = next(
            item for item in self.pals if item.Level == 80 and item.Exp == 637_561_014
        )
        original = copy.deepcopy(pal._pal_param)
        try:
            pal.Level = pal.Level
            self.assertEqual(637_561_014, pal.Exp)
        finally:
            pal._pal_param = original

    def test_rank_change_clears_hidden_condensation_progress(self):
        pal = next(
            item
            for item in self.pals
            if str(item.InstanceId) == "cfab9a78-49bd-bf16-474f-6e83eee20d7a"
        )
        original = copy.deepcopy(pal._pal_param)
        try:
            self.assertEqual((3, 9), (pal.Rank, pal.RankUpExp))
            self.assertTrue(pal.IsAwakening)
            self.assertEqual(9, _pal_data(pal)["RankUpExp"])

            pal.Rank = 3
            self.assertEqual(9, pal.RankUpExp)
            pal.Rank = 2
            self.assertEqual(0, pal.RankUpExp)
            self.assertNotIn("RankUpExp", pal._pal_param)
        finally:
            pal._pal_param = original

    def test_skin_edit_keeps_applier_guid_in_sync(self):
        pal = next(
            item
            for item in self.pals
            if item.DataAccessKey == "GrassBoss"
            and item.SkinName == "GrassBoss_Skin001"
        )
        original = copy.deepcopy(pal._pal_param)
        try:
            self.assertEqual(pal.OwnerPlayerUId, pal.SkinAppliedCharacterId)
            pal.SkinName = None
            self.assertNotIn("SkinName", pal._pal_param)
            self.assertNotIn("SkinAppliedCharacterId", pal._pal_param)
            pal.SkinName = "GrassBoss_Skin001"
            self.assertEqual(pal.OwnerPlayerUId, pal.SkinAppliedCharacterId)
        finally:
            pal._pal_param = original

    def test_base_worker_skin_uses_last_owner(self):
        pal = next(
            item
            for item in self.manager.baseworker_mapping.values()
            if item.RawSpecieKey == "Anubis" and item.OwnerPlayerUId is None
        )
        original = copy.deepcopy(pal._pal_param)
        try:
            self.assertIsNotNone(pal.LastOwnerPlayerUId)
            pal.SkinName = "Anubis_Skin001"
            self.assertEqual(pal.LastOwnerPlayerUId, pal.SkinAppliedCharacterId)
        finally:
            pal._pal_param = original

    def test_randomize_ivs_updates_all_active_iv_fields(self):
        pal = self.pals[0]
        original = copy.deepcopy(pal._pal_param)
        try:
            with patch(
                "palworld_pal_editor.core.pal_entity.random.randint",
                side_effect=(40, 70, 100),
            ):
                values = pal.randomize_ivs(40)

            self.assertEqual(
                {"Talent_HP": 40, "Talent_Shot": 70, "Talent_Defense": 100},
                values,
            )
            self.assertEqual(40, pal.Talent_HP)
            self.assertEqual(70, pal.Talent_Shot)
            self.assertEqual(100, pal.Talent_Defense)
        finally:
            pal._pal_param = original

    def test_randomize_ivs_rejects_invalid_minimum(self):
        pal = self.pals[0]
        for value, error in ((True, TypeError), (1.5, TypeError), (0, ValueError), (101, ValueError)):
            with self.subTest(value=value):
                with self.assertRaises(error):
                    pal.randomize_ivs(value)

    def test_exp_status_flags_consistent_mismatched_and_over_max_values(self):
        pal = object.__new__(PalEntity)
        pal._pal_param = {
            "Level": PalObjects.ByteProperty(80),
            "Exp": PalObjects.Int64Property(DataProvider.get_pal_level_xp(80)),
        }
        self.assertIsNone(pal.ExpStatus)

        pal._pal_param["Exp"] = PalObjects.Int64Property(
            DataProvider.get_pal_level_xp(66)
        )
        self.assertEqual("mismatch", pal.ExpStatus)

        max_level = DataProvider.get_pal_exp_table_max_level()
        pal._pal_param["Exp"] = PalObjects.Int64Property(
            DataProvider.get_pal_level_xp(max_level) + 1
        )
        self.assertEqual("over_max", pal.ExpStatus)


if __name__ == "__main__":
    unittest.main()
