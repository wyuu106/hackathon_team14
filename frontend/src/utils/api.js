import axios from "axios";

export const API_URL = import.meta.env.VITE_API_URL;

let accessToken = null;
let refreshPromise = null;
let authUpdateHandler = () => {};

export const publicApi = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

export const setApiAccessToken = (token) => {
  accessToken = token;
};

export const setAuthUpdateHandler = (handler) => {
  authUpdateHandler = handler;
};

export const refreshAccessToken = () => {
  if (!refreshPromise) {
    refreshPromise = publicApi.post("/auth/refresh")
      .then((response) => {
        accessToken = response.data.access_token;
        authUpdateHandler(response.data);
        return response.data.access_token;
      })
      .catch((error) => {
        accessToken = null;
        authUpdateHandler(null);
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
};

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status !== 401 || originalRequest?._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;
    try {
      const token = await refreshAccessToken();
      originalRequest.headers.Authorization = `Bearer ${token}`;
      return api(originalRequest);
    } catch {
      return Promise.reject(error);
    }
  },
);
