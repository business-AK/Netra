import React, { useState, useEffect } from 'react';
import { X, Cpu, Server, Key, Save, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';
import { VLMSettings } from '../types/chat';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (settings: VLMSettings) => void;
  currentSettings: VLMSettings;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  onSave,
  currentSettings,
}) => {
  const [provider, setProvider] = useState(currentSettings.provider || 'ollama');
  const [model, setModel] = useState(currentSettings.model || 'qwen2.5-vl:7b');
  const [baseUrl, setBaseUrl] = useState(currentSettings.baseUrl || 'http://localhost:11434');
  const [apiKey, setApiKey] = useState(currentSettings.apiKey || '');
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setProvider(currentSettings.provider || 'ollama');
      setModel(currentSettings.model || 'qwen2.5-vl:7b');
      setBaseUrl(currentSettings.baseUrl || 'http://localhost:11434');
      setApiKey(currentSettings.apiKey || '');
      setSavedSuccess(false);
    }
  }, [isOpen, currentSettings]);

  if (!isOpen) return null;

  const handleProviderChange = (p: string) => {
    setProvider(p);
    if (p === 'ollama') {
      setModel('qwen2.5-vl:7b');
      setBaseUrl('http://localhost:11434');
    } else if (p === 'gemini') {
      setModel('gemini-2.0-flash');
      setBaseUrl('https://generativelanguage.googleapis.com');
    } else if (p === 'groq') {
      setModel('llama-3.2-11b-vision-preview');
      setBaseUrl('https://api.groq.com/openai/v1');
    } else if (p === 'lmstudio') {
      setModel('local-model');
      setBaseUrl('http://localhost:1234/v1');
    } else if (p === 'openai') {
      setModel('gpt-4o-mini');
      setBaseUrl('https://api.openai.com/v1');
    } else if (p === 'openrouter') {
      setModel('qwen/qwen-2.5-vl-72b-instruct:free');
      setBaseUrl('https://openrouter.ai/api/v1');
    }
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ provider, model, baseUrl, apiKey });
    setSavedSuccess(true);
    setTimeout(() => {
      onClose();
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-100 text-base">Inference & VLM Engine</h3>
              <p className="text-xs text-slate-400">Choose between local offline models or hosted providers</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Select LLM / VLM Provider
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'ollama', label: 'Local Ollama', badge: 'Offline' },
                { id: 'gemini', label: 'Google Gemini', badge: 'Fast/Free' },
                { id: 'groq', label: 'Groq Vision', badge: 'Ultra-fast' },
                { id: 'lmstudio', label: 'LM Studio', badge: 'Local' },
                { id: 'openai', label: 'OpenAI', badge: 'Cloud' },
                { id: 'openrouter', label: 'OpenRouter', badge: 'Cloud' },
              ].map((item) => (
                <button
                  type="button"
                  key={item.id}
                  onClick={() => handleProviderChange(item.id)}
                  className={`px-2.5 py-2 text-xs font-medium rounded-xl border transition flex flex-col items-center justify-center gap-0.5 ${
                    provider === item.id
                      ? 'bg-indigo-600/25 border-indigo-500 text-indigo-200 shadow-sm'
                      : 'bg-slate-800/40 border-slate-700/60 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <span className="font-semibold">{item.label}</span>
                  <span className="text-[9px] text-slate-400 font-mono">{item.badge}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1.5">
              <Server className="w-3.5 h-3.5 text-indigo-400" /> Vision-Language Model Identifier
            </label>
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="e.g. qwen2.5-vl:7b, gemini-2.0-flash, llama-3.2-11b-vision-preview"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              API Base URL
            </label>
            <input
              type="url"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="http://localhost:11434"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-indigo-400" /> API Key
              </span>
              {(provider === 'ollama' || provider === 'lmstudio') && (
                <span className="text-[10px] text-emerald-400 font-normal">Not needed for local models</span>
              )}
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={
                provider === 'ollama' || provider === 'lmstudio'
                  ? 'No API key needed for local offline models'
                  : provider === 'gemini'
                  ? 'AIzaSy...'
                  : provider === 'groq'
                  ? 'gsk_...'
                  : 'sk-...'
              }
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            />
          </div>

          <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              Settings persist in your browser.
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-slate-100 hover:bg-slate-800 rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-lg shadow-indigo-600/20 transition active:scale-95"
              >
                {savedSuccess ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-300" />
                    <span>Saved!</span>
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    <span>Save Settings</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
