<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import ResearchNode from '@/components/modules/ResearchNode.vue'
import UiIcon from '@/components/modules/UiIcon.vue'
import { usePalEditorStore } from '@/stores/paleditor'
import { buildCompletedIdSet, buildResearchTree, findResearchNode } from '@/utils/researchTree'

const emit = defineEmits(['close'])
const palStore = usePalEditorStore()
const dialog = ref(null)
const selectedCategoryKey = ref('')
const selectedResearchId = ref('')
let previousFocus
let appContent
let previousAriaHidden

const selectedGuild = computed(() => palStore.GUILD_LIST.find(
  guild => guild.GuildId === palStore.SELECTED_RESEARCH_GUILD_ID,
))
const selectedCategory = computed(() => palStore.RESEARCH_CATEGORIES.find(
  category => category.key === selectedCategoryKey.value,
))
const researchTree = computed(() => buildResearchTree(selectedCategory.value?.items || []))
const completed = computed(() => buildCompletedIdSet(
  palStore.SELECTED_GUILD_RESEARCH.completed_research_ids,
))
const selectedResearch = computed(() => findResearchNode(researchTree.value, selectedResearchId.value))
const selectedCompleted = computed(() => selectedResearch.value
  ? completed.value.has(selectedResearch.value.InternalName)
  : false)
const completedCount = computed(() => palStore.SELECTED_GUILD_RESEARCH.completed_research_ids.length)
const totalCount = computed(() => palStore.RESEARCH_CATEGORIES.reduce(
  (total, category) => total + category.items.length,
  0,
))

watch(() => palStore.RESEARCH_CATEGORIES, categories => {
  if (!categories.some(category => category.key === selectedCategoryKey.value)) {
    selectedCategoryKey.value = categories[0]?.key || ''
  }
}, { immediate: true })

watch(selectedCategoryKey, () => {
  selectedResearchId.value = researchTree.value[0]?.InternalName || ''
})

async function selectGuild() {
  selectedResearchId.value = ''
  await palStore.fetchGuildResearch(palStore.SELECTED_RESEARCH_GUILD_ID)
}

async function toggleSelectedResearch() {
  if (!selectedResearch.value) return
  await palStore.toggleGuildResearch(
    selectedResearch.value.InternalName,
    !selectedCompleted.value,
  )
}

async function unlockAll() {
  if (!window.confirm(palStore.getTranslatedText('GuildResearch_Unlock_All_Confirm'))) return
  await palStore.unlockAllGuildResearch()
}

function close() {
  palStore.SHOW_RESEARCH_FLAG = false
  emit('close')
}

