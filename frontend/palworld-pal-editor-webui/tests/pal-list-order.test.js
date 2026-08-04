import assert from "node:assert/strict";
import test from "node:test";

import {
  filterPalPriority,
  isCreatedPal,
  isEditedPal,
  matchesPalSessionFilter,
  sortPalList,
} from "../src/components/modules/pal-list-order.js";

const pals = [
  { InstanceId: "storage-2", ContainerKind: "storage", SlotIndex: 2, FavoriteIndex: 1, Paldeck: "002", DisplayName: "Cattiva 10", Level: 40, Talent_HP: 60, Talent_Shot: 70, Talent_Defense: 80 },
  { InstanceId: "party-4", ContainerKind: "party", SlotIndex: 4, FavoriteIndex: 2, Paldeck: "004", DisplayName: "Lamball", Level: 20, Talent_HP: 50, Talent_Shot: 40, Talent_Defense: 30 },
  { InstanceId: "party-0", ContainerKind: "party", SlotIndex: 0, FavoriteIndex: 3, Paldeck: "003", DisplayName: "Cattiva 2", Level: 50, Talent_HP: 90, Talent_Shot: 90, Talent_Defense: 90 },
  { InstanceId: "storage-0", ContainerKind: "storage", SlotIndex: 0, FavoriteIndex: 0, Paldeck: "001", DisplayName: "Anubis", Level: 10, Talent_HP: 10, Talent_Shot: 20, Talent_Defense: 30 },
];

test("Pal list sorting follows the explicitly selected mode", () => {
  assert.deepEqual(
    sortPalList(pals, "location").map(pal => pal.InstanceId),
    ["party-0", "party-4", "storage-0", "storage-2"],
  );
  assert.deepEqual(
    sortPalList([...pals].reverse(), "priority").map(pal => pal.InstanceId),
    ["party-0", "party-4", "storage-2", "storage-0"],
  );
  assert.deepEqual(
    sortPalList([...pals].reverse(), "paldeck").map(pal => pal.InstanceId),
    ["storage-0", "storage-2", "party-0", "party-4"],
  );
});

test("location sorting groups base-camp Pals by container before slot", () => {
  const baseCampPals = [
    { InstanceId: "container-b-slot-0", ContainerKind: "other", ContainerId: "bbbb", SlotIndex: 0 },
    { InstanceId: "container-a-slot-5", ContainerKind: "other", ContainerId: "aaaa", SlotIndex: 5 },
    { InstanceId: "container-a-slot-1", ContainerKind: "other", ContainerId: "aaaa", SlotIndex: 1 },
  ];

  assert.deepEqual(
    sortPalList(baseCampPals, "location").map(pal => pal.InstanceId),
    ["container-a-slot-1", "container-a-slot-5", "container-b-slot-0"],
  );
});

test("Pal list sorting supports level, active IV total, name, and direction", () => {
  assert.deepEqual(
    sortPalList(pals, "level").map(pal => pal.InstanceId),
    ["storage-0", "party-4", "storage-2", "party-0"],
  );
  assert.deepEqual(
    sortPalList(pals, "iv", pal => pal.Paldeck, "desc").map(pal => pal.InstanceId),
    ["party-0", "storage-2", "party-4", "storage-0"],
  );
  assert.deepEqual(
    sortPalList(pals, "name").map(pal => pal.InstanceId),
    ["storage-0", "party-0", "storage-2", "party-4"],
  );
  assert.deepEqual(
    sortPalList(pals, "paldeck", pal => pal.Paldeck, "desc").map(pal => pal.InstanceId),
    ["party-4", "party-0", "storage-2", "storage-0"],
  );
});

test("Paldeck sorting places Pals without a Paldeck number last", () => {
  const withoutPaldeck = { InstanceId: "human", Paldeck: "" };

  assert.deepEqual(
    sortPalList([withoutPaldeck, ...pals], "paldeck").map(pal => pal.InstanceId),
    ["storage-0", "storage-2", "party-0", "party-4", "human"],
  );
});

test("Pal priority filtering recognizes unprioritized and I to III", () => {
  assert.deepEqual(pals.filter(pal => filterPalPriority(pal, "all")), pals);
  assert.deepEqual(pals.filter(pal => filterPalPriority(pal, "0")).map(pal => pal.InstanceId), ["storage-0"]);
  assert.deepEqual(pals.filter(pal => filterPalPriority(pal, "1")).map(pal => pal.InstanceId), ["storage-2"]);
  assert.deepEqual(pals.filter(pal => filterPalPriority(pal, "2")).map(pal => pal.InstanceId), ["party-4"]);
  assert.deepEqual(pals.filter(pal => filterPalPriority(pal, "3")).map(pal => pal.InstanceId), ["party-0"]);
});

test("Editor-created Pals can be filtered explicitly without changing sort order", () => {
  const created = new Set(["storage-2"]);
  assert.deepEqual(pals.filter(pal => isCreatedPal(pal, created)).map(pal => pal.InstanceId), ["storage-2"]);
  assert.equal(isCreatedPal({ InstanceId: "new", IsNewPal: true }, new Set()), true);
});

test("Edited session filtering includes created Pals but created filtering stays specific", () => {
  const edited = new Set(["edited"]);
  const created = new Set(["created"]);
  const unchangedPal = { InstanceId: "unchanged" };
  const editedPal = { InstanceId: "edited" };
  const createdPal = { InstanceId: "created" };

  assert.equal(isEditedPal(editedPal, edited, created), true);
  assert.equal(isEditedPal(createdPal, edited, created), true);
  assert.equal(isEditedPal(unchangedPal, edited, created), false);

  assert.equal(matchesPalSessionFilter(unchangedPal, false, false, edited, created), true);
  assert.equal(matchesPalSessionFilter(editedPal, true, false, edited, created), true);
  assert.equal(matchesPalSessionFilter(createdPal, true, false, edited, created), true);
  assert.equal(matchesPalSessionFilter(editedPal, false, true, edited, created), false);
  assert.equal(matchesPalSessionFilter(createdPal, false, true, edited, created), true);
  assert.equal(matchesPalSessionFilter(editedPal, true, true, edited, created), false);
  assert.equal(matchesPalSessionFilter(createdPal, true, true, edited, created), true);
});
