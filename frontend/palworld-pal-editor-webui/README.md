# palworld-pal-editor-webui

Vue 3 and Vite frontend for Palworld Pal Editor.

## Overview

The WebUI provides separate player and base rosters, groups working Pals by base, exposes unmatched workers as unassigned, and displays base details. It also provides guild-scoped Lab research editing when the connected backend supports the research catalog API.

Guild research is opened from the loaded-save toolbar. It edits existing Lab data and does not create Lab data for guilds that do not already have it.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur) + [TypeScript Vue Plugin (Volar)](https://marketplace.visualstudio.com/items?itemName=Vue.vscode-typescript-vue-plugin).

## Customize configuration

See [Vite Configuration Reference](https://vitejs.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```

### Tests

Run the frontend contract and utility tests with Node's built-in test runner:

```sh
node --test tests/*.test.js
```
