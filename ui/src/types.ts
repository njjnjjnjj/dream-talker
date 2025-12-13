export type Language = 'en' | 'zh';

export interface SleepRecord {
  id: string;          // 数据库里的 ID (UUID)
  timestamp: string;     // ISO 8601 格式的日期时间字符串
  duration: number;      // 持续时间（秒）
  audio_url: string;    // 音频文件的相对路径
  transcription: string; // 语音转写的文本
  confidence: number;    // STT 置信度
  is_favorite: boolean;  // 是否收藏
  tags: string[];        // 标签
  image_url?: string;     // AI 生成的图片 URL（可选）
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

export interface DailyActivitySummary {
  total_records: number;
  favorite_records: number;
}

export interface MonthlyActivity {
  activity: {
    [dateStr: string]: DailyActivitySummary; // "YYYY-MM-DD": DailyActivitySummary
  };
}

export interface StatisticsResponse {
  dailyStats: DailyStats[];
  hourlyStats: HourlyStat[];
  tagStats: TagStat[];
  keywordData: KeywordStat[];
}