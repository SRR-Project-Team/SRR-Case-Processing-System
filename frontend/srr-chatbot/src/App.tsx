import React from 'react';
import { Routes, Route } from 'react-router-dom';
import './App.css';
import ChatbotInterface from './components/ChatbotInterface';
import UserProfile from './components/UserProfile';
import Login from './components/Login';

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/*" element={<ChatbotInterface />} />
        <Route path='/profile' element={<UserProfile />} />
      </Routes>
    </div>
  );
}

export default App;