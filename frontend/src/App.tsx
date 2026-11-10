import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { SettingsModal } from './components/SettingsModal';
import { Home } from './pages/Home';
import { VideoWorkspace } from './pages/VideoWorkspace';
import { VLMSettings } from './types/chat';

const DEFAULT_VLM_SETTINGS: VLMSettings = {
  provider: 'ollama',
  model: 'qwen2.5-vl:7b',
  baseUrl: 'http://localhost:11434',
  apiKey: '',
};

export function App() {
  const [activeVideoId, setActiveVideoId] = useState<string | null>(null);
  const [activeVideoTitle, setActiveVideoTitle] = useState<string | undefined>(undefined);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  const [vlmSettings, setVlmSettings] = useState<VLMSettings>(() => {
    try {
      const saved = localStorage.getItem('netra_vlm_settings');
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error('Failed to parse saved settings:', e);
    }
    return DEFAULT_VLM_SETTINGS;
  });

  const handleSaveSettings = (newSettings: VLMSettings) => {
    setVlmSettings(newSettings);
    try {
      localStorage.setItem('netra_vlm_settings', JSON.stringify(newSettings));
    } catch (e) {
      console.error('Failed to save settings:', e);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      <Header
        onOpenSettings={() => setIsSettingsOpen(true)}
        onGoHome={() => setActiveVideoId(null)}
        activeVideoTitle={activeVideoTitle}
      />

      <main className="flex-1 flex flex-col">
        {activeVideoId ? (
          <VideoWorkspace
            videoId={activeVideoId}
            onBack={() => setActiveVideoId(null)}
            vlmSettings={vlmSettings}
          />
        ) : (
          <Home
            onSelectVideo={(id) => {
              setActiveVideoId(id);
            }}
          />
        )}
      </main>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSave={handleSaveSettings}
        currentSettings={vlmSettings}
      />
    </div>
  );
}

export default App;

