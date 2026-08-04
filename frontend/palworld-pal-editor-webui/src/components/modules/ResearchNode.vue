<script setup>
import UiIcon from '@/components/modules/UiIcon.vue'

defineOptions({ name: 'ResearchNode' })

defineProps({
  node: { type: Object, required: true },
  completed: { type: Set, required: true },
  currentId: { type: String, default: '' },
  selectedId: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  completedLabel: { type: String, default: 'Completed' },
  currentLabel: { type: String, default: 'Current research' },
  essentialLabel: { type: String, default: 'Essential research' },
})

const emit = defineEmits(['select'])
</script>

<template>
  <li class="research-branch">
    <button
      :class="['research-node', {
        completed: completed.has(node.InternalName),
        current: currentId === node.InternalName,
        selected: selectedId === node.InternalName,
        essential: node.IsEssential,
      }]"
      :aria-pressed="selectedId === node.InternalName"
      :disabled="disabled"
      @click="emit('select', node)"
    >
      <UiIcon :name="completed.has(node.InternalName) ? 'check' : 'branch'" />
      <span>
        <strong>{{ node.Name || node.InternalName }}</strong>
        <small>{{ node.Description || node.InternalName }}</small>
      </span>
      <em v-if="node.WorkAmount">{{ node.WorkAmount }}</em>
      <span class="sr-only">
        {{ completed.has(node.InternalName) ? completedLabel : '' }}
        {{ currentId === node.InternalName ? currentLabel : '' }}
        {{ node.IsEssential ? essentialLabel : '' }}
      </span>
    </button>
    <ul v-if="node.children?.length" class="research-children">
      <ResearchNode
        v-for="child in node.children"
        :key="child.InternalName"
        :node="child"
        :completed="completed"
        :current-id="currentId"
        :selected-id="selectedId"
        :disabled="disabled"
        :completed-label="completedLabel"
        :current-label="currentLabel"
        :essential-label="essentialLabel"
        @select="emit('select', $event)"
      />
    </ul>
  </li>
</template>

<style scoped>
.research-branch,
.research-children {
  display: grid;
  gap: var(--editor-space-2);
  margin: 0;
  padding: 0;
  list-style: none;
}

.research-children {
  position: relative;
  padding-left: var(--editor-space-5);
}

.research-children::before {
  position: absolute;
  top: 0;
  bottom: var(--editor-space-3);
  left: .65rem;
  width: 1px;
  background: var(--editor-color-border);
  content: '';
}

.research-node {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  width: 100%;
  align-items: center;
  gap: var(--editor-space-3);
  padding: var(--editor-space-3);
  border: 1px solid var(--editor-color-border);
  border-radius: var(--editor-radius-md);
  color: var(--editor-color-text);
  text-align: left;
  background: color-mix(in srgb, var(--editor-color-surface) 78%, transparent);
  cursor: pointer;
}

.research-node:hover,
.research-node.selected {
  border-color: var(--editor-color-primary);
  background: color-mix(in srgb, var(--editor-color-primary) 10%, var(--editor-color-surface));
}

.research-node.completed { border-color: var(--editor-color-success); }
.research-node.current { box-shadow: inset .22rem 0 var(--editor-color-warning); }
.research-node.essential strong::after { color: var(--editor-color-warning); content: ' *'; }
.research-node span { min-width: 0; }
.research-node strong,
.research-node small { display: block; }
.research-node small {
  overflow: hidden;
  color: var(--editor-color-muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}
.research-node em {
  color: var(--editor-color-muted);
  font-size: .75rem;
  font-style: normal;
}
</style>