function trapFocus(event) {
  const controls = [...dialog.value.querySelectorAll(
    'button:not(:disabled), select:not(:disabled), [href], [tabindex]:not([tabindex="-1"])'
  )].filter(control => control.offsetParent !== null)
  if (!controls.length) return event.preventDefault()
  const first = controls[0]
  const last = controls.at(-1)
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

onMounted(async () => {
  previousFocus = document.activeElement
  appContent = document.querySelector('.app-content')
  previousAriaHidden = appContent?.getAttribute('aria-hidden')
  appContent?.setAttribute('aria-hidden', 'true')
  await nextTick()
  dialog.value?.focus()
})

onBeforeUnmount(() => {
  if (previousAriaHidden === null) appContent?.removeAttribute('aria-hidden')
  else if (previousAriaHidden !== undefined) appContent?.setAttribute('aria-hidden', previousAriaHidden)
  previousFocus?.focus?.()
})
</script>

<template>
  <Teleport to="body">
    <div class="research-layer" @click.self="close" @keydown.esc="close">
      <section ref="dialog" class="research-dialog" role="dialog" aria-modal="true"
        aria-labelledby="guild-research-title" tabindex="-1" @keydown.esc="close" @keydown.tab="trapFocus">
        <header class="research-header">
          <div>
            <p>{{ palStore.getTranslatedText('GuildResearch_Eyebrow') }}</p>
            <h2 id="guild-research-title">{{ palStore.getTranslatedText('GuildResearch_Title') }}</h2>
            <small>{{ palStore.getTranslatedText('GuildResearch_Subtitle') }}</small>
          </div>
          <button class="icon-button" :aria-label="palStore.getTranslatedText('Message_Close')" @click="close">
            <UiIcon name="close" />
          </button>
        </header>

        <div class="research-toolbar">
          <label>
            <span>{{ palStore.getTranslatedText('GuildResearch_Guild') }}</span>
            <select v-model="palStore.SELECTED_RESEARCH_GUILD_ID" :disabled="palStore.GUILD_RESEARCH_LOADING"
              @change="selectGuild">
              <option v-for="guild in palStore.GUILD_LIST" :key="guild.GuildId" :value="guild.GuildId">
                {{ guild.GuildName || palStore.getTranslatedText('GuildResearch_Unnamed_Guild') }}
                {{ guild.HasLab ? '' : `(${palStore.getTranslatedText('GuildResearch_No_Lab_Short')})` }}
              </option>
            </select>
          </label>
          <div class="research-progress" role="status">
            <span>{{ palStore.getTranslatedText('GuildResearch_Progress') }}</span>
            <strong>{{ completedCount }} / {{ totalCount }}</strong>
          </div>
          <button class="secondary-button"
            :disabled="palStore.GUILD_RESEARCH_LOADING || palStore.GUILD_RESEARCH_NO_LAB"
            @click="unlockAll">
            <UiIcon name="maximum" /> {{ palStore.getTranslatedText('GuildResearch_Unlock_All') }}
          </button>
        </div>

        <div v-if="palStore.GUILD_RESEARCH_NO_LAB" class="research-empty" role="status">
          <UiIcon name="warning" />
          <div>
            <h3>{{ palStore.getTranslatedText('GuildResearch_No_Lab_Title') }}</h3>
            <p>{{ palStore.getTranslatedText('GuildResearch_No_Lab_Description') }}</p>
          </div>
        </div>

        <template v-else>
          <nav class="research-categories" :aria-label="palStore.getTranslatedText('GuildResearch_Categories')">
            <button v-for="category in palStore.RESEARCH_CATEGORIES" :key="category.key"
              :class="{ active: selectedCategoryKey === category.key }"
              :aria-pressed="selectedCategoryKey === category.key"
              :disabled="palStore.GUILD_RESEARCH_LOADING"
              @click="selectedCategoryKey = category.key">
              <img :src="palStore.backendAssetUrl(`/image/suitabilities/${category.icon}`)" alt="">
              <span>{{ category.label }}</span>
            </button>
          </nav>

          <main class="research-workspace">
            <section class="research-tree-panel" :aria-label="selectedCategory?.label">
              <ul class="research-tree">
                <ResearchNode v-for="node in researchTree" :key="node.InternalName" :node="node"
                  :completed="completed" :current-id="palStore.SELECTED_GUILD_RESEARCH.current_research_id"
                  :selected-id="selectedResearchId" :disabled="palStore.GUILD_RESEARCH_LOADING"
                  :completed-label="palStore.getTranslatedText('GuildResearch_Completed')"
                  :current-label="palStore.getTranslatedText('GuildResearch_Current')"
                  :essential-label="palStore.getTranslatedText('GuildResearch_Essential')"
                  @select="selectedResearchId = $event.InternalName" />
              </ul>
            </section>

            <aside class="research-detail">
              <template v-if="selectedResearch">
                <p>{{ selectedCategory?.label }}</p>
                <h3>{{ selectedResearch.Name || selectedResearch.InternalName }}</h3>
                <span :class="['research-state', { completed: selectedCompleted }]">
                  <UiIcon :name="selectedCompleted ? 'check' : 'branch'" />
                  {{ palStore.getTranslatedText(selectedCompleted
                    ? 'GuildResearch_Completed' : 'GuildResearch_Not_Completed') }}
                </span>
                <dl>
                  <div>
                    <dt>{{ palStore.getTranslatedText('GuildResearch_Effect') }}</dt>
                    <dd>{{ selectedResearch.Description || selectedResearch.InternalName }}</dd>
                  </div>
                  <div>
                    <dt>{{ palStore.getTranslatedText('GuildResearch_Work_Amount') }}</dt>
                    <dd>{{ selectedResearch.WorkAmount }}</dd>
                  </div>
                  <div v-if="selectedResearch.RequireResearchId">
                    <dt>{{ palStore.getTranslatedText('GuildResearch_Requires') }}</dt>
                    <dd>{{ selectedResearch.RequireResearchId }}</dd>
                  </div>
                </dl>
                <p class="cascade-note">{{ palStore.getTranslatedText(selectedCompleted
                  ? 'GuildResearch_Cancel_Cascade' : 'GuildResearch_Unlock_Cascade') }}</p>
                <button :class="['primary-button', { danger: selectedCompleted }]"
                  :disabled="palStore.GUILD_RESEARCH_LOADING" @click="toggleSelectedResearch">
                  <UiIcon :name="selectedCompleted ? 'close' : 'unlock'" />
                  {{ palStore.getTranslatedText(selectedCompleted
                    ? 'GuildResearch_Cancel' : 'GuildResearch_Unlock') }}
                </button>
              </template>
              <p v-else>{{ palStore.getTranslatedText('GuildResearch_Select_Research') }}</p>
            </aside>
          </main>
        </template>

        <footer>
          <span>{{ selectedGuild?.GuildName || palStore.getTranslatedText('GuildResearch_Unnamed_Guild') }}</span>
          <button class="secondary-button" @click="close">{{ palStore.getTranslatedText('Message_Close') }}</button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.research-layer {
  position: fixed;
  inset: 0;
  z-index: 1950;
  display: grid;
  place-items: center;
  padding: var(--editor-space-3);
  background: color-mix(in srgb, var(--editor-color-background) 78%, transparent);
  backdrop-filter: blur(10px);
}

.research-dialog {
  display: grid;
  grid-template-rows: auto auto auto minmax(0, 1fr) auto;
  width: min(78rem, calc(100vw - 1.5rem));
  height: min(52rem, calc(100dvh - 1.5rem));
  overflow: hidden;
  border: 1px solid var(--editor-color-glass-border);
  border-radius: var(--editor-radius-lg);
  color: var(--editor-color-text);
  background: var(--editor-color-glass-surface);
  backdrop-filter: var(--editor-glass-filter);
  box-shadow: var(--editor-glass-shadow);
}

.research-header,
.research-toolbar,
footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--editor-space-3);
  padding: var(--editor-space-3) var(--editor-space-5);
}

