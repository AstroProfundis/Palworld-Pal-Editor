import traceback

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from palworld_pal_editor.core import SaveManager
from palworld_pal_editor.core.basecamp_data import PalBaseCamp
from palworld_pal_editor.core.pal_objects import PalObjects
from palworld_pal_editor.core.player_entity import PlayerEntity
from palworld_pal_editor.utils import LOGGER, DataProvider
from palworld_pal_editor.utils.util import reply, world_to_game_map_coordinates

player_blueprint = Blueprint("player", __name__)


@player_blueprint.route("/player_pals", methods=["POST"])
@jwt_required()
def get_player_pals():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return reply(1, None, "Request body must be a JSON object")

    selector_names = (
        "PlayerUId",
        "BaseCampId",
        "UnassignedBaseWorkers",
    )
    selectors = [name for name in selector_names if name in payload]
    if len(selectors) != 1:
        return reply(1, None, "Exactly one pal owner selector is required")

    manager = SaveManager()
    player_entity = None
    selector = selectors[0]
    if selector == "BaseCampId":
        base_id = payload[selector]
        pals = manager.get_base_working_pals(base_id)
        if pals is None:
            return reply(1, None, f"Base camp {base_id} not found")
    elif selector == "UnassignedBaseWorkers":
        if payload[selector] is not True:
            return reply(1, None, "UnassignedBaseWorkers must be true")
        pals = manager.get_unassigned_working_pals()
    else:
        player_id = payload[selector]
        if player_id == "PAL_BASE_WORKER_BTN":
            pals = manager.get_working_pals()
        else:
            player_entity = manager.get_player(player_id)
            if not player_entity:
                return reply(1, None, f"Player {player_id} Not Found")
            pals = player_entity.get_sorted_pals()

    party_container_id = player_entity.OtomoCharacterContainerId if player_entity else None
    storage_container_id = player_entity.PalStorageContainerId if player_entity else None

    return reply(
        0,
        [
            pal_list_item_to_dict(
                pal,
                party_container_id=party_container_id,
                storage_container_id=storage_container_id,
            )
            for pal in pals
        ],
    )


def pal_list_item_to_dict(
    pal,
    party_container_id=None,
    storage_container_id=None,
):
    return {
        "InstanceId": str(pal.InstanceId) if pal.InstanceId else None,
        "IconAccessKey": pal.IconAccessKey or None,
        "DataAccessKey": pal.DataAccessKey or None,
        "I18nName": pal.I18nName or None,
        "DisplayName": pal.DisplayName or None,
        "Gender": pal.Gender.value if pal.Gender else None,
        "IsTower": pal.IsTower or False,
        "IsBOSS": pal.IsBOSS or False,
        "IsRarePal": pal.IsRarePal or False,
        "IsAwakening": pal.IsAwakening,
        "IsNewPal": pal.is_new_pal,
        "Level": pal.Level or 1,
        "Exp": pal.Exp or 0,
        "ExpStatus": pal.ExpStatus,
        "FriendshipLevel": pal.FriendshipLevel or 0,
        "Talent_HP": pal.Talent_HP or 0,
        "Talent_Shot": pal.Talent_Shot or 0,
        "Talent_Defense": pal.Talent_Defense or 0,
        "ContainerId": str(pal.ContainerId) if pal.ContainerId else None,
        "SlotIndex": pal.SlotIndex,
        "ContainerKind": (
            "party"
            if pal.ContainerId == party_container_id
            else "storage"
            if pal.ContainerId == storage_container_id
            else "other"
        ),
        "FavoriteIndex": pal.FavoriteIndex,
        "IsFavoritePal": bool(pal.IsFavoritePal),
        "Is_Unref_Pal": pal.is_unreferenced_pal,
        "in_owner_palbox": pal.in_owner_palbox,
    }


@player_blueprint.route("/players_data", methods=["GET"])
@jwt_required()
def get_player_list():
    manager = SaveManager()
    working_pals = manager.get_working_pals()
    unassigned_pals = manager.get_unassigned_working_pals()
    players = list(manager.get_players())
    bases = manager.get_bases()
    if not players and not bases and not unassigned_pals:
        return reply(1, None, "No Player or Base Found")
    return reply(
        0,
        {
            "players": [player_to_dict(player) for player in players],
            "bases": [base_to_dict(base, manager) for base in bases],
            "hasWorkingPal": bool(working_pals),
            "hasUnassignedWorkingPal": bool(unassigned_pals),
        },
    )


