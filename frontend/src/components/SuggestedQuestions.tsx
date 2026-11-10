import React from 'react';
import { Sparkles } from 'lucide-react';

interface SuggestedQuestionsProps {
  onSelectQuestion: (question: string) => void;
}

const DEFAULT_QUESTIONS = [
  'Summarize this video.',
  'What are the key events in chronological order?',
  'What main objects and people appear in the video?',
  'What happens at the beginning of the video?',
  'Is there any conversation about a specific topic?',
];

export const SuggestedQuestions: React.FC<SuggestedQuestionsProps> = ({ onSelectQuestion }) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
        <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
        <span>Suggested Inquiries</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {DEFAULT_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            onClick={() => onSelectQuestion(q)}
            className="text-xs bg-slate-800/60 hover:bg-slate-800 text-slate-300 hover:text-white px-3 py-1.5 rounded-xl border border-slate-700/60 transition text-left active:scale-95"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
};