.research-header { border-bottom: 1px solid var(--editor-color-border); }
.research-header p,
.research-header h2,
.research-header small,
.research-detail p,
.research-detail h3,
.research-empty h3,
.research-empty p { margin: 0; }
.research-header p,
.research-detail > p { color: var(--editor-color-primary); font-size: .75rem; text-transform: uppercase; }
.research-header small,
.cascade-note,
footer { color: var(--editor-color-muted); }

.research-toolbar {
  flex-wrap: wrap;
  border-bottom: 1px solid var(--editor-color-border);
  background: color-mix(in srgb, var(--editor-color-surface) 72%, transparent);
}
.research-toolbar label { display: grid; gap: var(--editor-space-1); min-width: min(22rem, 100%); }
.research-toolbar label span,
.research-progress span { color: var(--editor-color-muted); font-size: .75rem; }
.research-toolbar select {
  min-width: 0;
  padding: var(--editor-space-2) var(--editor-space-3);
  border: 1px solid var(--editor-color-border);
  border-radius: var(--editor-radius-sm);
  color: var(--editor-color-text);
  background: var(--editor-color-surface);
}
.research-progress { display: grid; }

.research-categories {
  display: flex;
  gap: var(--editor-space-2);
  padding: var(--editor-space-3) var(--editor-space-5);
  overflow-x: auto;
  border-bottom: 1px solid var(--editor-color-border);
}
.research-categories button {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: var(--editor-space-2);
  padding: var(--editor-space-2) var(--editor-space-3);
  border: 1px solid var(--editor-color-border);
  border-radius: 999px;
  color: var(--editor-color-muted);
  background: transparent;
  cursor: pointer;
}
.research-categories button.active {
  border-color: var(--editor-color-primary);
  color: var(--editor-color-text);
  background: color-mix(in srgb, var(--editor-color-primary) 12%, transparent);
}
.research-categories img { width: 1.5rem; height: 1.5rem; object-fit: contain; }

.research-workspace {
  display: grid;
  grid-template-columns: minmax(18rem, 1.5fr) minmax(17rem, .8fr);
  min-height: 0;
}
.research-tree-panel { overflow: auto; padding: var(--editor-space-4); }
.research-tree { display: grid; gap: var(--editor-space-3); margin: 0; padding: 0; list-style: none; }
.research-detail {
  display: flex;
  flex-direction: column;
  gap: var(--editor-space-4);
  padding: var(--editor-space-5);
  overflow: auto;
  border-left: 1px solid var(--editor-color-border);
  background: color-mix(in srgb, var(--editor-color-surface) 66%, transparent);
}
.research-detail dl { display: grid; gap: var(--editor-space-3); margin: 0; }
.research-detail dl div { display: grid; gap: var(--editor-space-1); }
.research-detail dt { color: var(--editor-color-muted); font-size: .75rem; }
.research-detail dd { margin: 0; }
.research-state { display: inline-flex; width: fit-content; align-items: center; gap: var(--editor-space-1); color: var(--editor-color-warning); }
.research-state.completed { color: var(--editor-color-success); }
.research-detail .primary-button { margin-top: auto; }
.research-detail .danger { background: var(--editor-color-danger); }

.research-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--editor-space-4);
  padding: var(--editor-space-6);
  color: var(--editor-color-warning);
}
.research-empty p { color: var(--editor-color-muted); }
footer { border-top: 1px solid var(--editor-color-border); }

.icon-button,
.primary-button,
.secondary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--editor-space-2);
  padding: var(--editor-space-2) var(--editor-space-3);
  border: 1px solid var(--editor-color-border);
  border-radius: var(--editor-radius-sm);
  color: var(--editor-color-text);
  background: var(--editor-color-surface);
  cursor: pointer;
}
.icon-button { padding: var(--editor-space-2); }
.primary-button { border-color: transparent; background: var(--editor-color-primary); }
button:disabled { cursor: not-allowed; opacity: .5; }

@media (max-width: 52rem) {
  .research-dialog { height: calc(100dvh - 1rem); width: calc(100vw - 1rem); }
  .research-header,
  .research-toolbar,
  footer { padding-inline: var(--editor-space-3); }
  .research-workspace { grid-template-columns: 1fr; overflow: auto; }
  .research-tree-panel { overflow: visible; }
  .research-detail { min-height: 19rem; border-top: 1px solid var(--editor-color-border); border-left: 0; }
}
</style>
