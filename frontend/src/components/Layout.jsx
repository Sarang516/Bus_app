import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from './UI';

export const Layout = ({ children, page, setPage }) => {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleLogout = () => {
    logout();
    window.location.href = '/';
  };

  const navigationItems = [
    {
      label: 'Dashboard',
      page: 'dashboard',
      roles: ['EMPLOYEE', 'APPROVER', 'TRANSPORT_ADMIN'],
    },
    {
      label: 'My Requests',
      page: 'my-requests',
      roles: ['EMPLOYEE', 'APPROVER'],
    },
    {
      label: 'New Request',
      page: 'new-request',
      roles: ['EMPLOYEE'],
    },
    {
      label: 'Pending Approval',
      page: 'pending-approval',
      roles: ['APPROVER'],
    },
    {
      label: 'Employee Bus List',
      page: 'employee-allotment',
      roles: ['APPROVER'],
    },
    {
      label: 'All Requests',
      page: 'all-requests',
      roles: ['TRANSPORT_ADMIN'],
    },
    {
      label: 'Driver Master',
      page: 'driver-master',
      roles: ['TRANSPORT_ADMIN'],
    },
    {
      label: 'Vehicle Master',
      page: 'vehicle-master',
      roles: ['TRANSPORT_ADMIN'],
    },
    {
      label: 'Driver-Vehicle Map',
      page: 'driver-vehicle-map',
      roles: ['TRANSPORT_ADMIN'],
    },
    {
      label: 'Employee Master',
      page: 'employee-master',
      roles: ['TRANSPORT_ADMIN'],
    },
    {
      label: 'My Profile',
      page: 'profile',
      roles: ['EMPLOYEE', 'APPROVER', 'TRANSPORT_ADMIN'],
    },
  ];

  const visibleItems = navigationItems.filter(
    (item) => !item.roles || item.roles.includes(user?.role)
  );

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <button
          type="button"
          className="sidebar-brand sidebar-home"
          onClick={() => setPage('dashboard')}
        >
          <div className="brand-icon">🚌</div>
          <div>
            <div className="brand-title">Bus App</div>
            <div className="brand-sub">Transport Portal</div>
          </div>
        </button>

        <nav className="sidebar-nav">
          {visibleItems.map((item) => (
            <button
              key={item.page}
              type="button"
              className={`nav-item ${page === item.page ? 'active' : ''}`}
              onClick={() => setPage(item.page)}
            >
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button
            type="button"
            className="user-meta"
            style={{ background: "none", border: "none", cursor: "pointer", width: "100%", textAlign: "left", padding: 0 }}
            onClick={() => setPage("profile")}
            title="View My Profile"
          >
            <div className="user-avatar" style={{ overflow: "hidden", padding: 0 }}>
              {user?.profile_photo
                ? <img src={user.profile_photo} alt={user.ename} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                : user?.ename?.charAt(0) || 'U'
              }
            </div>
            <div>
              <div className="user-name">{user?.ename}</div>
              <div className="user-role">{user?.role}</div>
            </div>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="main-area">
        {/* Topbar */}
        <header className="topbar">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            ☰
          </button>
          <div className="topbar-title">Bus Transportation Booking System</div>
          <div className="topbar-meta">
            <span className="topbar-username">{user?.ename}</span>
            <Button
              onClick={handleLogout}
              variant="danger"
              size="small"
              className="topbar-logout"
            >
              🚪 Logout
            </Button>
          </div>
        </header>

        {/* Page Content */}
        <main className="page-content">{children}</main>
      </div>
    </div>
  );
};
