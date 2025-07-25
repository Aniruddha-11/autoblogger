import React from 'react';
import './App.css';
import KeywordInput from './components/KeywordInput';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Smart Weld Blog Generator</h1>
      </header>
      <main>
        <KeywordInput />
      </main>
    </div>
  );
}

export default App;