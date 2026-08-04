from functools import wraps
import json
from typing import Any, Callable, Iterator, Optional

# from PIL import Image

from palworld_pal_editor.config import ASSETS_PATH, Config
from palworld_pal_editor.utils import LOGGER
from palworld_pal_editor.utils.util import alphanumeric_key


def load_json(filename: str) -> Any:
    path = ASSETS_PATH / "assets/data" / filename
    with path.open("r", encoding="utf8") as file:
        return json.load(file)


# def load_icons(sub_path: str) -> dict[str]:
#     icons = {}
#     valid_extensions = {".jpg", ".jpeg", ".png"}
#     path = BASE_PATH / "assets/icons" / sub_path
#     for img_path in path.iterdir():
#         if img_path.suffix.lower() in valid_extensions:
#             try:
#                 img = Image.open(img_path)
#                 icons[img_path.stem] = img
#             except IOError as e:
#                 LOGGER.error(f"Error opening {img_path}: {e}")
#     return icons


PAL_ATTACKS: dict[str, dict] = load_json("pal_attacks.json")
PAL_DATA: dict[str, dict] = load_json("pal_data.json") | load_json("human_data.json")
PAL_DATA_BY_CASEFOLD = {key.casefold(): key for key in PAL_DATA}
PALDECK_RECORD_ID_ALIASES = {
    "Blueplatypus": "BluePlatypus",
    "Werewolf_Ice": "WereWolf_Ice",
}
PAL_VARIANT_KIND_ORDER = {
    kind: index
    for index, kind in enumerate(
        (
            "base",
            "alpha",
            "boss",
            "predator",
            "quest",
            "tower",
            "raid",
            "boss-rush",
            "summon",
            "oilrig",
            "human",
            "other",
        )
    )
}


def _variant_sort_key(character_id: str) -> tuple[int, int, str]:
    record = PAL_DATA[character_id]
    return (
        0 if "base" in record.get("VariantTags", ()) else 1,
        PAL_VARIANT_KIND_ORDER.get(record.get("VariantKind"), 999),
        character_id,
    )


_pal_variants_by_family: dict[str, list[str]] = {}
for _character_id, _record in PAL_DATA.items():
    _pal_variants_by_family.setdefault(_record["FamilyID"], []).append(_character_id)
PAL_VARIANTS_BY_FAMILY: dict[str, tuple[str, ...]] = {
    family_id: tuple(sorted(variants, key=_variant_sort_key))
    for family_id, variants in _pal_variants_by_family.items()
}
PAL_PASSIVES: dict[str, dict] = load_json("pal_passives.json")
PAL_EXP_TABLE: list[int] = load_json("pal_exp_table.json")
PAL_FRIENDSHIP: dict[str, dict] = load_json("pal_friendship.json")
PLAYER_STATUS_DATA: dict[str, dict] = load_json("player_status_data.json")
TECH_DATA: dict[str, dict] = load_json("tech_data.json")
SKIN_DATA: dict[str, dict] = load_json("skin_data.json")
RESEARCH_DATA: dict[str, dict] = load_json("research_data.json")
# parent research id -> list of direct child research ids, built once from
# RESEARCH_DATA's RequireResearchId links (each research has at most one parent).
RESEARCH_CHILDREN: dict[str, list[str]] = {}
for _research_key, _research_entry in RESEARCH_DATA.items():
    _parent_id = _research_entry.get("RequireResearchId")
    if _parent_id:
        RESEARCH_CHILDREN.setdefault(_parent_id, []).append(_research_key)

