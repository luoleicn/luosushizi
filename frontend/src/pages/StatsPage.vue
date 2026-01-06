<template>
  <section class="page">
    <h2>学习小进度</h2>
    <p>看看你已经认识了多少字。</p>
    <p v-if="loading" class="loading">正在加载统计</p>
    <p v-if="error" class="notice error">统计没加载出来，待会儿再看看。</p>
    <p v-if="stats.due_today === 0 && !loading" class="notice success">今天的复习完成啦！</p>
    <p v-if="readOnly" class="notice info">当前是公开字典，只能查看统计。</p>
    <div class="panel progress-panel">
      <div class="progress-row">
        <span>已掌握</span>
        <div class="bar">
          <div class="bar-fill" :style="{ width: `${knownRate}%` }"></div>
        </div>
        <strong>{{ knownRate }}%</strong>
      </div>
      <div class="progress-row">
        <span>今日待复习</span>
        <div class="bar">
          <div class="bar-fill cool" :style="{ width: `${dueRate}%` }"></div>
        </div>
        <strong>{{ dueRate }}%</strong>
      </div>
    </div>
    <div class="panel weekly-panel">
      <div class="weekly-header">
        <h3>本周小进度</h3>
        <span>模拟展示</span>
      </div>
      <div class="weekly-bars">
        <div v-for="(day, index) in weekData" :key="index" class="week-bar">
          <div class="bar">
            <div class="bar-fill" :style="{ width: `${day.value}%` }"></div>
          </div>
          <span>{{ day.label }}</span>
        </div>
      </div>
    </div>
    <div class="grid two">
      <div class="panel stat-card">
        <h3>总汉字数</h3>
        <strong>{{ stats.total }}</strong>
        <span>已经装进卡片</span>
      </div>
      <div class="panel stat-card">
        <h3>今日待复习</h3>
        <strong>{{ stats.due_today }}</strong>
        <span>准备开始复习</span>
      </div>
      <div class="panel stat-card">
        <h3>已掌握</h3>
        <strong>{{ stats.known }}</strong>
        <span>越来越熟练</span>
      </div>
      <div class="panel stat-card">
        <h3>学习时长</h3>
        <strong>{{ formattedTime }}</strong>
        <span>已经努力这么久</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { api } from "../api/client";
import { getDictionaryState, loadDictionaries } from "../store/dictionary";

const stats = ref({
  total: 0,
  known: 0,
  due_today: 0,
  study_time_total: 0,
});
const loading = ref(false);
const error = ref("");
const dictionary = getDictionaryState();
const readOnly = computed(() => {
  const current = dictionary.items.find((item) => item.id === dictionary.currentId);
  return current ? !current.is_owner && current.visibility === "public" : false;
});

const loadStats = async () => {
  loading.value = true;
  error.value = "";
  try {
    if (!dictionary.currentId) {
      error.value = "请先选择一个字典。";
      stats.value = { total: 0, known: 0, due_today: 0, study_time_total: 0 };
      return;
    }
    const result = await api.getStats(dictionary.currentId);
    stats.value = result;
  } catch (err) {
    error.value = err.message || "Failed to load stats.";
  } finally {
    loading.value = false;
  }
};

const formattedTime = computed(() => {
  const seconds = stats.value.study_time_total || 0;
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
});

onMounted(() => {
  loadDictionaries().then(() => {
    if (!dictionary.currentId) {
      return;
    }
    loadStats();
  });
});

watch(
  () => dictionary.currentId,
  (nextId, prevId) => {
    if (!nextId || nextId === prevId) {
      return;
    }
    loadStats();
  }
);

const knownRate = computed(() => {
  if (!stats.value.total) {
    return 0;
  }
  return Math.min(100, Math.round((stats.value.known / stats.value.total) * 100));
});

const dueRate = computed(() => {
  if (!stats.value.total) {
    return 0;
  }
  return Math.min(100, Math.round((stats.value.due_today / stats.value.total) * 100));
});

const weekData = ref([
  { label: "一", value: 30 },
  { label: "二", value: 50 },
  { label: "三", value: 40 },
  { label: "四", value: 60 },
  { label: "五", value: 45 },
  { label: "六", value: 80 },
  { label: "日", value: 55 },
]);
</script>

<style scoped>
.stat-card {
  display: grid;
  gap: 6px;
  min-height: 140px;
}

.stat-card h3 {
  margin: 0;
  font-size: 15px;
  color: rgba(0, 0, 0, 0.6);
}

.stat-card strong {
  font-size: 32px;
}

.stat-card span {
  color: rgba(0, 0, 0, 0.5);
}

.progress-panel {
  margin: 16px 0;
  display: grid;
  gap: 12px;
}

.progress-row {
  display: grid;
  grid-template-columns: 90px 1fr 50px;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.7);
}

.bar {
  height: 10px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: #f2b705;
  border-radius: 999px;
}

.bar-fill.cool {
  background: #8bb7f0;
}

.weekly-panel {
  margin: 16px 0;
  display: grid;
  gap: 12px;
}

.weekly-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.weekly-header h3 {
  margin: 0;
  font-size: 16px;
}

.weekly-header span {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.5);
}

.weekly-bars {
  display: grid;
  gap: 8px;
}

.week-bar {
  display: grid;
  grid-template-columns: 1fr 24px;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.6);
}
</style>
