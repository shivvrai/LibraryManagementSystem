// src/utils/api.js
import { getToken } from "./auth";

export const API_BASE = import.meta.env.DEV
  ? "/api"
  : import.meta.env.VITE_API_URL || "/api";

export async function apiCall(endpoint, options = {}) {
  if (!endpoint || typeof endpoint !== "string")
    throw new Error("apiCall: endpoint must be a string");

  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = `${API_BASE}${path}`;
  const token = getToken();

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const config = {
    method: options.method || "GET",
    headers,
    ...(options.body !== undefined
      ? {
          body:
            typeof options.body === "string"
              ? options.body
              : JSON.stringify(options.body),
        }
      : {}),
  };

  try {
    const res = await fetch(url, config);
    const text = await res.text();
    const data = text ? JSON.parse(text) : null;

    if (!res.ok) {
      const errMsg =
        (data && (data.error || data.message || data.detail)) ||
        `API Error: ${res.status} ${res.statusText}`;
      const err = new Error(errMsg);
      err.status = res.status;
      err.raw = data;
      throw err;
    }

    return data;
  } catch (err) {
    if (err instanceof SyntaxError) {
      throw new Error("Invalid JSON response from server");
    }
    throw err;
  }
}

/* ===== authAPI ===== */
export const authAPI = {
  login: (credentials) =>
    apiCall("/auth/login", { method: "POST", body: credentials }),
  register: (payload) =>
    apiCall("/auth/register", { method: "POST", body: payload }),
  checkUsername: (username) =>
    apiCall("/auth/check-username", { method: "POST", body: { username } }),
};

/* ===== adminAPI ===== */
export const adminAPI = {
  getBooks: async () => {
    const res = await apiCall("/admin/books");
    return res.items || res;
  },
  addBook: (book) => apiCall("/admin/books", { method: "POST", body: book }),
  updateBook: (id, book) =>
    apiCall(`/admin/books/${id}`, { method: "PUT", body: book }),
  increaseBookQty: (id, amount = 1) =>
    apiCall(`/admin/books/${id}/increase?amount=${amount}`, {
      method: "PATCH",
    }),
  decreaseBookQty: (id, amount = 1) =>
    apiCall(`/admin/books/${id}/decrease?amount=${amount}`, {
      method: "PATCH",
    }),
  getStudents: async () => {
    const res = await apiCall("/admin/students");
    return res.items || res;
  },
  searchStudents: async (query) => {
    const res = await apiCall(
      `/admin/students?search=${encodeURIComponent(query)}`,
    );
    return res.items || res;
  },
  addStudent: (payload) =>
    apiCall("/admin/students", { method: "POST", body: payload }),
  updateStudent: (id, payload) =>
    apiCall(`/admin/students/${id}`, { method: "PUT", body: payload }),
  deleteStudent: (id, force = false) =>
    apiCall(`/admin/students/${id}?force=${force}`, { method: "DELETE" }),
  getTransactions: () => apiCall("/admin/transactions"),
  getOverdue: () => apiCall("/admin/overdue"),
  processReturn: (transactionId) =>
    apiCall(`/admin/return/${transactionId}`, { method: "POST" }),
  getStats: () => apiCall("/admin/stats"),

  // Book Copies
  getBookCopies: (bookId) => apiCall(`/admin/books/${bookId}/copies`),

  // Reservations
  getReservations: () => apiCall("/admin/reservations"),
  getBookReservations: (bookId) =>
    apiCall(`/admin/books/${bookId}/reservations`),

  // Profile / Settings
  getProfile: () => apiCall("/admin/profile"),
  updateProfile: (data) =>
    apiCall("/admin/profile", { method: "PUT", body: data }),
};

/* ===== studentAPI ===== */
export const studentAPI = {
  getBooks: () => apiCall("/student/books"),
  getMyBooks: () => apiCall("/student/my-books"),
  getFines: () => apiCall("/student/fines"),
  borrowBook: (bookId) =>
    apiCall("/student/borrow", { method: "POST", body: { book_id: bookId } }),
  returnBook: (transactionId) =>
    apiCall(`/student/return/${transactionId}`, { method: "POST" }),

  // Renewals
  renewBook: (transactionId) =>
    apiCall(`/student/renew/${transactionId}`, { method: "POST" }),

  // Reservations
  reserveBook: (bookId) =>
    apiCall("/student/reserve", { method: "POST", body: { book_id: bookId } }),
  cancelReservation: (reservationId) =>
    apiCall(`/student/reserve/${reservationId}`, { method: "DELETE" }),
  getReservations: () => apiCall("/student/reservations"),

  // Notifications
  getNotifications: () => apiCall("/student/notifications"),
  getUnreadCount: () => apiCall("/student/notifications/unread-count"),
  markNotificationRead: (id) =>
    apiCall(`/student/notifications/${id}/read`, { method: "PATCH" }),
  markAllNotificationsRead: () =>
    apiCall("/student/notifications/read-all", { method: "PATCH" }),

  // Preferences
  getPreferences: () => apiCall("/student/preferences"),
  addPreference: (data) =>
    apiCall("/student/preferences", { method: "POST", body: data }),
  removePreference: (id) =>
    apiCall(`/student/preferences/${id}`, { method: "DELETE" }),

  // Profile / Settings
  getProfile: () => apiCall("/student/profile"),
  updateProfile: (data) =>
    apiCall("/student/profile", { method: "PUT", body: data }),
};

export default { apiCall, authAPI, adminAPI, studentAPI, API_BASE };
