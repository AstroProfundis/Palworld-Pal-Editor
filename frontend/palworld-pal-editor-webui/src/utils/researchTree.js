export function buildCompletedIdSet(ids = []) {
  return new Set(ids.filter(id => typeof id === "string" && id));
}

export function buildResearchTree(items = []) {
  const nodes = new Map(items.map(item => [item.InternalName, { ...item, children: [] }]));
  const roots = [];

  for (const node of nodes.values()) {
    const parent = nodes.get(node.RequireResearchId);
    if (parent) parent.children.push(node);
    else roots.push(node);
  }

  return roots;
}

export function findResearchNode(nodes, id) {
  for (const node of nodes) {
    if (node.InternalName === id) return node;
    const found = findResearchNode(node.children || [], id);
    if (found) return found;
  }
  return null;
}
