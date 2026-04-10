import axios from 'axios';

// In local dev, VITE_API_URL is http://localhost:5000
// The Vite proxy forwards /api/* to Flask, so we just use '' (same origin)
// for local and the full URL for production.
const API_BASE = import.meta.env.VITE_API_URL || '';
console.log("[Axios] Initializing. VITE_API_URL =", import.meta.env.VITE_API_URL, "API_BASE =", API_BASE);

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,          // send cookies (JWT)
  headers: { 'Content-Type': 'application/json' },
});

export default api;
export { API_BASE };
