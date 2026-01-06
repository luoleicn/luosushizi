import { reactive } from "vue";
import { api, getToken } from "../api/client";

const dictionaryState = reactive({
  items: [],
  currentId: null,
});

export async function loadDictionaries() {
  if (!getToken()) {
    dictionaryState.items = [];
    dictionaryState.currentId = null;
    return dictionaryState.items;
  }
  const result = await api.listDictionaries();
  const items = result.items || [];
  items.sort((a, b) => {
    if (a.is_owner !== b.is_owner) {
      return a.is_owner ? -1 : 1;
    }
    if (a.visibility !== b.visibility) {
      return a.visibility === "private" ? -1 : 1;
    }
    return a.name.localeCompare(b.name);
  });
  dictionaryState.items = items;
  if (!dictionaryState.currentId && dictionaryState.items.length) {
    dictionaryState.currentId = dictionaryState.items[0].id;
  }
  return dictionaryState.items;
}

export function getDictionaryState() {
  return dictionaryState;
}

export function setCurrentDictionary(id) {
  dictionaryState.currentId = id;
}

export function getCurrentDictionary() {
  return dictionaryState.items.find((item) => item.id === dictionaryState.currentId) || null;
}