# Localized labels used to compose a research effect description. Lab research has no
# localized description text in the source data, so the description is synthesized from
# the effect fields, mirroring palworld-save-pal's approach.
RESEARCH_EFFECT_LABELS: dict[str, dict[str, str]] = {
    "ItemCorruptionSpeedRate": {"en": "Spoilage Rate", "zh-CN": "腐坏速度", "ja": "腐敗速度", "fr": "Vitesse de péremption"},
    "CraftSpeed": {"en": "Work Speed", "zh-CN": "制作速度", "ja": "作業速度", "fr": "Vitesse de travail"},
    "PalEggHatchingSpeed": {"en": "Egg Hatching Speed", "zh-CN": "孵蛋速度", "ja": "孵化速度", "fr": "Vitesse d'éclosion"},
    "LabResearchSpeed": {"en": "Research Speed", "zh-CN": "研究速度", "ja": "研究速度", "fr": "Vitesse de recherche"},
    "DefenseRateBaseCampWorker": {"en": "Base Pal Defense", "zh-CN": "基地帕鲁防御", "ja": "拠点パル防御", "fr": "Défense des Pals de base"},
    "AttackRateBaseCampWorker": {"en": "Base Pal Attack", "zh-CN": "基地帕鲁攻击", "ja": "拠点パル攻撃", "fr": "Attaque des Pals de base"},
    "ExpeditionTimeCostRate": {"en": "Expedition Time", "zh-CN": "探险耗时", "ja": "遠征時間", "fr": "Durée d'expédition"},
    "ExpeditionRewardRate": {"en": "Expedition Rewards", "zh-CN": "探险奖励", "ja": "遠征報酬", "fr": "Récompenses d'expédition"},
    "ProductExtraItemProbability": {"en": "Bonus Output Chance", "zh-CN": "额外产出概率", "ja": "追加生産確率", "fr": "Chance de production bonus"},
    "EnergyStorageRate": {"en": "Energy Storage", "zh-CN": "电力储存", "ja": "電力貯蔵量", "fr": "Stockage d'énergie"},
    "ConsumeEnergyRate": {"en": "Energy Consumption", "zh-CN": "电力消耗", "ja": "電力消費", "fr": "Consommation d'énergie"},
    "ProductItemConsumeMaterialNumRate": {"en": "Material Consumption", "zh-CN": "材料消耗", "ja": "材料消費", "fr": "Consommation de matériaux"},
    "OilExtractionSpeedRate": {"en": "Oil Extraction Speed", "zh-CN": "石油开采速度", "ja": "石油採掘速度", "fr": "Vitesse d'extraction de pétrole"},
    "FarmCropGrowupSpeed": {"en": "Crop Growth Speed", "zh-CN": "作物生长速度", "ja": "作物成長速度", "fr": "Vitesse de croissance des cultures"},
    "FarmCropHarvestNumRate": {"en": "Crop Yield", "zh-CN": "作物产量", "ja": "作物収穫量", "fr": "Rendement des cultures"},
}
# EffectType "no" marks a facility-development research with no numeric buff.
RESEARCH_DEVELOPMENT_LABEL: dict[str, str] = {"en": "Facility Development", "zh-CN": "设施开发", "ja": "施設開発", "fr": "Développement d'installation"}
# Work-suitability labels double as the category labels (categories == suitability keys).
RESEARCH_SUITABILITY_LABELS: dict[str, dict[str, str]] = {
    "Cool": {"en": "Cooling", "zh-CN": "冷却", "ja": "冷却", "fr": "Refroidissement"},
    "Deforest": {"en": "Lumbering", "zh-CN": "砍伐", "ja": "伐採", "fr": "Bûcheronnage"},
    "EmitFlame": {"en": "Kindling", "zh-CN": "点火", "ja": "着火", "fr": "Embrasement"},
    "GenerateElectricity": {"en": "Generating Electricity", "zh-CN": "发电", "ja": "発電", "fr": "Production d'électricité"},
    "Handcraft": {"en": "Handiwork", "zh-CN": "手工", "ja": "手作業", "fr": "Artisanat"},
    "ProductMedicine": {"en": "Medicine Production", "zh-CN": "制药", "ja": "薬品製造", "fr": "Production de médicaments"},
    "Mining": {"en": "Mining", "zh-CN": "采矿", "ja": "採掘", "fr": "Extraction minière"},
    "Seeding": {"en": "Planting", "zh-CN": "播种", "ja": "種まき", "fr": "Plantation"},
    "Watering": {"en": "Watering", "zh-CN": "浇水", "ja": "水やり", "fr": "Arrosage"},
}
RESEARCH_ITEM_TYPE_LABELS: dict[str, dict[str, str]] = {
    "Dish": {"en": "Dishes", "zh-CN": "料理", "ja": "料理", "fr": "Plats"},
    "Ingot": {"en": "Ingots", "zh-CN": "金属锭", "ja": "インゴット", "fr": "Lingots"},
    "ArmorBody": {"en": "Armor", "zh-CN": "护甲", "ja": "防具", "fr": "Armures"},
    "PalGear": {"en": "Pal Gear", "zh-CN": "帕鲁用具", "ja": "パル装備", "fr": "Équipement Pal"},
    "Weapon": {"en": "Weapons", "zh-CN": "武器", "ja": "武器", "fr": "Armes"},
    "CaptureBall": {"en": "Pal Spheres", "zh-CN": "帕鲁球", "ja": "パルスフィア", "fr": "Sphères Pal"},
    "Bullet": {"en": "Ammo", "zh-CN": "弹药", "ja": "弾薬", "fr": "Munitions"},
    "Medicine": {"en": "Medicine", "zh-CN": "药品", "ja": "薬品", "fr": "Médicaments"},
    "Ore": {"en": "Ore", "zh-CN": "矿石", "ja": "鉱石", "fr": "Minerai"},
}


