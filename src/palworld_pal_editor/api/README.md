# WebUI API

The WebUI API is an authenticated interface for the loaded save. All endpoints below require a valid JWT bearer token.

Responses use the following envelope:

```json
{
  "status": 0,
  "data": {},
  "msg": null
}
```

`status` `0` indicates success, `1` indicates a business or validation error, and `2` indicates that authentication is required.

## Base And Worker APIs

### `GET /api/player/players_data`

Returns `players`, `bases`, `hasWorkingPal`, and `hasUnassignedWorkingPal`.

Each base contains `Id`, `Name`, `GuildId`, `GuildName`, `BaseCampLevel`, `WorkerCount`, `WorldTranslation`, `MapCoordinates`, and `ContainerId`. A base remains in the response when it has no workers or its guild metadata is unavailable.

### `POST /api/player/player_pals`

Accepts exactly one of these selectors:

```json
{"PlayerUId": "player-uuid"}
```

```json
{"BaseCampId": "base-uuid"}
```

```json
{"UnassignedBaseWorkers": true}
```

`PlayerUId` set to `PAL_BASE_WORKER_BTN` remains a compatibility path that returns all recognized working Pals. An unknown `BaseCampId` returns a business error, while a known empty base returns an empty list.

## Guild Research APIs

### `GET /api/save/research_data`

Returns `researchCategories`. Each category contains `key`, `label`, `icon`, and ordered research items. Each item contains `InternalName`, `RequireResearchId`, `WorkAmount`, `IsEssential`, `Name`, and `Description`.

### `GET /api/guild/list`

Returns guilds with `GuildId`, `GuildName`, and `HasLab`.

### `POST /api/guild/research`

Accepts `GuildId` and returns `completed_research_ids`, `current_research_id`, and `work_amounts` for that guild.

### `PATCH /api/guild/research`

Accepts `GuildId`, `key`, and `value`.

The `toggle_research` operation uses this value:

```json
{
  "research": "ResearchInternalName",
  "status": true
}
```

Enabling an item also completes its ancestors. Disabling an item resets it and all descendants. The `unlock_all_research` operation completes every displayable catalog item and clears the current research target.

Research completion is represented by `work_amount` reaching the catalog `WorkAmount`; cancellation resets `work_amount` to `0`. When an operation completes or cancels the active research, `current_research_id` is reset to the game's `None` sentinel.

Requests for a guild without decoded Lab data return a business error. The API does not create missing Lab data.
