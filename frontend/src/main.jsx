import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './pages/App';
import { AuthProvider } from './context/AuthContext';
import './styles/global.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('App error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', height: '100vh', padding: 32,
          fontFamily: 'sans-serif', background: '#f9fafb',
        }}>
          <div style={{
            background: 'white', borderRadius: 12, padding: 40,
            maxWidth: 480, width: '100%', boxShadow: '0 4px 24px rgba(0,0,0,.08)',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
            <h2 style={{ margin: '0 0 8px', color: '#111827' }}>Something went wrong</h2>
            <p style={{ color: '#6b7280', marginBottom: 24 }}>
              An unexpected error occurred. Please refresh the page.
            </p>
            <button
              onClick={() => window.location.reload()}
              style={{
                background: '#1a56a0', color: 'white', border: 'none',
                borderRadius: 8, padding: '10px 24px', fontSize: 15,
                fontWeight: 600, cursor: 'pointer',
              }}
            >
              Refresh Page
            </button>
            {import.meta.env.DEV && (
              <pre style={{
                marginTop: 24, padding: 12, background: '#fef2f2',
                borderRadius: 6, fontSize: 11, color: '#b91c1c',
                textAlign: 'left', overflow: 'auto', maxHeight: 200,
              }}>
                {this.state.error?.toString()}
              </pre>
            )}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <AuthProvider>
        <App />
      </AuthProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