def _localize_label(table: dict[str, dict[str, str]], key: Optional[str]) -> Optional[str]:
    entry = table.get(key or "")
    if not entry:
        return None
    return entry.get(Config.i18n) or entry.get("en")


def _format_effect_value(value) -> Optional[str]:
    if not isinstance(value, (int, float)) or value == 0:
        return None
    number = int(value) if float(value).is_integer() else value
    sign = "+" if number > 0 else ""
    return f"{sign}{number}%"

# PAL_ICONS: dict[str] = load_icons("pals")

# I18N_LIST = ["en", "zh-CN", "ja"]
I18N_LIST: dict[str, str] = load_json("i18n_list.json")


def none_guard(
    data_source: dict | list, key_arg_position: int = 0, subkey: Optional[str] = None
):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[Any]:
            # Extract key from positional or keyword arguments
            key = (
                args[key_arg_position]
                if len(args) > key_arg_position
                else kwargs.get("key")
            )

            # if key not in data_source, or if subkey not in data source, or sub_data[subkey] is empty
            if key not in data_source or (
                subkey
                and (subkey not in data_source[key] or not data_source[key][subkey])
            ):
                # LOGGER.warning(
                #     f"Key: {key} or subkey: {subkey} were not found in the data source."
                # )
                return None

            return func(*args, **kwargs)

        return wrapper

    return decorator


