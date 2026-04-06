// src/utils/auth.jsx — Authentication helpers (clean, no dev bypass)

export const login = async (username, password) => {
  // Handled via api.js authAPI.login() in the Login component
  // This module only manages localStorage token/user state
  return true;
};

export const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
};

export const getToken = () => {
  return localStorage.getItem("token");
};

export const getUser = () => {
  const user = localStorage.getItem("user");
  return user ? JSON.parse(user) : null;
};

export const isAuthenticated = () => {
  return localStorage.getItem("token") !== null;
};

export const saveAuth = (token, user) => {
  localStorage.setItem("token", token);
  localStorage.setItem("user", JSON.stringify(user));
};
