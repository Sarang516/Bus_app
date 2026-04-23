import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach JWT ──────────────────────────────────────────
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response interceptor: extract error detail + handle 401 ──────────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const detail = error.response?.data?.detail;

    // Session expired or invalid token → force logout
    if (status === 401) {
      const isAuthRoute = error.config?.url?.includes('/auth/login') ||
                          error.config?.url?.includes('/auth/register');
      if (!isAuthRoute) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/';
      }
    }

    if (detail) {
      error.message = typeof detail === 'string' ? detail : JSON.stringify(detail);
    }
    return Promise.reject(error);
  }
);

const unwrap = (req) => req.then((r) => r.data);

// ── Auth ──────────────────────────────────────────────────────────────────────
export const loginUser            = (pernr, password) => unwrap(apiClient.post('/auth/login', { pernr, password }));
export const registerUser         = (data)            => unwrap(apiClient.post('/auth/register', data));
export const adminAddEmployee     = (data)            => unwrap(apiClient.post('/auth/admin/add-employee', data));
export const getEmployeeProfile   = (pernr)           => unwrap(apiClient.get(`/auth/employee/${pernr}`));

// ── Employees ─────────────────────────────────────────────────────────────────
export const listEmployees            = (params = {}) => unwrap(apiClient.get('/employees/', { params }));
export const listEmployeesWithAllotment = ()          => unwrap(apiClient.get('/employees/with-allotment'));
export const getEmployee              = (pernr)       => unwrap(apiClient.get(`/employees/${pernr}`));
export const updateEmployeeProfile    = (pernr, data) => unwrap(apiClient.put(`/employees/${pernr}`, data));

// ── Drivers ───────────────────────────────────────────────────────────────────
export const listDrivers   = (params = {}) => unwrap(apiClient.get('/drivers/', { params }));
export const getDriver     = (id)          => unwrap(apiClient.get(`/drivers/${id}`));
export const createDriver  = (data)        => unwrap(apiClient.post('/drivers/', data));
export const updateDriver  = (id, data)    => unwrap(apiClient.put(`/drivers/${id}`, data));
export const deleteDriver  = (id)          => unwrap(apiClient.delete(`/drivers/${id}`));

// ── Vehicles ──────────────────────────────────────────────────────────────────
export const listVehicles  = (params = {}) => unwrap(apiClient.get('/vehicles/', { params }));
export const getVehicle    = (no)          => unwrap(apiClient.get(`/vehicles/${no}`));
export const createVehicle = (data)        => unwrap(apiClient.post('/vehicles/', data));
export const updateVehicle = (no, data)    => unwrap(apiClient.put(`/vehicles/${no}`, data));
export const deleteVehicle = (no)          => unwrap(apiClient.delete(`/vehicles/${no}`));

// ── Routes ────────────────────────────────────────────────────────────────────
export const listRoutes    = ()       => unwrap(apiClient.get('/routes/'));
export const listPickups   = (seqnr)  => unwrap(apiClient.get(`/routes/${seqnr}/pickups`));
export const getRoutePickups = listPickups;

// ── Mappings ──────────────────────────────────────────────────────────────────
export const listMappings       = ()     => unwrap(apiClient.get('/mappings/'));
export const listActiveMappings = ()     => unwrap(apiClient.get('/mappings/', { params: { active_only: true } }));
export const createMapping      = (data) => unwrap(apiClient.post('/mappings/', data));
export const deleteMapping      = (id)   => unwrap(apiClient.delete(`/mappings/${id}`));

// ── Requests ──────────────────────────────────────────────────────────────────
export const createRequest      = (data)           => unwrap(apiClient.post('/requests/', data));
export const adminDirectAllot   = (data)           => unwrap(apiClient.post('/requests/admin-allot', data));
export const updateRequest      = (reqid, data)    => unwrap(apiClient.put(`/requests/${reqid}`, data));
export const getRequest         = (reqid)          => unwrap(apiClient.get(`/requests/${reqid}`));
export const getRequestLogs     = (reqid)          => unwrap(apiClient.get(`/requests/${reqid}/logs`));
export const updateRequestAction = (reqid, action, data = {}) =>
  unwrap(apiClient.put(`/requests/${reqid}/action`, { action, ...data }));
export const takeAction = (reqid, data = {}) => updateRequestAction(reqid, data.action, data);

export const listRequests = (pernr = null, role = null, extraParams = {}) => {
  const params = { ...extraParams };
  if (pernr) params.pernr = pernr;
  if (role)  params.role  = role;
  return unwrap(apiClient.get('/requests/', { params }));
};

// ── File Uploads ──────────────────────────────────────────────────────────────
export const uploadFile = (file) => {
  const form = new FormData();
  form.append('file', file);
  return unwrap(
    apiClient.post('/uploads/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  );
};

export const getFileUrl = (fileId) => `${API_BASE_URL}/uploads/${fileId}`;

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const getDashboard   = ()      => unwrap(apiClient.get('/dashboard/'));
export const getMyDashboard = (pernr) => unwrap(apiClient.get(`/dashboard/my/${pernr}`));

// ── Health ────────────────────────────────────────────────────────────────────
export const getHealth = () => unwrap(apiClient.get('/health'));

export const api = {
  loginUser, registerUser, adminAddEmployee, getEmployeeProfile,
  listEmployees, listEmployeesWithAllotment, getEmployee, updateEmployeeProfile,
  listDrivers, getDriver, createDriver, updateDriver, deleteDriver,
  listVehicles, getVehicle, createVehicle, updateVehicle, deleteVehicle,
  listRoutes, listPickups, getRoutePickups,
  listMappings, listActiveMappings, createMapping, deleteMapping,
  createRequest, adminDirectAllot, updateRequest, getRequest,
  getRequestLogs, updateRequestAction, takeAction, listRequests,
  uploadFile, getFileUrl,
  getDashboard, getMyDashboard, getHealth,
};

export default apiClient;
