import traceback
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from palworld_pal_editor.core import SaveManager
from palworld_pal_editor.utils import LOGGER, DataProvider
from palworld_pal_editor.utils.util import reply

guild_blueprint = Blueprint("guild", __name__)


def _request_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, reply(1, None, "Request body must be a JSON object")
    return payload, None


@guild_blueprint.route("/list", methods=["GET"])
@jwt_required()
def list_guilds():
    save_manager = SaveManager()
    group_data = getattr(save_manager, "group_data", None)
    guilds = []
    for group in group_data.get_groups() if group_data else []:
        # Only guild-type groups carry a guild_name in their raw data.
        if group.guild_name is None or group.group_id is None:
            continue
        guilds.append(
            {
                "GuildId": str(group.group_id),
                "GuildName": group.guild_name,
                "HasLab": save_manager.get_guild_lab(group.group_id) is not None,
            }
        )
    return reply(0, {"guilds": guilds})


@guild_blueprint.route("/research", methods=["POST"])
@jwt_required()
def get_guild_research():
    payload, error = _request_payload()
    if error is not None:
        return error
    guild_id = payload.get("GuildId")
    if not isinstance(guild_id, str) or not guild_id:
        return reply(1, None, "GuildId must be a non-empty string")

    lab = SaveManager().get_guild_lab(guild_id)
    if lab is None:
        LOGGER.warning(f"Guild {guild_id} has no lab data")
        return reply(1, None, f"Guild {guild_id} has no lab data")

    return reply(
        0,
        {
            "completed_research_ids": lab.completed_research_ids(),
            "current_research_id": lab.current_research_id,
            "work_amounts": {
                entry["research_id"]: entry["work_amount"]
                for entry in lab.research_info
            },
        },
    )


@guild_blueprint.route("/research", methods=["PATCH"])
@jwt_required()
def patch_guild_research():
    payload, error = _request_payload()
    if error is not None:
        return error
    guild_id = payload.get("GuildId")
    key = payload.get("key")
    value = payload.get("value")

    if not isinstance(guild_id, str) or not guild_id:
        return reply(1, None, "GuildId must be a non-empty string")

    lab = SaveManager().get_guild_lab(guild_id)
    if lab is None:
        LOGGER.warning(f"Guild {guild_id} has no lab data")
        return reply(1, None, f"Guild {guild_id} has no lab data")

    match key:
        case "toggle_research":
            if not isinstance(value, dict):
                return reply(1, None, "toggle_research value must be an object")
            research_id = value.get("research")
            status = value.get("status")
            if not isinstance(status, bool):
                return reply(1, None, "toggle_research status must be a boolean")
            if not isinstance(research_id, str) or not DataProvider.is_research_displayable(research_id):
                return reply(1, None, f"Unknown research id: {research_id}")
            try:
                lab.toggle_research(research_id, status)
            except Exception:
                LOGGER.error(f"Error in toggle_research: {traceback.format_exc()}")
                return reply(1, None, "Failed to update research state")
        case "unlock_all_research":
            try:
                lab.unlock_all_research()
            except Exception:
                LOGGER.error(f"Error in unlock_all_research: {traceback.format_exc()}")
                return reply(1, None, "Failed to unlock research")
        case _:
            return reply(1, None, f"Unknown key {key}")
    return reply(0)
