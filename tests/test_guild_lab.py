import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from flask_jwt_extended import create_access_token

from palworld_pal_editor.core.guild_lab_data import NO_CURRENT_RESEARCH_ID, PalGuildLab
from palworld_pal_editor.core.save_manager import SaveManager
from palworld_pal_editor.utils.data_provider import DataProvider
from palworld_pal_editor.webui import app


SAVE = (
    Path(__file__).parents[1]
    / "tests/saves/1.0/8C439FF04713B5F986F9CAB485575089"
)


def make_lab(research_info=None, current=NO_CURRENT_RESEARCH_ID):
    return PalGuildLab(
        {
            "research_info": list(research_info or []),
            "current_research_id": current,
            "trailing_bytes": b"\x00\x00",
        }
    )


class PalGuildLabTests(unittest.TestCase):
    def test_unlock_cascades_ancestors_and_clears_current_target(self):
        lab = make_lab(current="Seeding2")
        lab.toggle_research("Seeding2", True)

        self.assertEqual({"Seeding1", "Seeding2"}, set(lab.completed_research_ids()))
        self.assertEqual(
            DataProvider.get_research_work_amount("Seeding1"),
            lab.get_work_amount("Seeding1"),
        )
        self.assertEqual(NO_CURRENT_RESEARCH_ID, lab.current_research_id)
        self.assertEqual(b"\x00\x00", lab._raw_data["trailing_bytes"])

    def test_cancel_cascades_descendants_but_keeps_siblings(self):
        lab = make_lab(current="Seeding2")
        lab.toggle_research("Seeding2", True)
        lab.toggle_research("Cool1", True)

        lab.toggle_research("Seeding1", False)

        self.assertEqual({"Cool1"}, set(lab.completed_research_ids()))
        self.assertEqual(0.0, lab.get_work_amount("Seeding1"))
        self.assertEqual(0.0, lab.get_work_amount("Seeding2"))
        self.assertEqual(NO_CURRENT_RESEARCH_ID, lab.current_research_id)

    def test_unlock_all_completes_every_catalog_research(self):
        lab = make_lab(current="Cool1")
        lab.unlock_all_research()

        self.assertEqual(
            len(DataProvider.get_research_data()),
            len(lab.completed_research_ids()),
        )
        self.assertEqual(NO_CURRENT_RESEARCH_ID, lab.current_research_id)


class GuildApiTests(unittest.TestCase):
    @staticmethod
    def auth_header():
        app.config["JWT_SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"
        with app.app_context():
            token = create_access_token(identity="test", expires_delta=False)
        return {"Authorization": f"Bearer {token}"}

    def test_list_guilds_marks_lab_availability(self):
        class Group:
            group_id = "g-with-lab"
            guild_name = "Test Guild"

        class GroupData:
            @staticmethod
            def get_groups():
                return [Group()]

        class Manager:
            group_data = GroupData()

            @staticmethod
            def get_guild_lab(guild_id):
                return object() if str(guild_id) == "g-with-lab" else None

        with (
            patch("palworld_pal_editor.api.guild.SaveManager", return_value=Manager()),
            app.test_client() as client,
        ):
            response = client.get("/api/guild/list", headers=self.auth_header())

        payload = response.get_json()
        self.assertEqual(0, payload["status"])
        self.assertEqual(
            [{"GuildId": "g-with-lab", "GuildName": "Test Guild", "HasLab": True}],
            payload["data"]["guilds"],
        )

    def test_research_state_and_toggle_roundtrip_through_api(self):
        lab = make_lab()

        class Manager:
            @staticmethod
            def get_guild_lab(guild_id):
                return lab if str(guild_id) == "guild-1" else None

        with (
            patch("palworld_pal_editor.api.guild.SaveManager", return_value=Manager()),
            app.test_client() as client,
        ):
            headers = self.auth_header()
            state = client.post(
                "/api/guild/research", json={"GuildId": "guild-1"}, headers=headers
            ).get_json()
            self.assertEqual(0, state["status"])
            self.assertEqual([], state["data"]["completed_research_ids"])

            toggle = client.patch(
                "/api/guild/research",
                json={
                    "GuildId": "guild-1",
                    "key": "toggle_research",
                    "value": {"research": "Seeding2", "status": True},
                },
                headers=headers,
            ).get_json()
            self.assertEqual(0, toggle["status"])

            state = client.post(
                "/api/guild/research", json={"GuildId": "guild-1"}, headers=headers
            ).get_json()
            self.assertEqual(
                {"Seeding1", "Seeding2"}, set(state["data"]["completed_research_ids"])
            )
            self.assertIn("work_amounts", state["data"])

    def test_research_rejects_invalid_input(self):
        lab = make_lab()

        class Manager:
            @staticmethod
            def get_guild_lab(guild_id):
                return lab if str(guild_id) == "guild-1" else None

        with (
            patch("palworld_pal_editor.api.guild.SaveManager", return_value=Manager()),
            app.test_client() as client,
        ):
            headers = self.auth_header()
            missing_lab = client.post(
                "/api/guild/research", json={"GuildId": "guild-x"}, headers=headers
            ).get_json()
            self.assertEqual(1, missing_lab["status"])

            for value in (
                {"research": "NotARealResearch", "status": True},
                {"research": "Seeding1", "status": "yes"},
                "Seeding1",
            ):
                response = client.patch(
                    "/api/guild/research",
                    json={
                        "GuildId": "guild-1",
                        "key": "toggle_research",
                        "value": value,
                    },
                    headers=headers,
                ).get_json()
                self.assertEqual(1, response["status"], value)

            unknown_key = client.patch(
                "/api/guild/research",
                json={"GuildId": "guild-1", "key": "drop_table", "value": {}},
                headers=headers,
            ).get_json()
            self.assertEqual(1, unknown_key["status"])

            for method in (client.post, client.patch):
                for kwargs in ({}, {"json": []}, {"data": "{"}):
                    response = method(
                        "/api/guild/research",
                        headers=headers,
                        **kwargs,
                    )
                    self.assertEqual(200, response.status_code)
                    self.assertEqual(1, response.get_json()["status"])

        self.assertEqual([], lab.completed_research_ids())

    def test_research_before_loading_a_save_returns_a_business_error(self):
        manager = SaveManager()
        manager._clear_loaded_state()

        with app.test_client() as client:
            response = client.post(
                "/api/guild/research",
                json={"GuildId": "guild-1"},
                headers=self.auth_header(),
            )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.get_json()["status"])


