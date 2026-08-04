<script setup>
import { usePalEditorStore } from '@/stores/paleditor'

const palStore = usePalEditorStore()
const props = defineProps({ preview: Boolean })
const emit = defineEmits(['toggle'])
const toggleLabel = () => palStore.getTranslatedText(props.preview ? 'PlayerList_Restore' : 'PlayerList_Collapse')
const playerLabel = player => player.NickName || palStore.getTranslatedText('PlayerList_Unknown')
const playerInitial = player => playerLabel(player).trim().charAt(0).toUpperCase() || '?'
const baseLabel = (base, index) => base.Name
  || palStore.getTranslatedText('PlayerList_Base_Unnamed', [index + 1])
</script>

<template>
  <nav class="player-roster" :aria-label="palStore.getTranslatedText('PlayerList_Text')">
    <header class="roster-header">
      <button class="roster-title-button" :title="toggleLabel()"
        :aria-label="toggleLabel()" @click="emit('toggle')">
        {{ palStore.getTranslatedText("PlayerList_Text") }}
      </button>
    </header>

    <div class="roster-list">
      <button v-for="(base, index) in [...palStore.BASES.values()]" :key="base.Id"
        class="roster-row roster-row--base" @click="palStore.selectBase(base.Id)" :title="base.Id"
        :aria-current="base.Id == palStore.SELECTED_BASE_ID ? 'true' : undefined"
        :disabled="(base.Id == palStore.SELECTED_BASE_ID && !palStore.SELECTED_PAL_ID) || palStore.LOADING_FLAG">
        <span class="player-avatar">BASE</span>
        <span class="roster-copy">
          <strong>{{ baseLabel(base, index) }}</strong>
          <small v-if="base.GuildName">{{ base.GuildName }}</small>
        </span>
      </button>

      <button v-if="palStore.HAS_UNASSIGNED_WORKING_PAL" class="roster-row roster-row--base"
        @click="palStore.selectUnassignedWorkers()"
        :aria-current="palStore.BASE_PAL_BTN_CLK_FLAG && !palStore.SELECTED_BASE_ID ? 'true' : undefined"
        :disabled="(palStore.BASE_PAL_BTN_CLK_FLAG && !palStore.SELECTED_BASE_ID && !palStore.SELECTED_PAL_ID) || palStore.LOADING_FLAG">
        <span class="player-avatar">PAL</span>
        <span class="roster-copy">{{ palStore.getTranslatedText(palStore.LEGACY_BASE_WORKER_MODE
          ? 'PlayerList_Base_Pal' : 'PlayerList_Base_Unassigned') }}</span>
      </button>

      <button v-for="player in palStore.PLAYER_MAP.values()" :key="player.InstanceId"
        class="roster-row" @click="palStore.selectPlayer(player.InstanceId)" :title="player.InstanceId"
        :aria-current="player.InstanceId == palStore.SELECTED_PLAYER_ID ? 'true' : undefined"
        :disabled="(player.InstanceId == palStore.SELECTED_PLAYER_ID && palStore.SHOW_PLAYER_EDIT_FLAG) || palStore.LOADING_FLAG">
        <span class="player-avatar">{{ playerInitial(player) }}</span>
        <span class="roster-copy">{{ player.NickName || palStore.getTranslatedText('PlayerList_Unknown') }}</span>
      </button>
    </div>
  </nav>
</template>

<style scoped>
.player-roster {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  height: 100%;
  min-height: 0;
}

.roster-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--editor-space-2);
  padding: var(--editor-space-3);
  border-bottom: 1px solid var(--editor-color-border);
}

.roster-title-button {
  margin: 0;
  padding: 0;
  border: 0;
  color: var(--editor-color-muted);
  background: transparent;
  font-size: .8rem;
  letter-spacing: .04em;
  text-transform: uppercase;
  cursor: pointer;
}

.roster-list {
  display: grid;
  min-height: 0;
  align-content: start;
  gap: var(--editor-space-1);
  overflow-y: auto;
  padding: var(--editor-space-2);
}

.roster-row {
  display: grid;
  grid-template-columns: 2rem minmax(0, 1fr);
  align-items: center;
  gap: var(--editor-space-2);
  min-height: 2.75rem;
  padding: var(--editor-space-1) var(--editor-space-2);
  border: 1px solid transparent;
  border-radius: var(--editor-radius-sm);
  color: var(--editor-color-text);
  background: var(--editor-color-surface-raised);
  text-align: left;
  cursor: pointer;
}

.roster-row:hover {
  background: var(--editor-color-control-hover);
}

.roster-row[aria-current="true"] {
  border-color: var(--editor-color-focus);
  color: var(--editor-color-text);
  background: var(--editor-color-surface-raised);
  box-shadow: inset .2rem 0 var(--editor-color-focus), 0 0 .7rem color-mix(in srgb, var(--editor-color-focus) 25%, transparent);
}

.roster-row:disabled {
  cursor: default;
}

.roster-copy {
  display: grid;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.roster-copy small {
  color: var(--editor-color-muted);
  overflow: hidden;
  text-overflow: ellipsis;
}

.player-avatar {
  display: grid;
  width: 2rem;
  height: 2rem;
  place-items: center;
  border-radius: 50%;
  color: var(--editor-color-background);
  background: var(--editor-color-primary);
  font-size: .7rem;
  font-weight: 700;
}

.roster-row--base .player-avatar {
  background: var(--editor-color-warning);
  font-size: .55rem;
}

.roster-row:focus-visible,
.roster-title-button:focus-visible {
  outline: 2px solid var(--editor-color-focus);
  outline-offset: 2px;
}

@media (max-width: 760px) {
  .roster-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 480px) {
  .roster-list {
    grid-template-columns: 1fr;
  }
}
</style>
