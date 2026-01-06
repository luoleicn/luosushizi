<template>
  <section class="page">
    <h2>字典管理</h2>
    <p>创建自己的字库，或查看公开字典。</p>

    <div class="grid two">
      <div class="panel">
        <h3>新建字典</h3>
        <label class="field">
          <span>名称</span>
          <input v-model="form.name" type="text" placeholder="例如：一年级识字" />
        </label>
        <label class="field">
          <span>权限</span>
          <select v-model="form.visibility">
            <option value="private">私有</option>
            <option value="public">公开</option>
          </select>
        </label>
        <div class="actions">
          <button class="btn btn-primary" :disabled="loading" @click="createDict">
            {{ loading ? "正在创建..." : "创建" }}
          </button>
        </div>
        <p v-if="message" :class="['notice', messageType]">{{ message }}</p>
      </div>

      <div class="panel">
        <h3>我的与公开字典</h3>
        <div v-if="dictionary.items.length" class="dict-list">
          <div v-for="item in dictionary.items" :key="item.id" class="dict-item">
            <div class="dict-title">
              <strong>{{ item.name }}</strong>
              <span class="tag">{{ item.visibility === 'public' ? '公开' : '私有' }}</span>
              <span v-if="item.is_owner" class="tag owner">我的</span>
              <span v-else class="tag readonly">只读</span>
            </div>
            <div class="dict-actions">
              <button class="btn btn-ghost" @click="setCurrent(item.id)">使用</button>
              <button
                class="btn btn-secondary"
                :disabled="!item.is_owner"
                @click="startEdit(item)"
              >
                编辑
              </button>
              <button
                class="btn btn-ghost"
                :disabled="!item.is_owner"
                @click="removeDict(item)"
              >
                删除
              </button>
            </div>
          </div>
        </div>
        <p v-else class="notice info">还没有字典，先创建一个吧。</p>
      </div>
    </div>

    <div v-if="editing" class="panel edit-panel">
      <h3>编辑字典</h3>
      <label class="field">
        <span>名称</span>
        <input v-model="editForm.name" type="text" />
      </label>
      <label class="field">
        <span>权限</span>
        <select v-model="editForm.visibility">
          <option value="private">私有</option>
          <option value="public">公开</option>
        </select>
      </label>
      <div class="actions">
        <button class="btn btn-primary" :disabled="loading" @click="saveEdit">
          保存
        </button>
        <button class="btn btn-ghost" @click="cancelEdit">取消</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { api } from "../api/client";
import { getDictionaryState, loadDictionaries, setCurrentDictionary } from "../store/dictionary";

const dictionary = getDictionaryState();
const loading = ref(false);
const message = ref("");
const messageType = ref("info");
const editing = ref(false);
const form = reactive({ name: "", visibility: "private" });
const editForm = reactive({ id: null, name: "", visibility: "private" });

const refresh = async () => {
  await loadDictionaries();
};

const createDict = async () => {
  if (!form.name.trim()) {
    messageType.value = "error";
    message.value = "请先填写字典名称。";
    return;
  }
  loading.value = true;
  message.value = "";
  try {
    await api.createDictionary({
      name: form.name.trim(),
      visibility: form.visibility,
    });
    messageType.value = "success";
    message.value = "字典创建成功！";
    form.name = "";
    await refresh();
  } catch (err) {
    messageType.value = "error";
    message.value = err.message || "创建失败，请稍后再试。";
  } finally {
    loading.value = false;
  }
};

const setCurrent = (id) => {
  setCurrentDictionary(id);
};

const startEdit = (item) => {
  editing.value = true;
  editForm.id = item.id;
  editForm.name = item.name;
  editForm.visibility = item.visibility;
};

const saveEdit = async () => {
  if (!editForm.id) {
    return;
  }
  loading.value = true;
  try {
    await api.updateDictionary(editForm.id, {
      name: editForm.name.trim(),
      visibility: editForm.visibility,
    });
    editing.value = false;
    await refresh();
  } catch (err) {
    messageType.value = "error";
    message.value = err.message || "更新失败，请稍后再试。";
  } finally {
    loading.value = false;
  }
};

const removeDict = async (item) => {
  if (!item.is_owner) {
    return;
  }
  const confirmed = window.confirm("确认删除该字典吗？删除后无法恢复。");
  if (!confirmed) {
    return;
  }
  loading.value = true;
  try {
    await api.deleteDictionary(item.id);
    if (dictionary.currentId === item.id) {
      const remaining = dictionary.items.filter((dict) => dict.id !== item.id);
      dictionary.currentId = remaining.length ? remaining[0].id : null;
    }
    await refresh();
  } catch (err) {
    messageType.value = "error";
    message.value = err.message || "删除失败，请稍后再试。";
  } finally {
    loading.value = false;
  }
};

const cancelEdit = () => {
  editing.value = false;
};

onMounted(() => {
  refresh();
});
</script>

<style scoped>
.field {
  display: grid;
  gap: 8px;
  font-weight: 600;
}

.field span {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.7);
}

.field input,
.field select {
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  font-size: 16px;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.dict-list {
  display: grid;
  gap: 12px;
}

.dict-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.04);
}

.dict-title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.dict-actions {
  display: flex;
  gap: 8px;
}

.tag {
  margin-left: 8px;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.08);
}

.tag.owner {
  background: rgba(242, 183, 5, 0.2);
  color: #7a4b00;
}

.tag.readonly {
  background: rgba(30, 98, 185, 0.15);
  color: #1e4b84;
}

.edit-panel {
  margin-top: 16px;
}
</style>