class GuildLabSaveRoundTripTests(unittest.TestCase):
    @staticmethod
    def guild_extra_data(manager):
        return manager.gvas_file.properties["worldSaveData"]["value"][
            "GuildExtraSaveDataMap"
        ]["value"]

    def test_unmodified_guild_extra_data_roundtrips_without_changes(self):
        manager = SaveManager()
        self.assertIsNotNone(manager.open(str(SAVE)))
        original = copy.deepcopy(self.guild_extra_data(manager))

        with tempfile.TemporaryDirectory(prefix="pal-editor-guild-extra-") as directory:
            self.assertTrue(manager.save(directory))

            reloaded = SaveManager()
            self.assertIsNotNone(reloaded.open(directory))
            self.assertEqual(original, self.guild_extra_data(reloaded))

    def test_unknown_lab_payload_is_preserved_and_disables_research(self):
        manager = SaveManager()
        self.assertIsNotNone(manager.open(str(SAVE)))
        guild_entry = self.guild_extra_data(manager)[0]
        guild_id = str(guild_entry["key"])
        raw_data = guild_entry["value"]["Lab"]["value"]["RawData"]
        raw_data["value"] = {"values": b"\x01\x02\x03"}

        with tempfile.TemporaryDirectory(prefix="pal-editor-unknown-lab-") as directory:
            self.assertTrue(manager.save(directory))

            reloaded = SaveManager()
            self.assertIsNotNone(reloaded.open(directory))
            self.assertIsNone(reloaded.get_guild_lab(guild_id))
            reloaded_raw_data = self.guild_extra_data(reloaded)[0]["value"]["Lab"][
                "value"
            ]["RawData"]
            self.assertEqual(b"\x01\x02\x03", reloaded_raw_data["value"]["values"])

            second_directory = Path(directory) / "second"
            self.assertTrue(reloaded.save(str(second_directory)))
            second_reload = SaveManager()
            self.assertIsNotNone(second_reload.open(str(second_directory)))
            second_raw_data = self.guild_extra_data(second_reload)[0]["value"]["Lab"][
                "value"
            ]["RawData"]
            self.assertEqual(b"\x01\x02\x03", second_raw_data["value"]["values"])

    def test_research_unlock_persists_through_save_and_reload(self):
        manager = SaveManager()
        self.assertIsNotNone(manager.open(str(SAVE)))
        level_path = SAVE / "Level.sav"
        original_hash = hashlib.sha256(level_path.read_bytes()).hexdigest()

        lab = next(iter(manager.guild_extra_data.guild_lab_map.values()))
        guild_entry = self.guild_extra_data(manager)[0]
        non_lab_before = copy.deepcopy(
            {key: value for key, value in guild_entry["value"].items() if key != "Lab"}
        )
        trailing_bytes_before = copy.deepcopy(lab._raw_data.get("trailing_bytes"))
        self.assertNotIn("Cool2", lab.completed_research_ids())
        self.assertIn("Cool1", lab.completed_research_ids())
        lab.toggle_research("Cool2", True)

        with tempfile.TemporaryDirectory(prefix="pal-editor-guild-lab-") as directory:
            self.assertTrue(manager.save(directory))

            reloaded = SaveManager()
            self.assertIsNotNone(reloaded.open(directory))
            reloaded_lab = next(
                iter(reloaded.guild_extra_data.guild_lab_map.values())
            )
            self.assertIn("Cool2", reloaded_lab.completed_research_ids())
            self.assertIn("Seeding2", reloaded_lab.completed_research_ids())
            reloaded_entry = self.guild_extra_data(reloaded)[0]
            self.assertEqual(
                non_lab_before,
                {key: value for key, value in reloaded_entry["value"].items() if key != "Lab"},
            )
            self.assertEqual(
                trailing_bytes_before,
                reloaded_lab._raw_data.get("trailing_bytes"),
            )

        self.assertEqual(
            original_hash, hashlib.sha256(level_path.read_bytes()).hexdigest()
        )


if __name__ == "__main__":
    unittest.main()