class DataProvider:
    icon_cache = {}

    @staticmethod
    def default_i18n() -> str:
        return "en"

    @staticmethod
    def get_player_status_data() -> dict[str, dict]:
        return PLAYER_STATUS_DATA

    def get_i18n_map() -> dict[str, str]:
        return I18N_LIST

    # @staticmethod
    # def get_pal_icon(key: str) -> Optional[Any]:
    #     if key not in PAL_ICONS:
    #         LOGGER.warning(f"Pal icon {key} doesn't exist.")
    #         return
    #     return PAL_ICONS[key]
    @staticmethod
    def in_pal_data(key: str) -> bool:
        """
        Checks if the key exists in the PAL_DATA dictionary.
        """
        return key in PAL_DATA

    @staticmethod
    def resolve_pal_key(key: Optional[str]) -> Optional[str]:
        if not key or key in PAL_DATA:
            return key
        return PAL_DATA_BY_CASEFOLD.get(key.casefold(), key)

    @staticmethod
    def get_pal_record(key: Optional[str]) -> Optional[dict]:
        return PAL_DATA.get(DataProvider.resolve_pal_key(key))

    @staticmethod
    def get_pal_family_id(character_id: str) -> str:
        record = DataProvider.get_pal_record(character_id)
        return record["FamilyID"] if record else character_id

    @staticmethod
    def get_pal_variant_kind(character_id: str) -> str:
        record = DataProvider.get_pal_record(character_id)
        return record.get("VariantKind", "other") if record else "other"

    @staticmethod
    def get_pal_variant_tags(character_id: str) -> tuple[str, ...]:
        record = DataProvider.get_pal_record(character_id)
        return tuple(record.get("VariantTags", ())) if record else ()

    @staticmethod
    def get_pal_icon_key(character_id: str) -> str:
        record = DataProvider.get_pal_record(character_id)
        return record.get("IconKey", "unknown") if record else "unknown"

    @staticmethod
    def get_pal_paldeck_record_id(character_id: str) -> Optional[str]:
        record = DataProvider.get_pal_record(character_id)
        if not record or record.get("Human", False):
            return None
        record_id = record.get("PaldeckRecordID") or record["FamilyID"]
        return PALDECK_RECORD_ID_ALIASES.get(record_id, record_id)

    @staticmethod
    def get_family_variants(
        character_id: str, kind: Optional[str] = None
    ) -> tuple[str, ...]:
        record = DataProvider.get_pal_record(character_id)
        if not record:
            return (character_id,) if kind is None else ()
        variants = PAL_VARIANTS_BY_FAMILY[record["FamilyID"]]
        if kind is None:
            return variants
        return tuple(
            variant
            for variant in variants
            if PAL_DATA[variant].get("VariantKind") == kind
        )

    @staticmethod
    def get_pal_variant(character_id: str, kind: str) -> Optional[str]:
        variants = DataProvider.get_family_variants(character_id, kind)
        return variants[0] if len(variants) == 1 else None

    @none_guard(data_source=PAL_DATA, subkey="I18n")
    @staticmethod
    def get_pal_i18n(key: str) -> Optional[str]:
        tags = set(PAL_DATA[key].get("VariantTags", ()))
        if tags and tags.issubset({"alpha", "boss"}):
            key = DataProvider.get_pal_variant(key, "base") or key
        i18n_list: dict = PAL_DATA[key]["I18n"]
        return i18n_list.get(Config.i18n, i18n_list.get("en"))

    @none_guard(data_source=PAL_DATA, subkey="Stats")
    @staticmethod
    def get_pal_stats(pal: str, scaling_type: str) -> Optional[int]:
        scaling_list: dict = PAL_DATA[pal]["Stats"]
        return scaling_list.get(scaling_type, None)

    @none_guard(data_source=PAL_DATA, subkey="Parameters")
    @staticmethod
    def get_pal_parameter(pal: str, parameter: str) -> Optional[float]:
        return PAL_DATA[pal]["Parameters"].get(parameter)

    @none_guard(data_source=PAL_DATA, subkey="SortingKey")
    @staticmethod
    def get_pal_sorting_key(key: str, sorting_key="paldeck") -> Optional[str]:
        sorting_key_list: dict = PAL_DATA[key]["SortingKey"]
        return sorting_key_list.get(sorting_key)

    @staticmethod
    def get_sorted_pals() -> list[dict]:
        sorted_list = sorted(
            PAL_DATA.values(),
            key=lambda item: (
                DataProvider.is_pal_human(item["InternalName"]),
                alphanumeric_key(
                    DataProvider.get_pal_sorting_key(item["InternalName"])
                    or DataProvider.get_pal_i18n(item["InternalName"])
                ),
                len(item["InternalName"]),
            ),
        )
        return sorted_list

    @staticmethod
    def is_pal_human(key: str) -> Optional[bool]:
        record = DataProvider.get_pal_record(key)
        return record.get("Human", False) if record else None

    @staticmethod
    def has_human_icon(key: str) -> bool:
        record = DataProvider.get_pal_record(key)
        return record.get("HasIcon", False) if record else False

    @staticmethod
    def get_skin_data() -> dict[str, dict]:
        return SKIN_DATA

    @staticmethod
    def get_skin(key: str) -> Optional[dict]:
        return SKIN_DATA.get(key)

    @staticmethod
    def get_skins_for_pal(key: str) -> list[dict]:
        return [
            skin
            for skin in SKIN_DATA.values()
            if skin.get("TargetPalName") == key
        ]

    @staticmethod
    def is_pal_invalid(key: str) -> bool:
        if key not in PAL_DATA:
            return True
        return PAL_DATA[key].get("Invalid", False)

    @none_guard(data_source=PAL_DATA, subkey="Attacks")
    def get_pal_attacks(pal: str) -> Optional[list[str]]:
        return PAL_DATA[pal]["Attacks"]

    @none_guard(data_source=PAL_DATA, subkey="Suitabilities")
    def get_pal_suitabilities(pal: str) -> Optional[dict[str, int]]:
        return PAL_DATA[pal]["Suitabilities"]

    @none_guard(data_source=PAL_DATA, subkey="BestWorkSuitability")
    def get_pal_best_work_suitability(pal: str) -> Optional[str]:
        return PAL_DATA[pal]["BestWorkSuitability"]

    @staticmethod
    def get_pal_level_xp(lv: int) -> Optional[int]:
        try:
            return PAL_EXP_TABLE[str(lv)]["PalTotalEXP"]
        except Exception:
            LOGGER.warning(f"Level {lv} is out of bounds.")
            return None

    @staticmethod
    def get_pal_exp_table_max_level() -> int:
        return max(int(level) for level in PAL_EXP_TABLE)

    @staticmethod
    def get_pal_exp_level(exp: int) -> Optional[int]:
        levels = sorted(int(level) for level in PAL_EXP_TABLE)
        for index, level in enumerate(levels):
            total = PAL_EXP_TABLE[str(level)]["PalTotalEXP"]
            if index == len(levels) - 1:
                return level if exp >= total else None
            next_total = PAL_EXP_TABLE[str(levels[index + 1])]["PalTotalEXP"]
            if total <= exp < next_total:
                return level
        return None

    @staticmethod
    def get_pal_friendship(lv: str) -> Optional[int]:
        try:
            return PAL_FRIENDSHIP[str(lv)]["required_point"]
        except Exception:
            LOGGER.warning(f"Friendship level {lv} is out of bounds.")
            return None
        
    @staticmethod
    def get_pal_friendship_level_from_pts(pts: int) -> Optional[int]:
        max_lv = -3
        for level, data in PAL_FRIENDSHIP.items():
            if pts >= data["required_point"]:
                max_lv = max(max_lv, int(level))
        return max_lv

    @none_guard(data_source=PAL_ATTACKS, subkey="I18n")
    @staticmethod
    def get_attack_i18n(key: str) -> Optional[tuple[str, str]]:
        i18n_list: dict = PAL_ATTACKS[key]["I18n"]
        english: dict = i18n_list.get("en", {})
        i18n: dict = i18n_list.get(Config.i18n, {})
        return (
            i18n.get("Name") or english.get("Name") or key,
            i18n.get("Description") or english.get("Description", ""),
        )

    @staticmethod
    def get_attack_learner_names(key: str) -> list[str]:
        names = []
        seen = set()
        for learner in PAL_ATTACKS.get(key, {}).get("Learners", ()):
            family = DataProvider.get_pal_family_id(learner.get("CharacterID", ""))
            if not family or family.casefold() in seen:
                continue
            seen.add(family.casefold())
            names.append(DataProvider.get_pal_i18n(family) or family)
        return names

    @staticmethod
    def has_attack(key: str) -> bool:
        return key in PAL_ATTACKS

    @staticmethod
    def has_skill_fruit(attack: str) -> bool:
        if attack not in PAL_ATTACKS:
            return False
        if PAL_ATTACKS[attack].get("SkillFruit"):
            return True
        return False

    @staticmethod
    def is_invalid_attack(key: str) -> bool:
        if key not in PAL_ATTACKS:
            return True
        return PAL_ATTACKS[key].get("Invalid", False)

    @staticmethod
    def is_unique_attacks(key: str) -> bool:
        if key not in PAL_ATTACKS:
            return False
        return PAL_ATTACKS[key].get("UniqueSkill", False)

    @staticmethod
    def is_non_inheritable_attack(key: str) -> bool:
        return PAL_ATTACKS.get(key, {}).get("NonInheritable", False)

    @staticmethod
    def is_exclusive_attack(key: str) -> bool:
        return PAL_ATTACKS.get(key, {}).get("Exclusive", False)

    @staticmethod
    def is_boss_attack(key: str) -> bool:
        return PAL_ATTACKS.get(key, {}).get("BossSkill", False)

    @staticmethod
    def is_assignable_attack(key: str) -> bool:
        return PAL_ATTACKS.get(key, {}).get("Assignable", False)

    @staticmethod
    def is_assignable_human_attack(key: str) -> bool:
        return PAL_ATTACKS.get(key, {}).get("AssignableToHumans", False)

    @staticmethod
    def get_sorted_attacks() -> list[dict]:
        sorted_list = sorted(
            PAL_ATTACKS.values(),
            key=lambda item: (
                DataProvider.is_invalid_attack(item["InternalName"]),
                item["Element"],
                DataProvider.is_unique_attacks(item["InternalName"]),
                # DataProvider.has_skill_fruit(item["InternalName"]),
                item["Power"],
                item["CT"],
            ),
        )
        return sorted_list

    @none_guard(data_source=PAL_PASSIVES, subkey="I18n")
    @staticmethod
    def get_passive_i18n(key: str) -> Optional[tuple[str, str]]:
        i18n_list: dict = PAL_PASSIVES[key]["I18n"]
        english: dict = i18n_list.get("en", {})
        i18n: dict = i18n_list.get(Config.i18n, {})
        return (
            i18n.get("Name") or english.get("Name") or key,
            i18n.get("Description") or english.get("Description", ""),
        )

    @staticmethod
    def has_passive_skill(key: str) -> bool:
        return key in PAL_PASSIVES

    @staticmethod
    def get_sorted_passives() -> list[dict]:
        sorted_list = sorted(
            PAL_PASSIVES.values(),
            key=lambda item: (
                -item["Rating"],
                DataProvider.get_passive_i18n(item["InternalName"]),
            ),
        )
        return sorted_list

    @staticmethod
    def get_passive_buff(key: str, buff_key: str) -> float:
        return PAL_PASSIVES.get(key, {}).get("Buff", {}).get(buff_key, 0)

    @staticmethod
    def get_attacks_to_learn(pal: str, level: int) -> list[str]:
        attacks = DataProvider.get_pal_attacks(pal)
        if attacks is None:
            return []
        return [attack for attack in attacks if attacks[attack] <= (level or 1)]

    @staticmethod
    def get_attacks_to_forget(pal: str, level: int) -> list[str]:
        attacks = DataProvider.get_pal_attacks(pal)
        if attacks is None:
            return []
        return [
            attack
            for attack in attacks
            if attacks[attack] > level and not DataProvider.has_skill_fruit(attack)
        ]

    @staticmethod
    def is_valid_i18n(key: str):
        return key in I18N_LIST

    @staticmethod
    def get_i18n_options() -> list[str]:
        return I18N_LIST.keys()

    @staticmethod
    def get_player_level_xp(lv: int) -> Optional[int]:
        try:
            return PAL_EXP_TABLE[str(lv)]["TotalEXP"]
        except IndexError:
            LOGGER.warning(f"Level {lv} is out of bounds.")
            return None

    @staticmethod
    def get_tech_data() -> dict[str, dict]:
        return TECH_DATA

    @staticmethod
    def get_tech_i18n(key: str) -> dict | str | None:
        record = TECH_DATA.get(key)
        if record is None:
            return None
        i18n_list: dict = record.get("I18n", {})
        return (
            i18n_list.get(Config.i18n)
            or i18n_list.get("en")
            or i18n_list.get("ja")
            or key
        )

    @staticmethod
    def get_tech_lv(key: str) -> int:
        return TECH_DATA.get(key, {}).get("Level", 0)

    @staticmethod
    def is_boss_tech(key: str) -> bool:
        return TECH_DATA.get(key, {}).get("BossTechnology", False)

    @staticmethod
    def get_research_data() -> dict[str, dict]:
        return RESEARCH_DATA

    @staticmethod
    def is_research_displayable(key: str) -> bool:
        return key in RESEARCH_DATA

    @staticmethod
    def iter_displayable_research() -> Iterator[tuple[str, dict]]:
        for key, data in RESEARCH_DATA.items():
            yield key, data

    @staticmethod
    def get_research_i18n(key: str) -> Optional[str]:
        if key not in RESEARCH_DATA:
            return None
        i18n_list: dict = RESEARCH_DATA[key]["I18n"]
        localized = i18n_list.get(Config.i18n, i18n_list.get("en"))
        return localized.get("Name") if localized else None

    @staticmethod
    def get_research_category(key: str) -> Optional[str]:
        return RESEARCH_DATA.get(key, {}).get("Category")

    @staticmethod
    def get_research_category_label(category: Optional[str]) -> Optional[str]:
        return _localize_label(RESEARCH_SUITABILITY_LABELS, category) or category

    @staticmethod
    def get_research_description(key: str) -> Optional[str]:
        """Compose a localized, effect-only description from the research effect fields."""
        data = RESEARCH_DATA.get(key)
        if not data:
            return None
        effect_type = data.get("EffectType")
        if not effect_type or effect_type == "no":
            return RESEARCH_DEVELOPMENT_LABEL.get(Config.i18n) or RESEARCH_DEVELOPMENT_LABEL["en"]

        label = _localize_label(RESEARCH_EFFECT_LABELS, effect_type) or effect_type
        parts = [label]
        if value := _format_effect_value(data.get("EffectValue")):
            parts.append(value)
        context = _localize_label(
            RESEARCH_SUITABILITY_LABELS, data.get("EffectWorkSuitability")
        ) or _localize_label(RESEARCH_ITEM_TYPE_LABELS, data.get("EffectItemType"))
        if context:
            parts.append(f"({context})")
        return " ".join(parts)

    @staticmethod
    def is_essential_research(key: str) -> bool:
        return bool(RESEARCH_DATA.get(key, {}).get("IsEssential", False))

    @staticmethod
    def get_research_work_amount(key: str) -> int:
        return RESEARCH_DATA.get(key, {}).get("WorkAmount", 0)

    @staticmethod
    def get_research_ancestors(key: str) -> list[str]:
        """Returns ids up the RequireResearchId chain, ordered root..parent (excludes key)."""
        ancestors: list[str] = []
        seen: set[str] = {key}
        current = RESEARCH_DATA.get(key, {}).get("RequireResearchId")
        while current and current not in seen:
            ancestors.append(current)
            seen.add(current)
            current = RESEARCH_DATA.get(current, {}).get("RequireResearchId")
        ancestors.reverse()
        return ancestors

    @staticmethod
    def get_research_descendants(key: str) -> list[str]:
        """Returns all transitive children via the reverse adjacency map (excludes key)."""
        descendants: list[str] = []
        seen: set[str] = {key}
        stack = list(RESEARCH_CHILDREN.get(key, []))
        while stack:
            child = stack.pop()
            if child in seen:
                continue
            seen.add(child)
            descendants.append(child)
            stack.extend(RESEARCH_CHILDREN.get(child, []))
        return descendants
