import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("../src/components/PalEditor.vue", import.meta.url), "utf8");

test("Pal progression and skill editors use the compact shared layout", () => {
  for (const className of [
    "pal-editor", "pal-progression-grid", "pal-panel", "range-grid",
    "suitability-grid", "skill-section", "skill-cards",
  ]) assert.match(source, new RegExp(`class="[^"]*${className}`), className);

  assert.match(source, /grid-template-columns:\s*repeat\(auto-fit,\s*minmax\(14rem,\s*1fr\)\)/);
  assert.match(source, /@container\s+pal-editor\s*\(max-width:\s*42rem\)/);
  assert.doesNotMatch(source, /EditorItem|editField|skillPanel|flex-v|@mouseup|@touchend|--sub-height|--editor-panel-width/);
  assert.match(source, /\/image\/ui\/soul/);
});

test("range controls preserve limits and update from keyboard-friendly change events", () => {
  for (const field of [
    "Talent_HP", "Talent_Defense", "Talent_Shot", "Talent_Melee",
    "Rank_HP", "Rank_Attack", "Rank_Defence", "Rank_CraftSpeed", "Rank",
  ]) {
    assert.match(source, new RegExp(`name="${field}"[\\s\\S]*?@change="updateRange\\('${field}', \\$event\\)"`), field);
  }
  assert.doesNotMatch(source, /<input type="range"/);
  assert.match(source, /palStore\.HIDE_INVALID_OPTIONS \? 100 : 255/);
  assert.match(source, /palStore\.HIDE_INVALID_OPTIONS \? palStore\.MAX_SOULS_LEVEL : 255/);
  assert.match(source, /palStore\.HIDE_INVALID_OPTIONS \? 5 : 255/);
});

test("all Pal edit contracts and validity rules remain available", () => {
  for (const handler of [
    "toggleAwakening", "suitDown", "suitUp", "pop_PassiveSkillList",
    "add_PassiveSkillList", "pop_EquipWaza", "add_EquipWaza",
    "pop_MasteredWaza", "add_MasteredWaza",
  ]) assert.match(source, new RegExp(handler), handler);

  assert.match(source, /key != 'EPalWorkSuitability::OilExtraction'/);
  assert.match(source, /canAssignActiveSkill/);
  assert.match(source, /elementIconKey/);
  assert.match(source, /skillBadgeLabels/);
  assert.match(source, /canToggleBossVariant/);
});

test("IV panel exposes bounded randomization controls", () => {
  assert.match(source, /name="ivRandomMinimum"[\s\S]*?type="number"[\s\S]*?min="1"[\s\S]*?max="100"/);
  assert.match(source, /name="randomize_ivs"/);
  assert.match(source, /palStore\.randomizePalIVs\(minimum\)/);
});

test("Pal editor exposes the save-backed favorite toggle", () => {
  assert.match(source, /name="IsFavoritePal"/);
  assert.match(source, /palStore\.SELECTED_PAL_DATA\.swapFavorite/);
  assert.match(source, /Editor_Favorite/);
});
