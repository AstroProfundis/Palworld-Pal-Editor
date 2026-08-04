<script setup>
import { computed } from 'vue'

import UiIcon from '@/components/modules/UiIcon.vue'
import { usePalEditorStore } from '@/stores/paleditor'

const palStore = usePalEditorStore()
const base = computed(() => palStore.SELECTED_BASE_ID
  ? palStore.BASES.get(palStore.SELECTED_BASE_ID)
  : null)
const isUnassigned = computed(() => palStore.BASE_PAL_BTN_CLK_FLAG && !palStore.SELECTED_BASE_ID)
const valueOrDash = value => value ?? '-'
const baseName = computed(() => isUnassigned.value
  ? palStore.getTranslatedText('PlayerList_Base_Unassigned')
  : base.value?.Name || palStore.getTranslatedText('PlayerList_Base_Unnamed'))
const workerCount = computed(() => base.value?.palsLoaded
  ? base.value.pals.size
  : isUnassigned.value
    ? palStore.PAL_MAP.size
    : base.value?.WorkerCount || 0)
const coordinates = computed(() => {
  const value = base.value?.MapCoordinates
  return value ? `${value.x}, ${value.y}` : '-'
})
</script>

<template>
  <section class="base-info editor-surface">
    <header class="base-info__header">
      <span class="base-info__icon"><UiIcon name="home" /></span>
      <div>
        <p class="base-info__eyebrow">{{ palStore.getTranslatedText('BaseInfo_Title') }}</p>
        <h1>{{ baseName }}</h1>
      </div>
    </header>

    <dl class="base-info__grid">
      <div>
        <dt>{{ palStore.getTranslatedText('BaseInfo_Name') }}</dt>
        <dd>{{ baseName }}</dd>
      </div>
      <div>
        <dt>{{ palStore.getTranslatedText('BaseInfo_Guild') }}</dt>
        <dd>{{ valueOrDash(base?.GuildName) }}</dd>
      </div>
      <div>
        <dt>{{ palStore.getTranslatedText('BaseInfo_Level') }}</dt>
        <dd>{{ valueOrDash(base?.BaseCampLevel) }}</dd>
      </div>
      <div>
        <dt>{{ palStore.getTranslatedText('BaseInfo_WorkerCount') }}</dt>
        <dd>{{ workerCount }}</dd>
      </div>
      <div>
        <dt>{{ palStore.getTranslatedText('BaseInfo_Coords') }}</dt>
        <dd>{{ coordinates }}</dd>
      </div>
    </dl>
  </section>
</template>

<style scoped>
.base-info {
  display: grid;
  gap: var(--editor-space-5);
  min-height: 100%;
  align-content: start;
  padding: clamp(var(--editor-space-4), 4vw, var(--editor-space-6));
}

.base-info__header {
  display: flex;
  align-items: center;
  gap: var(--editor-space-3);
}

.base-info__icon {
  display: grid;
  width: 3rem;
  height: 3rem;
  place-items: center;
  border-radius: var(--editor-radius-md);
  color: var(--editor-color-background);
  background: var(--editor-color-warning);
}

.base-info__eyebrow,
.base-info h1 {
  margin: 0;
}

.base-info__eyebrow,
.base-info dt {
  color: var(--editor-color-muted);
  font-size: .78rem;
  letter-spacing: .04em;
  text-transform: uppercase;
}

.base-info__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
  gap: var(--editor-space-3);
  margin: 0;
}

.base-info__grid > div {
  display: grid;
  gap: var(--editor-space-2);
  padding: var(--editor-space-4);
  border: 1px solid var(--editor-color-border);
  border-radius: var(--editor-radius-md);
  background: var(--editor-color-surface-raised);
}

.base-info dd {
  margin: 0;
  font-size: 1.05rem;
  overflow-wrap: anywhere;
}
</style>
