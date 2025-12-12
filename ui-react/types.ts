export type Language = 'en' | 'zh';

export interface SleepRecord {
  id: string;
  timestamp: string; // ISO String
  duration: number; // In seconds
  audioUrl: string; // URL to blob or mock
  transcription: string;
  confidence: number; // STT confidence 0-1
  tags: string[]; // e.g. "Mumbling", "Shouting", "Clear"
  isFavorite: boolean;
  // Legacy/Optional AI fields
  imageUrl?: string; 
}

export interface KeywordStat {
  text: string;
  value: number; // Frequency
  category: 'emotion' | 'object' | 'action' | 'abstract';
}

export interface DailyStats {
  date: string;
  count: number;
  avgDuration: number;
}

export interface HourlyStat {
  hour: string; // "01:00", "02:00"
  count: number;
}

export interface TagStat {
  name: string;
  value: number;
}

export interface MonthlyActivity {
  [dateStr: string]: number; // "YYYY-MM-DD": count
}