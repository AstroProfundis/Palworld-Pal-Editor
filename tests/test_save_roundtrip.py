import hashlib
from pathlib import Path
import tempfile
import unittest

from palworld_pal_editor.core.save_manager import SaveManager


SAVE = (
    Path(__file__).parents[1]
    / "tests/saves/1.0/8C439FF04713B5F986F9CAB485575089"
)


class SaveRoundTripTests(unittest.TestCase):
    def test_1_0_base_grouping_queries_are_complete_and_read_only(self):
        source_paths = [SAVE / "Level.sav", *sorted((SAVE / "Players").glob("*.sav"))]
        original_hashes = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_paths
        }

        manager = SaveManager()
        self.assertIsNotNone(manager.open(str(SAVE)))

        groups = []
        for base in manager.get_bases():
            base_pals = manager.get_base_working_pals(base.id)
            self.assertIsNotNone(base_pals)
            groups.append({str(pal.InstanceId) for pal in base_pals})
        groups.append(
            {
                str(pal.InstanceId)
                for pal in manager.get_unassigned_working_pals()
            }
        )

        assigned_ids = set()
        for group in groups:
            self.assertTrue(assigned_ids.isdisjoint(group))
            assigned_ids.update(group)

        self.assertEqual(
            {str(instance_id) for instance_id in manager.baseworker_mapping},
            assigned_ids,
        )
        self.assertEqual(
            original_hashes,
            {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in source_paths
            },
        )

    def test_1_0_save_preserves_oodle_format_and_state(self):
        manager = SaveManager()
        self.assertIsNotNone(manager.open(str(SAVE)))
        level_path = SAVE / "Level.sav"
        player_path = SAVE / "Players/00000000000000000000000000000001.sav"
        original_hashes = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (level_path, player_path)
        }

        with tempfile.TemporaryDirectory(prefix="pal-editor-1.0-") as directory:
            output = Path(directory)
            self.assertTrue(manager.save(str(output)))
            self.assertEqual(b"PlM1", (output / "Level.sav").read_bytes()[8:12])
            self.assertIsNotNone(manager.open(str(output)))
            player = manager.get_player("00000000-0000-0000-0000-000000000001")
            self.assertEqual((80, 45_859_908), (player.Level, player.Exp))
            pal = manager.get_pal("cfab9a78-49bd-bf16-474f-6e83eee20d7a")
            self.assertEqual((3, 9, True), (pal.Rank, pal.RankUpExp, pal.IsAwakening))

        self.assertEqual(
            original_hashes,
            {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (level_path, player_path)
            },
        )


if __name__ == "__main__":
    unittest.main()
