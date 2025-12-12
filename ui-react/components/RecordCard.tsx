import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Play, Pause, Star, Tag, Clock } from 'lucide-react';
import { SleepRecord } from '../types';
import { useLanguage } from '../contexts/LanguageContext';

interface RecordCardProps {
  record: SleepRecord;
  onUpdateRecord?: (id: string, updates: Partial<SleepRecord>) => void;
}

const RecordCard: React.FC<RecordCardProps> = ({ record, onUpdateRecord }) => {
  const { t, language } = useLanguage();
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  
  // Create a static, consistent waveform pattern based on the record ID
  const waveformData = useMemo(() => {
    const bars = 60;
    // Simple pseudo-random generator seeded by id string length + index
    return Array.from({ length: bars }, (_, i) => {
        const seed = record.id.charCodeAt(record.id.length - 1) + i;
        // Generate values between 20% and 100% height
        return 20 + (Math.sin(seed) * 40 + 40); 
    });
  }, [record.id]);

  const animationRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, []);

  const togglePlay = () => {
    if (isPlaying) {
      setIsPlaying(false);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    } else {
      setIsPlaying(true);
      lastTimeRef.current = performance.now();
      animationRef.current = requestAnimationFrame(animatePlay);
      
      // If we are at the end, restart
      if (currentTime >= record.duration) {
        setCurrentTime(0);
      }
    }
  };

  const animatePlay = (time: number) => {
    const deltaTime = (time - lastTimeRef.current) / 1000;
    lastTimeRef.current = time;

    setCurrentTime(prev => {
      const nextTime = prev + deltaTime;
      if (nextTime >= record.duration) {
        setIsPlaying(false);
        return record.duration;
      }
      animationRef.current = requestAnimationFrame(animatePlay);
      return nextTime;
    });
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.min(Math.max(x / rect.width, 0), 1);
    const newTime = percentage * record.duration;
    
    setCurrentTime(newTime);
    
    // Optional: If we want to auto-play on seek, uncomment:
    // if (!isPlaying) togglePlay();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const toggleFavorite = () => {
    if (onUpdateRecord) {
      onUpdateRecord(record.id, { isFavorite: !record.isFavorite });
    }
  };

  const timeString = new Date(record.timestamp).toLocaleTimeString(language === 'zh' ? 'zh-CN' : 'en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  });

  return (
    <div className="bg-slate-800 rounded-xl p-5 border border-slate-700/50 hover:border-slate-600 transition-all shadow-md group">
      
      {/* Header Info */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-full ${isPlaying ? 'bg-indigo-500/20 text-indigo-400' : 'bg-slate-700/50 text-slate-400'}`}>
                <Clock size={18} />
            </div>
            <div>
                <div className="flex items-center gap-2">
                    <span className="text-lg font-bold font-mono tracking-tight text-white">{timeString}</span>
                    {record.confidence > 0.85 && (
                        <span className="text-[10px] uppercase font-bold bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20">
                            High Quality
                        </span>
                    )}
                </div>
                <div className="text-xs text-slate-400 mt-0.5">
                    {new Date(record.timestamp).toLocaleDateString()}
                </div>
            </div>
        </div>
        
        <button 
          onClick={toggleFavorite}
          className={`p-2 rounded-full transition-all ${
            record.isFavorite 
              ? 'text-amber-400 bg-amber-400/10 hover:bg-amber-400/20' 
              : 'text-slate-600 hover:text-slate-400 hover:bg-slate-700'
          }`}
          title="Toggle Favorite"
        >
          <Star size={20} fill={record.isFavorite ? "currentColor" : "none"} />
        </button>
      </div>

      {/* Audio Player Container */}
      <div className="bg-slate-900/50 rounded-lg p-3 mb-4 border border-slate-700/50 flex items-center gap-4">
          {/* Play/Pause Button */}
          <button 
             onClick={togglePlay}
             className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all ${
               isPlaying 
               ? 'bg-indigo-500 text-white shadow-[0_0_10px_rgba(99,102,241,0.4)]' 
               : 'bg-slate-700 text-slate-300 hover:bg-slate-600 hover:text-white'
             }`}
          >
            {isPlaying ? <Pause size={18} fill="currentColor"/> : <Play size={18} fill="currentColor" className="ml-1" />}
          </button>

          {/* Interactive Waveform / Progress Bar */}
          <div className="flex-1 h-full flex flex-col justify-center cursor-pointer group/waveform" onClick={handleSeek}>
             {/* Visual Bars */}
             <div className="flex items-center justify-between h-8 gap-[2px]">
                {waveformData.map((height, i) => {
                    const progress = currentTime / record.duration;
                    const barIndexPercent = i / waveformData.length;
                    const isPlayed = barIndexPercent <= progress;

                    return (
                        <div 
                           key={i} 
                           className={`w-1 rounded-full transition-colors duration-150 ${
                               isPlayed ? 'bg-indigo-500' : 'bg-slate-700 group-hover/waveform:bg-slate-600'
                           }`}
                           style={{ height: `${height}%` }}
                        />
                    );
                })}
             </div>
          </div>

          {/* Time Display */}
          <div className="flex-shrink-0 font-mono text-xs text-slate-400 w-20 text-right">
              <span className={isPlaying ? "text-indigo-400 font-bold" : ""}>{formatTime(currentTime)}</span>
              <span className="mx-1 opacity-50">/</span>
              <span>{formatTime(record.duration)}</span>
          </div>
      </div>
      
      {/* Transcript */}
      <div className="relative mb-3 pl-1">
        <p className="text-lg text-slate-200 font-medium italic leading-relaxed">
          "{record.transcription}"
        </p>
      </div>

      {/* Tags */}
      {record.tags && record.tags.length > 0 && (
        <div className="flex gap-2 flex-wrap">
            {record.tags.map(tag => (
                <span key={tag} className="flex items-center gap-1 text-xs font-medium text-slate-400 bg-slate-700/50 px-2 py-1 rounded-md border border-slate-700 hover:bg-slate-700 hover:text-slate-200 transition-colors cursor-default">
                    <Tag size={10} />
                    {tag}
                </span>
            ))}
            <span className={record.confidence > 0.8 ? "text-xs px-2 py-1 text-emerald-500 ml-auto" : "text-xs px-2 py-1 text-amber-500 ml-auto"}>
                {Math.round(record.confidence * 100)}% {t.card.match}
            </span>
        </div>
      )}

    </div>
  );
};

export default RecordCard;