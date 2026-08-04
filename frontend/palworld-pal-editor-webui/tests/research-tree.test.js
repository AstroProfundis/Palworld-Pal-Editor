import assert from "node:assert/strict";
import test from "node:test";

import {
  buildCompletedIdSet,
  buildResearchTree,
  findResearchNode,
} from "../src/utils/researchTree.js";

const items = [
  { InternalName: "Root", RequireResearchId: null },
  { InternalName: "Child", RequireResearchId: "Root" },
  { InternalName: "Grandchild", RequireResearchId: "Child" },
  { InternalName: "Orphan", RequireResearchId: "Missing" },
];

test("research tree preserves dependencies and promotes missing-parent nodes", () => {
  const tree = buildResearchTree(items);

  assert.deepEqual(tree.map(node => node.InternalName), ["Root", "Orphan"]);
  assert.equal(tree[0].children[0].InternalName, "Child");
  assert.equal(tree[0].children[0].children[0].InternalName, "Grandchild");
  assert.equal(findResearchNode(tree, "Grandchild")?.RequireResearchId, "Child");
  assert.equal(findResearchNode(tree, "Unknown"), null);
});

test("completed research ids normalize into a membership set", () => {
  const completed = buildCompletedIdSet(["Root", "Child", "Root", null]);

  assert.deepEqual([...completed], ["Root", "Child"]);
});
