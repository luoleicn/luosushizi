<template>
  <div class="app">
    <header class="top-bar">
      <div class="brand">
        <div class="brand-mark">字</div>
        <div>
          <h1>Hanzi Cards</h1>
          <p>Learn one character at a time</p>
        </div>
      </div>
      <nav class="nav">
        <router-link to="/study">学习</router-link>
        <router-link to="/input">录入</router-link>
        <router-link to="/stats">统计</router-link>
        <router-link v-if="!auth.user" to="/login">登录</router-link>
        <div v-else class="user-desktop">
          <span>{{ auth.user?.username }}</span>
          <button class="logout" @click="handleLogout">退出</button>
        </div>
      </nav>
    </header>
    <main class="content">
      <router-view />
    </main>
    <nav class="bottom-nav">
      <router-link to="/study">学习</router-link>
      <router-link to="/input">录入</router-link>
      <router-link to="/stats">统计</router-link>
      <router-link v-if="!auth.user" to="/login">登录</router-link>
      <div v-else class="user-pill">
        <span>{{ auth.user?.username }}</span>
        <button class="bottom-logout" @click="handleLogout">退出</button>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { api } from "./api/client";
import { getAuthState, logout } from "./store/auth";

const router = useRouter();
const auth = getAuthState();

const handleLogout = () => {
  logout();
  router.push("/login");
};

onMounted(() => {
  if (auth.token) {
    api.me();
  }
});
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr;
}

.top-bar {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: linear-gradient(120deg, rgba(255, 248, 235, 0.95), rgba(236, 245, 255, 0.9));
  border-bottom: 1px solid rgba(34, 34, 34, 0.1);
  position: sticky;
  top: 0;
  z-index: 10;
}

.content {
  padding: 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand h1 {
  margin: 0;
  font-size: 20px;
  letter-spacing: 0.5px;
}

.brand p {
  margin: 2px 0 0;
  font-size: 12px;
  opacity: 0.7;
}

.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-size: 22px;
  font-weight: 700;
  background: #f5d76e;
  box-shadow: 0 10px 20px rgba(245, 215, 110, 0.4);
}

.nav {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.nav a,
.nav a:visited {
  text-decoration: none;
  color: #1b1b1b;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.06);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.nav a.router-link-active {
  background: #1b1b1b;
  color: #fff;
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.18);
}

.logout {
  border: none;
  background: #ffedd1;
  color: #7a3a00;
  padding: 8px 12px;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 600;
}

.user-desktop {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.7);
  max-width: 160px;
}

.user-desktop span {
  display: inline-block;
  max-width: 90px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bottom-nav {
  display: none;
}

@media (max-width: 720px) {
  .top-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .content {
    padding: 16px;
  }

  .nav {
    display: none;
  }

  .bottom-nav {
    position: sticky;
    bottom: 0;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    padding: 12px 12px 18px;
    background: rgba(255, 247, 232, 0.95);
    border-top: 1px solid rgba(0, 0, 0, 0.08);
    backdrop-filter: blur(8px);
  }

  .bottom-nav a,
  .bottom-nav a:visited,
  .bottom-logout,
  .user-pill {
    text-decoration: none;
    color: #1b1b1b;
    background: #ffffff;
    border-radius: 14px;
    padding: 10px 0;
    text-align: center;
    font-weight: 600;
    border: 1px solid rgba(0, 0, 0, 0.06);
  }

  .bottom-nav a.router-link-active {
    background: #1b1b1b;
    color: #fff;
  }

  .bottom-logout {
    border: none;
    background: #ffedd1;
    color: #7a3a00;
    cursor: pointer;
  }

  .user-pill {
    display: grid;
    gap: 6px;
    padding: 8px 6px;
  }

  .user-pill span {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.6);
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
