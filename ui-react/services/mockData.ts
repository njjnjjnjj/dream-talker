import { SleepRecord, KeywordStat, DailyStats, Language, MonthlyActivity, HourlyStat, TagStat } from '../types';

const MOCK_TRANSCRIPTS_EN = [
  "No... don't eat the blue apple... it's swimming.",
  "Wait, I left the oven on... in the castle.",
  "Flying... so high... clouds are marshmallow.",
  "Run! The giant rabbit is coming!",
  "Put the stapler back... it belongs to the cat.",
  "Seven... forty-two... green...",
  "Stop looking at me like that.",
  "I didn't do it... it was the shadow.",
  "Water... need water...",
  "The door is locked from the outside."
];

const MOCK_TRANSCRIPTS_ZH = [
  "不要吃那个蓝色的苹果...它在游泳...",
  "等等，我把烤箱忘在城堡里了...",
  "飞...好高...云是棉花糖做的...",
  "快跑！巨大的兔子来了！",
  "把订书机放回去...那是猫的...",
  "七...四十二...绿色...",
  "别那样看着我。",
  "不是我干的...是影子...",
  "水...我要水...",
  "门从外面锁上了。"
];

const KEYWORDS_EN = [
  { text: "Falling", value: 45, category: "action" },
  { text: "Flying", value: 38, category: "action" },
  { text: "Monster", value: 30, category: "object" },
  { text: "Water", value: 25, category: "object" },
  { text: "Running", value: 22, category: "action" },
  { text: "Late", value: 20, category: "abstract" },
  { text: "Darkness", value: 18, category: "abstract" },
  { text: "Cat", value: 15, category: "object" },
  { text: "Eating", value: 12, category: "action" },
  { text: "Mother", value: 10, category: "object" },
  { text: "Lost", value: 28, category: "emotion" },
  { text: "Scared", value: 35, category: "emotion" },
  { text: "Happy", value: 8, category: "emotion" },
  { text: "Work", value: 14, category: "abstract" },
  { text: "School", value: 12, category: "object" },
];

const KEYWORDS_ZH = [
  { text: "坠落", value: 45, category: "action" },
  { text: "飞行", value: 38, category: "action" },
  { text: "怪物", value: 30, category: "object" },
  { text: "水", value: 25, category: "object" },
  { text: "奔跑", value: 22, category: "action" },
  { text: "迟到", value: 20, category: "abstract" },
  { text: "黑暗", value: 18, category: "abstract" },
  { text: "猫", value: 15, category: "object" },
  { text: "吃东西", value: 12, category: "action" },
  { text: "母亲", value: 10, category: "object" },
  { text: "迷路", value: 28, category: "emotion" },
  { text: "害怕", value: 35, category: "emotion" },
  { text: "快乐", value: 8, category: "emotion" },
  { text: "工作", value: 14, category: "abstract" },
  { text: "学校", value: 12, category: "object" },
];

const TAGS_EN = ["Mumbling", "Clear", "Shouting", "Laughing", "Whisper"];
const TAGS_ZH = ["含糊不清", "清晰", "喊叫", "笑声", "低语"];

export const generateMockRecords = (date: Date, lang: Language): SleepRecord[] => {
  const records: SleepRecord[] = [];
  const seed = date.getFullYear() + date.getMonth() + date.getDate();
  const hasRecords = (seed % 3) !== 0; 
  
  if (!hasRecords) return [];

  const count = (seed % 5) + 1; 
  const transcripts = lang === 'zh' ? MOCK_TRANSCRIPTS_ZH : MOCK_TRANSCRIPTS_EN;
  const tagList = lang === 'zh' ? TAGS_ZH : TAGS_EN;
  
  for (let i = 0; i < count; i++) {
    const time = new Date(date);
    // Bias towards 2AM - 4AM
    const hour = Math.floor(Math.random() * 3) + 2; 
    time.setHours(hour); 
    time.setMinutes(Math.floor(Math.random() * 60));
    
    // Random Tags (1 or 2)
    const tags = [];
    tags.push(tagList[Math.floor(Math.random() * tagList.length)]);
    if (Math.random() > 0.7) tags.push(tagList[Math.floor(Math.random() * tagList.length)]);

    records.push({
      id: `rec_${date.getTime()}_${i}`,
      timestamp: time.toISOString(),
      duration: Math.floor(Math.random() * 10) + 2, // 2 to 12 seconds
      audioUrl: '', 
      transcription: transcripts[Math.floor(Math.random() * transcripts.length)],
      confidence: 0.7 + (Math.random() * 0.25),
      tags: [...new Set(tags)],
      isFavorite: Math.random() > 0.8
    });
  }
  
  return records.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
};

export const getKeywordStats = (lang: Language): KeywordStat[] => {
  const keywords = lang === 'zh' ? KEYWORDS_ZH : KEYWORDS_EN;
  return keywords.map(k => ({
    ...k,
    category: k.category as any
  }));
};

export const getWeeklyStats = (lang: Language): DailyStats[] => {
  const stats: DailyStats[] = [];
  const today = new Date();
  const locale = lang === 'zh' ? 'zh-CN' : 'en-US';
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    stats.push({
      date: d.toLocaleDateString(locale, { weekday: 'short' }),
      count: Math.floor(Math.random() * 8),
      avgDuration: Math.floor(Math.random() * 8) + 2
    });
  }
  return stats;
};

export const getHourlyStats = (): HourlyStat[] => {
  const data: HourlyStat[] = [];
  // 10 PM to 7 AM
  const hours = [22, 23, 0, 1, 2, 3, 4, 5, 6, 7];
  
  hours.forEach(h => {
    // Peak around 2-3 AM
    let base = 2;
    if (h === 2 || h === 3) base = 8;
    if (h === 1 || h === 4) base = 5;
    
    data.push({
      hour: `${h.toString().padStart(2, '0')}:00`,
      count: Math.floor(Math.random() * 5) + base
    });
  });
  return data;
};

export const getTagStats = (lang: Language): TagStat[] => {
  const tagList = lang === 'zh' ? TAGS_ZH : TAGS_EN;
  return tagList.map(tag => ({
    name: tag,
    value: Math.floor(Math.random() * 20) + 5
  }));
};

export const getMonthlyActivity = (year: number, month: number): MonthlyActivity => {
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const activity: MonthlyActivity = {};
  
  for (let i = 1; i <= daysInMonth; i++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
    const seed = year + month + i;
    const hasRecords = (seed % 3) !== 0;
    activity[dateStr] = hasRecords ? (seed % 5) + 1 : 0;
  }
  return activity;
};