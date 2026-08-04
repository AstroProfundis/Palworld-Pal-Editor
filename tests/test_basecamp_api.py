import unittest
from types import SimpleNamespace
from unittest.mock import patch

from flask_jwt_extended import create_access_token

from palworld_pal_editor.webui import app


def make_pal(instance_id="pal-id"):
    return SimpleNamespace(
        InstanceId=instance_id,
        IconAccessKey="SheepBall",
        DataAccessKey="SheepBall",
        I18nName="Lamball",
        DisplayName="Lamball",
        Gender=None,
        IsTower=False,
        IsBOSS=False,
        IsRarePal=False,
        IsAwakening=False,
        is_new_pal=False,
        Level=5,
        Exp=100,
        ExpStatus=None,
        FriendshipLevel=2,
        Talent_HP=10,
        Talent_Shot=20,
        Talent_Defense=30,
        ContainerId="worker-container",
        SlotIndex=1,
        FavoriteIndex=3,
        IsFavoritePal=True,
        is_unreferenced_pal=False,
        in_owner_palbox=False,
    )


class BaseCampApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["JWT_SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"
        with app.app_context():
            cls.token = create_access_token(identity="test", expires_delta=False)

    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def test_player_pals_supports_each_owner_selector(self):
        pal = make_pal()

        class Player:
            OtomoCharacterContainerId = None
            PalStorageContainerId = None

            @staticmethod
            def get_sorted_pals():
                return [pal]

        manager = SimpleNamespace(
            get_player=lambda player_id: Player() if player_id == "player-id" else None,
            get_working_pals=lambda: [pal],
            get_base_working_pals=lambda base_id: [pal] if base_id == "base-id" else None,
            get_unassigned_working_pals=lambda: [pal],
        )

        with (
            patch("palworld_pal_editor.api.player.SaveManager", return_value=manager),
            app.test_client() as client,
        ):
            for request_body in (
                {"PlayerUId": "player-id"},
                {"PlayerUId": "PAL_BASE_WORKER_BTN"},
                {"BaseCampId": "base-id"},
                {"UnassignedBaseWorkers": True},
            ):
                with self.subTest(request_body=request_body):
                    response = client.post(
                        "/api/player/player_pals",
                        json=request_body,
                        headers=self.headers(),
                    ).get_json()
                    self.assertEqual(0, response["status"])
                    self.assertEqual("pal-id", response["data"][0]["InstanceId"])
                    self.assertEqual(30, response["data"][0]["Talent_Defense"])
                    self.assertTrue(response["data"][0]["IsFavoritePal"])

    def test_player_pals_rejects_invalid_selector_requests(self):
        manager = SimpleNamespace()
        with (
            patch("palworld_pal_editor.api.player.SaveManager", return_value=manager),
            app.test_client() as client,
        ):
            invalid_requests = (
                None,
                [],
                {},
                {"PlayerUId": "player", "BaseCampId": "base"},
                {"UnassignedBaseWorkers": False},
                {"UnassignedBaseWorkers": "true"},
                {"UnassignedBaseWorkers": 1},
            )
            for request_body in invalid_requests:
                with self.subTest(request_body=request_body):
                    kwargs = {"headers": self.headers()}
                    if request_body is not None:
                        kwargs["json"] = request_body
                    response = client.post(
                        "/api/player/player_pals",
                        **kwargs,
                    ).get_json()
                    self.assertEqual(1, response["status"])

    def test_unknown_base_is_not_confused_with_an_empty_base(self):
        manager = SimpleNamespace(
            get_base_working_pals=lambda base_id: [] if base_id == "empty" else None
        )
        with (
            patch("palworld_pal_editor.api.player.SaveManager", return_value=manager),
            app.test_client() as client,
        ):
            empty = client.post(
                "/api/player/player_pals",
                json={"BaseCampId": "empty"},
                headers=self.headers(),
            ).get_json()
            missing = client.post(
                "/api/player/player_pals",
                json={"BaseCampId": "missing"},
                headers=self.headers(),
            ).get_json()

        self.assertEqual((0, []), (empty["status"], empty["data"]))
        self.assertEqual(1, missing["status"])
        self.assertIn("not found", missing["msg"].lower())

    def test_players_data_includes_empty_bases_and_unassigned_workers(self):
        group = SimpleNamespace(
            group_id="guild-id",
            guild_name="Guild Name",
            base_camp_level=17,
        )
        base_with_group = SimpleNamespace(
            id="base-a",
            name="Main Base",
            owner_group_id="guild-id",
            container_id="worker-container",
            world_translation={"x": 0.0, "y": 0.0, "z": 5.0},
        )
        base_without_group = SimpleNamespace(
            id="base-b",
            name=None,
            owner_group_id="missing-guild",
            container_id=None,
            world_translation=None,
        )
        manager = SimpleNamespace(
            get_players=lambda: [],
            get_bases=lambda: [base_with_group, base_without_group],
            get_working_pals=lambda: [make_pal()],
            get_unassigned_working_pals=lambda: [make_pal("legacy")],
            get_base_working_pals=lambda base_id: [],
            group_data=SimpleNamespace(
                get_group=lambda group_id: group if group_id == "guild-id" else None
            ),
        )

        with (
            patch("palworld_pal_editor.api.player.SaveManager", return_value=manager),
            app.test_client() as client,
        ):
            payload = client.get(
                "/api/player/players_data",
                headers=self.headers(),
            ).get_json()

        self.assertEqual(0, payload["status"])
        self.assertEqual([], payload["data"]["players"])
        self.assertTrue(payload["data"]["hasWorkingPal"])
        self.assertTrue(payload["data"]["hasUnassignedWorkingPal"])
        self.assertEqual(2, len(payload["data"]["bases"]))
        first, second = payload["data"]["bases"]
        self.assertEqual("Guild Name", first["GuildName"])
        self.assertEqual(17, first["BaseCampLevel"])
        self.assertEqual({"x": -344, "y": 270}, first["MapCoordinates"])
        self.assertEqual(0, first["WorkerCount"])
        self.assertIsNone(second["GuildId"])
        self.assertIsNone(second["MapCoordinates"])


if __name__ == "__main__":
    unittest.main()
