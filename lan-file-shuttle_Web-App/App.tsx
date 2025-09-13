
import React, { useState } from 'react';
import { SenderView } from './components/SenderView';
import { ReceiverView } from './components/ReceiverView';
import { HomeIcon, UploadIcon, DownloadIcon } from './constants';
import type { AppView } from './types';

const App: React.FC = () => {
  const [view, setView] = useState<AppView>('home');

  const renderView = () => {
    switch (view) {
      case 'sender':
        return <SenderView />;
      case 'receiver':
        return <ReceiverView />;
      default:
        return (
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-200 mb-2">Welcome to LAN File Shuttle</h2>
            <p className="text-gray-400 mb-8">Choose your role to begin a simulated transfer.</p>
            <div className="flex flex-col md:flex-row justify-center gap-6">
              <button
                onClick={() => setView('sender')}
                className="flex items-center justify-center gap-3 bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-lg shadow-lg transition-transform transform hover:scale-105"
              >
                <UploadIcon />
                Send Files
              </button>
              <button
                onClick={() => setView('receiver')}
                className="flex items-center justify-center gap-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-4 px-6 rounded-lg shadow-lg transition-transform transform hover:scale-105"
              >
                <DownloadIcon />
                Receive Files
              </button>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="bg-gray-900 min-h-screen text-white p-4 sm:p-6 md:p-8 flex flex-col items-center">
      <div className="w-full max-w-4xl">
        <header className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <svg className="w-10 h-10 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-100">LAN File Shuttle</h1>
          </div>
          {view !== 'home' && (
            <button
              onClick={() => setView('home')}
              className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
            >
              <HomeIcon />
              Home
            </button>
          )}
        </header>
        <main className="bg-gray-800 rounded-xl shadow-2xl p-6 sm:p-8">
          {renderView()}
        </main>
        <footer className="text-center mt-8 text-gray-500 text-sm">
          <p>&copy; 2024 LAN File Shuttle. All rights reserved. This is a UI simulation.</p>
        </footer>
      </div>
    </div>
  );
};

export default App;
