import { Language } from '../types';

export const translations = {
  en: {
    appTitle: "DreamSpeak",
    tabs: {
      recordings: "Recordings",
      insights: "Analytics"
    },
    search: {
      placeholder: "Search transcripts...",
      onlyFavorites: "Favorites only"
    },
    timeline: {
      title: "Timeline",
      eventsDetected: "Events",
      noEvents: "No sleep talking detected.",
      silence: "Restful silence recorded.",
      noResults: "No recordings match your search."
    },
    card: {
      match: "Confidence",
      listen: "Play Audio",
      playing: "Playing...",
      duration: "s",
      tags: "Tags"
    },
    heatmap: {
      title: "Keyword Frequency",
      categories: {
        emotion: "Emotion",
        object: "Object",
        action: "Action",
        abstract: "Abstract"
      },
      legend: {
         emotion: "Emotion",
         object: "Object",
         action: "Action",
         abstract: "Abstract"
      }
    },
    stats: {
      title: "Sleep Talk Analytics",
      last7Days: "Last 7 Days Trend",
      hourlyDist: "Hourly Distribution (Circadian)",
      tagDist: "Sound Type Breakdown",
      totalEvents: "Total Events",
      avgDuration: "Avg Duration",
      peakHour: "Peak Hour",
      loudestDay: "Most Active Day",
      axisCount: "Events",
      axisDuration: "Avg Secs"
    },
    date: {
      tonight: "Tonight / Last Night",
      dateFormat: "en-US",
      weekdays: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    }
  },
  zh: {
    appTitle: "梦语者",
    tabs: {
      recordings: "录音记录",
      insights: "数据分析"
    },
    search: {
      placeholder: "搜索梦话内容...",
      onlyFavorites: "仅看收藏"
    },
    timeline: {
      title: "时间轴",
      eventsDetected: "个事件",
      noEvents: "未检测到梦话",
      silence: "昨晚很安静，一夜无梦。",
      noResults: "没有找到匹配的记录。"
    },
    card: {
      match: "置信度",
      listen: "播放录音",
      playing: "播放中...",
      duration: "秒",
      tags: "标签"
    },
    heatmap: {
      title: "高频词汇热度",
      categories: {
        emotion: "情绪",
        object: "物品",
        action: "动作",
        abstract: "抽象"
      },
      legend: {
         emotion: "情绪",
         object: "物品",
         action: "动作",
         abstract: "抽象"
      }
    },
    stats: {
      title: "梦话数据概览",
      last7Days: "近7日趋势",
      hourlyDist: "时段分布 (生物钟)",
      tagDist: "声音类型占比",
      totalEvents: "累计事件",
      avgDuration: "平均时长",
      peakHour: "高峰时段",
      loudestDay: "最活跃日",
      axisCount: "次数",
      axisDuration: "平均秒数"
    },
    date: {
      tonight: "今晚 / 昨晚",
      dateFormat: "zh-CN",
      weekdays: ["日", "一", "二", "三", "四", "五", "六"]
    }
  }
};