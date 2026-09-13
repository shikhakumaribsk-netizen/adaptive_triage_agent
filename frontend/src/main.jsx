import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

// Hide the initial loader once React is ready
const hideLoader = () => {
  const loader = document.getElementById('initial-loader');
  if (loader) {
    loader.classList.add('hidden');
    // Remove from DOM after transition
    setTimeout(() => loader.remove(), 400);
  }
};

const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Hide loader after first render
hideLoader();