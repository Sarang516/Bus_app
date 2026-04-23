import { createContext, useContext, useState, useEffect } from 'react';
import { loginUser } from '../utils/api';

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
      const data = await loginUser(pernr, password);

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
