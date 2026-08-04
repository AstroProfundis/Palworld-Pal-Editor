import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const modal = await readFile(new URL("../src/components/GuildResearchModal.vue", import.meta.url), "utf8");
const app = await readFile(new URL("../src/App.vue", import.meta.url), "utf8");
const topbar = await readFile(new URL("../src/components/TopBar.vue", import.meta.url), "utf8");
const store = await readFile(new URL("../src/stores/paleditor.js", import.meta.url), "utf8");
const en = await readFile(new URL("../src/i18n/en.js", import.meta.url), "utf8");

test("guild research modal is accessible and guild-scoped", () => {
  assert.match(modal, /role="dialog"/);
  assert.match(modal, /aria-modal="true"/);
  assert.match(modal, /v-model="palStore\.SELECTED_RESEARCH_GUILD_ID"/);
  assert.match(modal, /GUILD_RESEARCH_NO_LAB/);
  assert.match(modal, /GUILD_RESEARCH_LOADING/);
  assert.match(modal, /palStore\.toggleGuildResearch/);
  assert.match(modal, /palStore\.unlockAllGuildResearch/);
  assert.match(modal, /@keydown\.tab="trapFocus"/);
});

test("research state is loaded through authenticated store operations", () => {
  assert.match(store, /GET\("\/api\/save\/research_data"\)/);
  assert.match(store, /GET\("\/api\/guild\/list"\)/);
  assert.match(store, /POST\("\/api\/guild\/research"/);
  assert.match(store, /PATCH\("\/api\/guild\/research"/);
  assert.match(store, /SHOW_RESEARCH_FLAG/);
  assert.match(store, /GUILD_RESEARCH_LOADING/);
});

test("research modal is mounted globally and opened from the loaded-save toolbar", () => {
  assert.match(app, /GuildResearchModal/);
  assert.match(app, /palStore\.SHOW_RESEARCH_FLAG/);
  assert.match(topbar, /openGuildResearch/);
  assert.match(en, /GuildResearch_Title:/);
  assert.match(en, /Operation_Load_Guild_Research:/);
});
