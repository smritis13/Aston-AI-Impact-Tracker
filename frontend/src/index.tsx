import App from './App';
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

try {
  localStorage.removeItem('loaderEnable');
  document.documentElement.setAttribute('loader', 'disable');
  document.getElementById('loader')?.remove();
} catch {
  document.documentElement.setAttribute('loader', 'disable');
}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
   <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
