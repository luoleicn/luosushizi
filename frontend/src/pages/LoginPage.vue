<template>
  <section class="page">
    <h2>欢迎回来</h2>
    <p>用大人准备好的账号登录，我们一起开始识字吧。</p>
    <div class="panel login-panel">
      <label class="field">
        <span>账号</span>
        <input v-model="username" type="text" placeholder="请输入账号" />
      </label>
      <label class="field">
        <span>密码</span>
        <div class="password-field">
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="请输入密码"
          />
          <button type="button" class="toggle" @click="showPassword = !showPassword">
            <span class="sr-only">{{ showPassword ? "隐藏密码" : "显示密码" }}</span>
            <svg v-if="showPassword" viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M2 12s3.8-6 10-6 10 6 10 6-3.8 6-10 6-10-6-10-6Z"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
              />
              <circle cx="12" cy="12" r="3.5" fill="none" stroke="currentColor" stroke-width="1.6" />
            </svg>
            <svg v-else viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M3 5l18 14M2 12s3.8-6 10-6c2.1 0 3.9.5 5.4 1.2M22 12s-3.8 6-10 6c-2.1 0-3.9-.5-5.4-1.2"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
        </div>
      </label>
      <button class="btn btn-secondary" :disabled="loading" @click="handleLogin">
        {{ loading ? "正在登录..." : "登录" }}
      </button>
      <p v-if="error" class="notice error">登录没成功，再试一次吧。</p>
    </div>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api/client";
import { setAuth } from "../store/auth";
import { loadDictionaries } from "../store/dictionary";

const router = useRouter();
const username = ref("");
const password = ref("");
const showPassword = ref(false);
const error = ref("");
const loading = ref(false);

const handleLogin = async () => {
  error.value = "";
  loading.value = true;
  try {
    const response = await api.login({
      username: username.value.trim(),
      password: password.value,
    });
    setAuth(response.access_token, response.user);
    await loadDictionaries();
    router.push("/study");
  } catch (err) {
    error.value = err.message || "Login failed.";
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-panel {
  max-width: 420px;
  display: grid;
  gap: 16px;
}

.field {
  display: grid;
  gap: 8px;
  font-weight: 600;
}

.field span {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.7);
}

.field input {
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  font-size: 16px;
}

.password-field {
  display: flex;
  gap: 8px;
  align-items: center;
}

.password-field input {
  flex: 1;
}

.toggle {
  border: none;
  background: rgba(0, 0, 0, 0.08);
  color: rgba(0, 0, 0, 0.7);
  padding: 10px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
}

.toggle svg {
  width: 20px;
  height: 20px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

</style>
