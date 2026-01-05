<template>
  <section class="page">
    <h2>装进小卡片</h2>
    <p>把要认识的字放进来，一字一张卡。</p>
    <div class="grid two">
      <div class="panel">
        <label class="field">
          <span>汉字</span>
          <textarea
            v-model="text"
            @input="updateCounts"
            rows="6"
            placeholder="例如：春夏秋冬天地人"
          ></textarea>
        </label>
        <div class="summary">
          <span>总数：{{ counts.total }}</span>
          <span>去重：{{ counts.unique }}</span>
          <span>无效：{{ counts.invalid }}</span>
        </div>
        <div class="preview" v-if="previewGroups.length">
          <div v-for="group in previewGroups" :key="group.key" class="group">
            <div class="group-label">组</div>
            <div class="group-chars">
              <span
                v-for="item in group.chars"
                :key="item.key"
                :class="['char', item.valid ? 'valid' : 'invalid']"
              >
                {{ item.char }}
              </span>
            </div>
          </div>
        </div>
        <div class="actions">
          <button class="btn btn-primary" :disabled="loading" @click="handleImport">
            {{ loading ? "正在导入..." : "导入" }}
          </button>
          <button class="btn btn-ghost" @click="clearText">清空</button>
        </div>
        <p v-if="message" :class="['notice', messageType]">{{ message }}</p>
        <p v-if="counts.invalid > 0" class="notice info">
          已自动过滤 {{ counts.invalid }} 个非汉字字符。
        </p>
      </div>
      <div class="panel hint-panel">
        <h3>小贴士</h3>
        <ul>
          <li>只放汉字就可以啦。</li>
          <li>拼音和常用词由离线词库给出。</li>
          <li>重复的字会自动跳过。</li>
          <li>可以用空格或逗号分组，方便检查。</li>
        </ul>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from "vue";
import { api } from "../api/client";

const text = ref("");
const loading = ref(false);
const message = ref("");
const messageType = ref("info");
const counts = ref({ total: 0, unique: 0, invalid: 0 });

const isHanzi = (char) => char >= "\u4e00" && char <= "\u9fff";

const separatorRegex = /[\\s,，、;；]+/;

const previewGroups = computed(() => {
  const raw = text.value.trim();
  if (!raw) {
    return [];
  }
  const groups = raw.split(separatorRegex).filter(Boolean);
  return groups.map((group, index) => ({
    key: `${group}-${index}`,
    text: group,
    chars: Array.from(group).map((char, idx) => ({
      char,
      key: `${group}-${index}-${idx}`,
      valid: isHanzi(char),
    })),
  }));
});

const updateCounts = () => {
  extractCharacters(text.value);
};

const clearText = () => {
  text.value = "";
  message.value = "";
  counts.value = { total: 0, unique: 0, invalid: 0 };
};

const extractCharacters = (input) => {
  const matches = input.match(/[\u4e00-\u9fa5]/g) || [];
  const unique = Array.from(new Set(matches));
  const invalid = Array.from(input).filter((char) => !isHanzi(char)).length;
  counts.value = {
    total: matches.length,
    unique: unique.length,
    invalid,
  };
  return unique;
};

const handleImport = async () => {
  message.value = "";
  updateCounts();
  const items = extractCharacters(text.value);
  if (!items.length) {
    messageType.value = "error";
    message.value = "这里只有汉字才会变成卡片哦。";
    return;
  }
  loading.value = true;
  try {
    const result = await api.importCharacters({ items });
    messageType.value = "success";
    message.value = `已装进 ${result.imported} 个字，跳过 ${result.skipped} 个。真棒！`;
  } catch (err) {
    messageType.value = "error";
    message.value = "哎呀，导入失败了，再试一次吧。";
  } finally {
    loading.value = false;
  }
};
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

.field textarea {
  padding: 14px;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  font-size: 18px;
  resize: vertical;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.summary {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 10px;
  color: rgba(0, 0, 0, 0.6);
  font-weight: 600;
}

.preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.group {
  display: grid;
  gap: 6px;
  padding: 8px;
  border-radius: 12px;
  border: 1px dashed rgba(0, 0, 0, 0.12);
  background: rgba(255, 255, 255, 0.6);
}

.group-label {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.5);
}

.group-chars {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.char {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  font-size: 18px;
  font-weight: 600;
}

.char.valid {
  background: rgba(29, 143, 77, 0.12);
  color: #1a5b37;
}

.char.invalid {
  background: rgba(178, 59, 59, 0.12);
  color: #7b1f1f;
}

.hint-panel h3 {
  margin: 0 0 12px;
}

.hint-panel ul {
  margin: 0;
  padding-left: 18px;
  color: rgba(0, 0, 0, 0.6);
}

</style>