def base_to_dict(base: PalBaseCamp, manager: SaveManager):
    group = manager.group_data.get_group(base.owner_group_id)
    world_translation = base.world_translation
    map_coordinates = None
    if isinstance(world_translation, dict):
        world_x = world_translation.get("x")
        world_y = world_translation.get("y")
        if (
            isinstance(world_x, (int, float))
            and not isinstance(world_x, bool)
            and isinstance(world_y, (int, float))
            and not isinstance(world_y, bool)
        ):
            map_coordinates = world_to_game_map_coordinates(world_x, world_y)

    working_pals = manager.get_base_working_pals(base.id)
    if working_pals is None:
        raise RuntimeError(f"Base camp {base.id} disappeared while serializing")

    return {
        "Id": str(base.id) if base.id else None,
        "Name": base.name or None,
        "GuildId": str(group.group_id) if group and group.group_id else None,
        "GuildName": group.guild_name if group else None,
        # Palworld stores this level on the guild record rather than per base.
        "BaseCampLevel": group.base_camp_level if group else None,
        "WorkerCount": len(working_pals),
        "WorldTranslation": world_translation,
        "MapCoordinates": map_coordinates,
        "ContainerId": str(base.container_id) if base.container_id else None,
    }


@player_blueprint.route("/player_data", methods=["POST"])
@jwt_required()
def get_player_data():
    PlayerUId = request.json.get("PlayerUId")

    if PlayerUId == "PAL_BASE_WORKER_BTN":
        LOGGER.warning(f"PAL_BASE_WORKER_BTN is not a real player")
        return reply(1, None, f"PAL_BASE_WORKER_BTN is not a real player")

    player_entity = SaveManager().get_player(PlayerUId)
    if not player_entity:
        LOGGER.warning(f"Player {PlayerUId} not exist")
        return reply(1, None, f"Player {PlayerUId} not exist")

    player_dict = player_to_dict(player_entity)
    player_dict["UnlockedRecipeTechnologyNames"] = (
        player_entity.UnlockedRecipeTechnologyNames or []
    )

    return reply(0, player_dict)


def player_to_dict(player: PlayerEntity):
    return {
        "InstanceId": str(player.PlayerUId),
        "NickName": player.NickName or "",
        "Level": player.Level or 1,
        "Exp": player.Exp or 0,
        "UnusedStatusPoint": player.UnusedStatusPoint or 0,
        "StatusPoints": player.StatusPoints,
        "ExStatusPoints": player.ExStatusPoints,
        "StatusPointTotals": player.StatusPointTotals,
        "StatusPointMinimums": player.StatusPointMinimums,
        "StatusPointMaximums": player.StatusPointMaximums,
        "StatusPointTotalMaximums": PalObjects.StatusPointMaximums,
        "StatusPointMetadata": DataProvider.get_player_status_data(),
        "HasViewingCage": player.has_viewing_cage(),
        "OtomoCharacterContainerId": str(player.OtomoCharacterContainerId),
        "PalStorageContainerId": str(player.PalStorageContainerId),
        "UnlockedRecipeTechnologyNames": [],
        "TechnologyPoint": player.TechnologyPoint or 0,
        "bossTechnologyPoint": player.bossTechnologyPoint or 0,
    }


@player_blueprint.route("/player_data", methods=["PATCH"])
@jwt_required()
def patch_player_data():
    PlayerUId = request.json.get("PlayerUId")
    key = request.json.get("key")
    value = request.json.get("value")

    if PlayerUId == "PAL_BASE_WORKER_BTN":
        LOGGER.warning(f"PAL_BASE_WORKER_BTN is not a real player")
        return reply(1, None, f"PAL_BASE_WORKER_BTN is not a real player")

    player_entity = SaveManager().get_player(PlayerUId)
    if not player_entity:
        LOGGER.warning(f"Player {PlayerUId} not exist")
        return reply(1, None, f"Player {PlayerUId} not exist")

    try:
        match key:
            case "toggle_UnlockedRecipeTechnologyNames":
                player_entity.toggle_UnlockedRecipeTechnologyNames(value["tech"], value["status"])
            case "unlock_all_techs":
                player_entity.unlock_all_techs()
            case "unlock_viewing_cage":
                player_entity.unlock_viewing_cage()
            case "set_StatusPoint":
                player_entity.set_StatusPoint(value["name"], value["points"])
            case "set_TotalStatusPoint":
                player_entity.set_TotalStatusPoint(value["name"], value["points"])
            case _:
                field = getattr(type(player_entity), key, None)
                if not isinstance(field, property) or field.fset is None:
                    return reply(1, None, f"Unsupported player field: {key}")
                setattr(player_entity, key, value)
    except Exception as e:
        stack_trace = traceback.format_exc()
        LOGGER.error(f"Error in patching player data {stack_trace}, key: {key}, value: {value}")
        return reply(1, None, f"Error in patching player data {stack_trace}")
    return reply(0)
