<template>
  <section class="page">
    <h2>开始识字</h2>
    <p>认识就点“认识”，不认识就点“不认识”。</p>
    <p v-if="loading" class="loading">正在加载队列</p>
    <p v-if="error" class="notice error">队列加载失败了，稍后再试试。</p>
    <div class="study-layout">
      <div class="panel card-panel">
        <div class="card-face" :class="{ empty: !currentCard, reveal: currentCard }">
          {{ currentCard?.hanzi || "无" }}
        </div>
        <div class="card-actions">
          <button class="btn btn-primary" :disabled="!currentCard" @click="markKnown">
            我认识
          </button>
          <button class="btn btn-secondary" :disabled="!currentCard" @click="markUnknown">
            我不认识
          </button>
        </div>
        <p v-if="badgeMessage" class="badge">{{ badgeMessage }}</p>
        <p v-if="encouragement" class="encourage">{{ encouragement }}</p>
        <button class="sound-toggle" @click="soundEnabled = !soundEnabled">
          {{ soundEnabled ? "音效开" : "音效关" }}
        </button>
        <div v-if="showHint" class="hint reveal-hint">
          <div class="hint-title">提示</div>
          <div class="hint-body">
            <span class="pill">{{ hint.pinyin || "..." }}</span>
            <span v-for="word in hint.commonWords" :key="word.word" class="pill">
              {{ word.word }}
            </span>
          </div>
        </div>
        <button class="btn btn-ghost next-btn" :disabled="!currentCard" @click="nextCard">
          下一张
        </button>
        <p class="key-hint">快捷键：Enter/→ 我认识，←/Backspace 我不认识，空格 下一张</p>
        <div v-if="!currentCard" class="empty-state reveal-hint">
          <div v-if="completed" class="stars" aria-hidden="true">★ ☆ ★</div>
          <p>{{ emptyMessage }}</p>
          <div class="empty-actions">
            <button class="btn btn-primary" :disabled="loading" @click="reloadQueue">
              {{ loading ? "正在刷新..." : "刷新队列" }}
            </button>
            <router-link class="btn btn-ghost" to="/input">去录入</router-link>
          </div>
        </div>
      </div>
      <aside class="panel side-panel">
        <h3>今日</h3>
        <div class="stat">
          <span>待复习</span>
          <strong>{{ stats.due }}</strong>
        </div>
        <div class="stat">
          <span>新卡片</span>
          <strong>{{ stats.new }}</strong>
        </div>
        <div class="stat">
          <span>已复习</span>
          <strong>{{ stats.reviewed }}</strong>
        </div>
      </aside>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { api } from "../api/client";

const queue = ref([]);
const currentIndex = ref(0);
const showHint = ref(false);
const hint = ref({ pinyin: "", commonWords: [] });
const stats = ref({ due: 0, new: 0, reviewed: 0 });
const loading = ref(false);
const error = ref("");
const sessionId = ref(null);
const emptyMessage = ref("今天的卡片已经学完啦，可以去录入新字。");
const sessionClosed = ref(false);
const completed = ref(false);
const streak = ref(0);
const badgeMessage = ref("");
const encouragement = ref("");
const soundEnabled = ref(true);

const currentCard = computed(() => queue.value[currentIndex.value]);

const loadQueue = async () => {
  loading.value = true;
  error.value = "";
  try {
    const result = await api.getQueue();
    queue.value = result.items || [];
    currentIndex.value = 0;
    stats.value = {
      due: queue.value.length,
      new: queue.value.filter((item) => item.is_new).length,
      reviewed: 0,
    };
  } catch (err) {
    error.value = err.message || "Failed to load queue.";
  } finally {
    loading.value = false;
  }
};

const loadHint = async (hanzi) => {
  const result = await api.getCharacterInfo(hanzi);
  hint.value = {
    pinyin: result.pinyin,
    commonWords: result.common_words || [],
  };
};

const nextCard = () => {
  showHint.value = false;
  hint.value = { pinyin: "", commonWords: [] };
  if (currentIndex.value < queue.value.length - 1) {
    currentIndex.value += 1;
  } else {
    currentIndex.value = queue.value.length;
    completed.value = true;
    emptyMessage.value = "太棒了！这轮学习完成啦，继续加油！";
    closeSessionIfNeeded();
  }
};

const review = async (rating) => {
  if (!currentCard.value) {
    return;
  }
  if (rating >= 3) {
    streak.value += 1;
    if (streak.value > 0 && streak.value % 3 === 0) {
      badgeMessage.value = `连对 ${streak.value} 次！`;
      setTimeout(() => {
        badgeMessage.value = "";
      }, 1500);
    }
  } else {
    streak.value = 0;
  }
  if (currentCard.value.is_new && stats.value.new > 0) {
    stats.value.new -= 1;
  }
  if (stats.value.due > 0) {
    stats.value.due -= 1;
  }
  await api.review({ hanzi: currentCard.value.hanzi, rating });
  stats.value.reviewed += 1;
};

