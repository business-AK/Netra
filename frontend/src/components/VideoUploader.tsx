import React, { useState, useRef } from 'react';
import { UploadCloud, Film, AlertCircle, FileCheck2, Loader2, Sparkles } from 'lucide-react';
import { api } from '../services/api';
import { VideoStatus } from '../types/video';

interface VideoUploaderProps {
  onUploadSuccess: (status: VideoStatus) => void;
}

export const VideoUploader: React.FC<VideoUploaderProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const supportedFormats = ['MP4', 'MKV', 'MOV', 'AVI', 'WEBM'];

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    const validExtensions = ['mp4', 'mkv', 'mov', 'avi', 'webm'];

    if (!ext || !validExtensions.includes(ext)) {
      setErrorMessage(`Unsupported format .${ext}. Please upload MP4, MKV, MOV, AVI, or WEBM.`);
      return;
    }

    setErrorMessage(null);
    setIsUploading(true);
    setUploadProgress(0);

    try {
      const result = await api.uploadVideo(file, (progressEvent) => {
        if (progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percent);
        }
      });
      onUploadSuccess(result);
    } catch (err: any) {
      console.error('Upload failed:', err);
      setErrorMessage(err?.response?.data?.detail || err.message || 'Video upload failed.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Upload Box */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-3xl p-10 md:p-14 text-center cursor-pointer transition-all duration-200 backdrop-blur-md overflow-hidden ${
          isDragging
            ? 'border-indigo-500 bg-indigo-950/30 scale-[1.01] shadow-2xl shadow-indigo-500/20'
            : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 hover:bg-slate-900/60 shadow-xl'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".mp4,.mkv,.mov,.avi,.webm"
          className="hidden"
          onChange={handleFileSelect}
          disabled={isUploading}
        />

        {/* Ambient glow in background */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-80 h-32 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col items-center">
          {isUploading ? (
            <div className="w-full max-w-md py-6 space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center mx-auto animate-pulse">
                <Loader2 className="w-8 h-8 animate-spin" />
              </div>
              <div className="space-y-1">
                <h4 className="text-base font-semibold text-slate-100">Uploading Video File...</h4>
                <p className="text-xs text-slate-400">Transferring file to backend storage ({uploadProgress}%)</p>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-gradient-to-r from-indigo-500 to-cyan-400 h-full transition-all duration-200"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          ) : (
            <>
              <div className="w-16 h-16 rounded-2xl bg-slate-800/80 border border-slate-700/80 text-indigo-400 flex items-center justify-center mb-5 group-hover:scale-110 transition shadow-inner">
                <UploadCloud className="w-8 h-8 text-indigo-400" />
              </div>

              <h3 className="text-xl font-bold text-slate-100 mb-2">
                Drop your video here or <span className="text-indigo-400 hover:text-indigo-300 underline underline-offset-4">browse</span>
              </h3>
              <p className="text-sm text-slate-400 max-w-md mb-6">
                Netra will extract frames, generate visual embeddings, transcribe spoken audio, and build multimodal search indexes.
              </p>

              <div className="flex flex-wrap items-center justify-center gap-1.5">
                {supportedFormats.map((fmt) => (
                  <span
                    key={fmt}
                    className="px-2.5 py-1 text-xs font-semibold bg-slate-800/80 text-slate-300 rounded-lg border border-slate-700/60"
                  >
                    {fmt}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Error Message Alert */}
      {errorMessage && (
        <div className="mt-4 p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl flex items-center gap-3 text-rose-300 text-sm animate-in fade-in">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
};

