import { type SleepRecord, type KeywordStat, type DailyStats, type HourlyStat, type TagStat, type Language, type MonthlyActivity } from '../types';

export const generateMockRecords = (date: Date, language: Language): SleepRecord[] => {
  const records: SleepRecord[] = [];
  const numberOfRecords = Math.floor(Math.random() * 5) + 3; // 3 to 7 records

  for (let i = 0; i < numberOfRecords; i++) {
    const hour = Math.floor(Math.random() * 8) + 20; // 8 PM to 3 AM
    const minute = Math.floor(Math.random() * 60);
    const second = Math.floor(Math.random() * 60);

    const recordDate = new Date(date);
    recordDate.setHours(hour, minute, second, 0);

    const commonPhrases_en = [
      "No, don't do that!", "Where is it?", "It's too cold.", "Leave me alone.", "What time is it?",
      "I need to go.", "Who's there?", "It's right here.", "Just a little more.", "I'm sleepy."
    ];
    const commonPhrases_zh = [
      "不，不要那样！", "它在哪里？", "太冷了。", "让我一个人呆着。", "现在几点了？",
      "我得走了。", "是谁在那里？", "它就在这里。", "再来一点。", "我困了。"
    ];

    const tags = ['Mumbling', 'Shouting', 'Whispering', 'Clear', 'Gasp'];
    const randomTags = Array.from({ length: Math.floor(Math.random() * 3) + 1 }, 
                                  () => tags[Math.floor(Math.random() * tags.length)]);

    records.push({
      id: `rec-${date.toISOString()}-${i}`,
      timestamp: recordDate.toISOString(),
      duration: Math.floor(Math.random() * 30) + 5, // 5 to 35 seconds
      audioUrl: `mock-audio-${i}.mp3`,
      transcription: language === 'en'
        ? commonPhrases_en[Math.floor(Math.random() * commonPhrases_en.length)] || "Unknown"
        : commonPhrases_zh[Math.floor(Math.random() * commonPhrases_zh.length)] || "未知",
      confidence: parseFloat((Math.random() * (0.95 - 0.7) + 0.7).toFixed(2)),
      tags: [...new Set(randomTags.filter(tag => tag !== undefined))] as string[], // Unique tags
      isFavorite: Math.random() > 0.7
    });
  }
  return records.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
};

export const getKeywordStats = (language: Language): KeywordStat[] => {
  if (language === 'en') {
    return [
      { text: "dream", value: 50, category: "abstract" },
      { text: "run", value: 35, category: "action" },
      { text: "house", value: 30, category: "object" },
      { text: "scared", value: 25, category: "emotion" },
      { text: "work", value: 20, category: "action" },
      { text: "cat", value: 18, category: "object" },
      { text: "happy", value: 15, category: "emotion" },
      { text: "fly", value: 12, category: "action" },
      { text: "tree", value: 10, category: "object" },
      { text: "confused", value: 8, category: "emotion" },
    ];
  } else {
    return [
      { text: "梦", value: 55, category: "abstract" },
      { text: "跑", value: 40, category: "action" },
      { text: "家", value: 32, category: "object" },
      { text: "害怕", value: 28, category: "emotion" },
      { text: "工作", value: 22, category: "action" },
      { text: "猫", value: 19, category: "object" },
      { text: "开心", value: 16, category: "emotion" },
      { text: "飞", value: 13, category: "action" },
      { text: "树", value: 11, category: "object" },
      { text: "困惑", value: 9, category: "emotion" },
    ];
  }
};

export const getWeeklyStats = (language: Language): DailyStats[] => {
  const stats: DailyStats[] = [];
  const today = new Date();
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    stats.push({
      date: d.toLocaleDateString(language === 'en' ? 'en-US' : 'zh-CN', { weekday: 'short', day: 'numeric' }),
      count: Math.floor(Math.random() * 10) + 2, // 2 to 11 events
      avgDuration: parseFloat((Math.random() * (20 - 5) + 5).toFixed(1)) // 5 to 20 seconds
    });
  }
  return stats;
};

export const getHourlyStats = (): HourlyStat[] => {
  const stats: HourlyStat[] = [];
  for (let i = 0; i < 24; i++) {
    stats.push({
      hour: `${i.toString().padStart(2, '0')}:00`,
      count: Math.floor(Math.random() * 15) + (i > 20 || i < 4 ? 10 : 0) // Peak late night/early morning
    });
  }
  return stats;
};

export const getTagStats = (language: Language): TagStat[] => {
  const baseTags = [
    { name: "Mumbling", value: 30 },
    { name: "Shouting", value: 15 },
    { name: "Whispering", value: 25 },
    { name: "Clear", value: 20 },
    { name: "Gasp", value: 10 },
  ];

  if (language === 'zh') {
    return baseTags.map(tag => {
      switch (tag.name) {
        case "Mumbling": return { ...tag, name: "喃喃自语" };
        case "Shouting": return { ...tag, name: "大喊" };
        case "Whispering": return { ...tag, name: "耳语" };
        case "Clear": return { ...tag, name: "清晰" };
        case "Gasp": return { ...tag, name: "喘息" };
        default: return tag;
      }
    });
  }
  return baseTags;
};

export const getMonthlyActivity = (year: number, month: number): MonthlyActivity => {
  const activity: MonthlyActivity = {};
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  for (let i = 1; i <= daysInMonth; i++) {
    const date = new Date(year, month, i);
    // Simulate some activity
    if (Math.random() > 0.4) { // 60% chance of activity
      activity[date.toISOString().slice(0, 10)] = Math.floor(Math.random() * 5) + 1; // 1 to 5 events
    }
  }
  return activity;
};