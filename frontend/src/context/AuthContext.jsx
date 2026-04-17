import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser]       = useState(null);
  const [token, setToken]     = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError]     = useState(null);

  // Restore session from localStorage on mount
  useEffect(() => {
    const savedUser  = localStorage.getItem('user');
    const savedToken = localStorage.getItem('token');
    if (savedUser && savedToken) {
      setUser(JSON.parse(savedUser));
      setToken(savedToken);
    }
  }, []);

  const _persistSession = (userData, accessToken) => {
    setUser(userData);
    setToken(accessToken);
    localStorage.setItem('user',  JSON.stringify(userData));
    localStorage.setItem('token', accessToken);
  };

  // ── Login ──────────────────────────────────────────────────────────────────
  const login = async (pernr, password) => {
    setIsLoading(true); setError(null);
    try {
      const response = await fetch('/api/auth/login', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ pernr, password }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Login failed. Check credentials.');
      }

      const data = await response.json();
      const userData = {
        pernr:         data.pernr,
        ename:         data.ename,
        role:          data.role,
        designation:   data.designation,
        department:    data.department,
        address:       data.address       || null,
        email:         data.email         || null,
        mobile_no:     data.mobile_no     || null,
        profile_photo: data.profile_photo || null,
      };

      _persistSession(userData, data.access_token);
      return userData;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // ── Self-Register ──────────────────────────────────────────────────────────
  const register = async (formData) => {
    setIsLoading(true); setError(null);
    try {
      const response = await fetch('/api/auth/register', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(formData),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Registration failed.');
      }

      const data = await response.json();
      const userData = {
        pernr:         data.pernr,
        ename:         data.ename,
        role:          data.role,
        designation:   data.designation,
        department:    data.department,
        address:       data.address       || null,
        email:         data.email         || null,
        mobile_no:     data.mobile_no     || null,
        profile_photo: data.profile_photo || null,
      };

      _persistSession(userData, data.access_token);
      return userData;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // ── Update user profile in context + localStorage ─────────────────────────
  const updateUser = (updatedFields) => {
    const merged = { ...user, ...updatedFields };
    setUser(merged);
    localStorage.setItem('user', JSON.stringify(merged));
  };

  // ── Logout ─────────────────────────────────────────────────────────────────
  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  };

  const value = {
    user,
    token,
    isLoading,
    error,
    login,
    register,
    logout,
    updateUser,
    getUser: () => user,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
