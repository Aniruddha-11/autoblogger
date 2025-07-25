class SessionManager {
  constructor() {
    this.SESSION_KEY = 'shothik_blog_session';
    this.BATCH_SESSION_KEY = 'shothik_batch_session';
  }

  // Manual Mode Session Management
  saveManualSession(sessionData) {
    const session = {
      ...sessionData,
      timestamp: Date.now(),
      mode: 'manual'
    };
    localStorage.setItem(this.SESSION_KEY, JSON.stringify(session));
    console.log('Manual session saved:', session);
  }

  getManualSession() {
    try {
      const session = localStorage.getItem(this.SESSION_KEY);
      if (session) {
        const parsed = JSON.parse(session);
        // Check if session is not too old (24 hours)
        if (Date.now() - parsed.timestamp < 24 * 60 * 60 * 1000) {
          return parsed;
        } else {
          this.clearManualSession();
        }
      }
    } catch (error) {
      console.error('Error loading manual session:', error);
      this.clearManualSession();
    }
    return null;
  }

  clearManualSession() {
    localStorage.removeItem(this.SESSION_KEY);
  }

  // Batch Mode Session Management
  saveBatchSession(sessionData) {
    const session = {
      ...sessionData,
      timestamp: Date.now(),
      mode: 'batch'
    };
    localStorage.setItem(this.BATCH_SESSION_KEY, JSON.stringify(session));
    console.log('Batch session saved:', session);
  }

  getBatchSession() {
    try {
      const session = localStorage.getItem(this.BATCH_SESSION_KEY);
      if (session) {
        const parsed = JSON.parse(session);
        // Check if session is not too old (24 hours)
        if (Date.now() - parsed.timestamp < 24 * 60 * 60 * 1000) {
          return parsed;
        } else {
          this.clearBatchSession();
        }
      }
    } catch (error) {
      console.error('Error loading batch session:', error);
      this.clearBatchSession();
    }
    return null;
  }

  clearBatchSession() {
    localStorage.removeItem(this.BATCH_SESSION_KEY);
  }

  // General session info
  getActiveSession() {
    const manual = this.getManualSession();
    const batch = this.getBatchSession();
    
    if (manual && batch) {
      // Return the most recent one
      return manual.timestamp > batch.timestamp ? manual : batch;
    }
    
    return manual || batch;
  }

  clearAllSessions() {
    this.clearManualSession();
    this.clearBatchSession();
  }

  // Step-specific session updates
  updateManualStep(keywordId, step, data = {}) {
    const existing = this.getManualSession() || {};
    this.saveManualSession({
      ...existing,
      keywordId,
      currentStep: step,
      stepData: {
        ...existing.stepData,
        [step]: data
      }
    });
  }

  updateBatchStep(jobId, status, data = {}) {
    const existing = this.getBatchSession() || {};
    this.saveBatchSession({
      ...existing,
      jobId,
      status,
      ...data
    });
  }
}

export default new SessionManager();