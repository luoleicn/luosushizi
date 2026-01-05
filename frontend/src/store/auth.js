import { reactive } from "vue";
import { clearToken, getToken, getUser, setToken } from "../api/client";

const authState = reactive({
  token: getToken(),
  user: getUser(),
});

export function getAuthState() {
  return authState;
}

export function setAuth(token, user) {
  setToken(token, user);
  authState.token = token;
  authState.user = user;
}

export function logout() {
  clearToken();
  authState.token = null;
  authState.user = null;
}

export function refreshAuth() {
  authState.token = getToken();
  authState.user = getUser();
}
