import React, { useState } from 'react';
import './App.css';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ChatProvider } from './contexts/ChatContext';
import { ThemeProvider } from './contexts/ThemeContext';
import Sidebar from './components/Sidebar';
import ChatbotInterface from './components/ChatbotInterface';
import FileManagement from './components/FileManagement';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';

type AppView = 'chat' | 'files';
type AuthView = 'login' | 'register';

/**
 * Main App Component (Inner)
 * 
 * Renders the main application interface after authentication
 */
function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentView, setCurrentView] = useState<AppView>('chat');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [authView, setAuthView] = useState<AuthView>('login');

  // Show loading spinner while checking auth state
  if (isLoading) {
    return (
      <div className="App loading min-h-screen flex items-center justify-center bg-background">
        <div className="loading-spinner text-center animate-fade-in">
          <div className="spinner-icon text-4xl mb-4 animate-bounce-light">🔄</div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <ChatProvider>
      <div className="App h-screen flex flex-row bg-background overflow-hidden">
        <Sidebar 
          currentView={currentView} 
          onViewChange={setCurrentView}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
        <div className="app-main-content flex-1 flex flex-col min-h-0 p-4 md:p-6 lg:p-8 overflow-hidden relative min-w-0">
            {isAuthenticated ? (
              currentView === 'chat' ? (
                <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
                  <ChatbotInterface />
                </div>
              ) : (
                <div className="flex-1 flex flex-col min-h-0 overflow-auto">
                  <FileManagement onSwitchToChat={() => setCurrentView('chat')} />
                </div>
              )
            ) : null}
            {/* Login/Register as overlay modal (no separate page) */}
            {!isAuthenticated && (
              <>
                <div className="auth-overlay" aria-hidden="true" />
                <div className="auth-modal-center">
                  {authView === 'register' ? (
                    <RegisterPage
                      embedded
                      onSwitchToLogin={() => setAuthView('login')}
                    />
                  ) : (
                    <LoginPage
                      embedded
                      onSwitchToRegister={() => setAuthView('register')}
                    />
                  )}
                </div>
              </>
            )}
          </div>
      </div>
    </ChatProvider>
  );
}

/**
 * Root App Component
 * 
 * Wraps the application with necessary providers
 */
function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;