const markKnown = async () => {
  encouragement.value = "太厉害了！继续加油！";
  setTimeout(() => {
    encouragement.value = "";
  }, 1400);
  playSound("known");
  await review(4);
  nextCard();
};

const markUnknown = async () => {
  showHint.value = true;
  encouragement.value = "没关系，看看提示再试试。";
  setTimeout(() => {
    encouragement.value = "";
  }, 1800);
  playSound("unknown");
  await loadHint(currentCard.value.hanzi);
  await review(2);
};

const playSound = (type) => {
  if (!soundEnabled.value) {
    return;
  }
  const audio = new Audio(type === "known" ? "/sounds/success.mp3" : "/sounds/try.mp3");
  audio.volume = 0.5;
  audio.play().catch(() => {});
};

const reloadQueue = async () => {
  await loadQueue();
  if (!queue.value.length) {
    emptyMessage.value = "今天的卡片已经学完啦，可以去录入新字。";
    completed.value = false;
    await closeSessionIfNeeded();
  } else {
    emptyMessage.value = "";
    completed.value = false;
    streak.value = 0;
  }
};

const closeSessionIfNeeded = async () => {
  if (sessionId.value && !sessionClosed.value) {
    sessionClosed.value = true;
    await api.endSession({ session_id: sessionId.value });
  }
};

onMounted(() => {
  loadQueue();
  api.startSession().then((result) => {
    sessionId.value = result.session_id;
  });
  window.addEventListener("keydown", handleKey);
});

onBeforeUnmount(() => {
  closeSessionIfNeeded();
  window.removeEventListener("keydown", handleKey);
});

const handleKey = (event) => {
  const target = event.target;
  if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) {
    return;
  }
  if (event.key === "ArrowRight" || event.key === "Enter") {
    markKnown();
  } else if (event.key === "ArrowLeft" || event.key === "Backspace") {
    markUnknown();
  } else if (event.key === " ") {
    nextCard();
  }
};
</script>

<style scoped>
.study-layout {
  display: grid;
  gap: 16px;
}

@media (min-width: 900px) {
  .study-layout {
    grid-template-columns: 2fr 1fr;
  }
}

.card-panel {
  display: grid;
  gap: 18px;
  align-items: center;
  justify-items: center;
  text-align: center;
  padding: 28px;
}

.card-face {
  width: min(320px, 70vw);
  height: min(320px, 70vw);
  border-radius: 28px;
  display: grid;
  place-items: center;
  font-size: clamp(96px, 18vw, 160px);
  font-weight: 700;
  background: linear-gradient(145deg, #fff8e1, #f5d76e);
  box-shadow: 0 18px 45px rgba(245, 215, 110, 0.45);
}

.card-face.empty {
  background: linear-gradient(145deg, #f7f5f1, #f0ede7);
  color: rgba(0, 0, 0, 0.35);
  box-shadow: none;
}

.card-face.reveal {
  animation: card-pop 0.45s ease;
}

.card-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.badge {
  margin: 0;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(242, 183, 5, 0.2);
  color: #7a4b00;
  font-weight: 700;
  animation: hint-fade 0.35s ease;
}

.encourage {
  margin: 0;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.6);
  animation: hint-fade 0.35s ease;
}

.sound-toggle {
  border: none;
  background: rgba(0, 0, 0, 0.08);
  color: rgba(0, 0, 0, 0.7);
  padding: 6px 12px;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 600;
}

.hint {
  width: 100%;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.85);
  padding: 12px 14px;
  border: 1px dashed rgba(0, 0, 0, 0.12);
}

.hint-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
  color: rgba(0, 0, 0, 0.6);
}

.hint-body {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pill {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.07);
  font-size: 14px;
}

.next-btn {
  justify-self: center;
}

.key-hint {
  margin: 0;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.55);
}

.reveal-hint {
  animation: hint-fade 0.35s ease;
}

.empty-state {
  text-align: center;
  display: grid;
  gap: 12px;
  justify-items: center;
}

.empty-state p {
  margin: 0;
}

.stars {
  font-size: 22px;
  color: #f2b705;
  letter-spacing: 4px;
  animation: twinkle 1.2s ease-in-out infinite;
}

.empty-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

@keyframes card-pop {
  0% {
    transform: translateY(10px) scale(0.97);
    opacity: 0;
  }
  100% {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

@keyframes hint-fade {
  0% {
    transform: translateY(6px);
    opacity: 0;
  }
  100% {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes twinkle {
  0% {
    transform: scale(0.95);
    opacity: 0.6;
  }
  50% {
    transform: scale(1.05);
    opacity: 1;
  }
  100% {
    transform: scale(0.95);
    opacity: 0.6;
  }
}

@media (prefers-reduced-motion: reduce) {
  .card-face.reveal,
  .reveal-hint {
    animation: none;
  }
}

.side-panel h3 {
  margin: 0 0 12px;
}

.stat {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  font-weight: 600;
}

.stat:last-child {
  border-bottom: none;
}

.stat span {
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
}
</style>
