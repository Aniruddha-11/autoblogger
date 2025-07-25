import React, { useState, useEffect } from 'react';
import './App.css';
import KeywordInput from './components/KeywordInput';
import BatchUpload from './components/BatchUpload';
import SessionManager from './utils/SessionManager';

function App() {
  const [mode, setMode] = useState('manual');
  const [isRestoring, setIsRestoring] = useState(true);

  useEffect(() => {
    // Restore session on app load
    const restoreSession = async () => {
      try {
        const activeSession = SessionManager.getActiveSession();
        
        if (activeSession) {
          console.log('Restoring session:', activeSession);
          setMode(activeSession.mode);
          
          // Add a small delay to show restoration
          setTimeout(() => {
            setIsRestoring(false);
          }, 500);
        } else {
          setIsRestoring(false);
        }
      } catch (error) {
        console.error('Error restoring session:', error);
        setIsRestoring(false);
      }
    };

    restoreSession();
  }, []);

  const handleModeChange = (newMode) => {
    // If switching modes, ask for confirmation if there's an active session
    const activeSession = SessionManager.getActiveSession();
    
    if (activeSession && activeSession.mode !== newMode) {
      const confirmed = window.confirm(
        `You have an active ${activeSession.mode} session. Switching modes will clear your current progress. Continue?`
      );
      
      if (!confirmed) {
        return;
      }
    }
    
    // Clear sessions when switching modes
    if (newMode !== mode) {
      SessionManager.clearAllSessions();
    }
    
    setMode(newMode);
  };

  if (isRestoring) {
    return (
      <div className="App">
        <header className="App-header">
          <h1>Shothik.AI Blog Generator</h1>
        </header>
        <main>
          <div className="session-restore">
            <div className="spinner-large"></div>
            <p>Restoring your session...</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Shothik.AI Blog Generator</h1>
        <div className="mode-selector">
          <button 
            className={`mode-btn ${mode === 'manual' ? 'active' : ''}`}
            onClick={() => handleModeChange('manual')}
          >
            📝 Manual Mode
          </button>
          <button 
            className={`mode-btn ${mode === 'batch' ? 'active' : ''}`}
            onClick={() => handleModeChange('batch')}
          >
            🚀 Batch Mode
          </button>
        </div>
      </header>
      <main>
        {mode === 'manual' ? <KeywordInput /> : <BatchUpload />}
      </main>
    </div>
  );
}

export default App;