import { type Language } from '../types'

export const translations = {
  en: {
    appTitle: 'DreamSpeak',
    tabs: {
      recordings: 'Recordings',
      insights: 'Analytics',
    },
    search: {
      placeholder: 'Search transcripts...',
      onlyFavorites: 'Favorites only',
    },
    timeline: {
      title: 'Timeline',
      eventsDetected: 'Events',
      noEvents: 'No sleep talking detected.',
      silence: 'Restful silence recorded.',
      noResults: 'No recordings match your search.',
    },
    card: {
      match: 'Confidence',
      listen: 'Play Audio',
      playing: 'Playing...',
      duration: 's',
      tags: 'Tags',
    },
    heatmap: {
      title: 'Keyword Frequency',
      categories: {
        emotion: 'Emotion',
        object: 'Object',
        action: 'Action',
        abstract: 'Abstract',
      },
      legend: {
        emotion: 'Emotion',
        object: 'Object',
        action: 'Action',
        abstract: 'Abstract',
      },
    },
    stats: {
      title: 'Sleep Talk Analytics',
      last7Days: 'Last 7 Days Trend',
      hourlyDist: 'Hourly Distribution (Circadian)',
      tagDist: 'Sound Type Breakdown',
      totalEvents: 'Total Events',
      avgDuration: 'Avg Duration',
      peakHour: 'Peak Hour',
      loudestDay: 'Most Active Day',
      axisCount: 'Events',
      axisDuration: 'Avg Secs',
      last7DaysShort: '7 Days', // New
      last30DaysShort: '30 Days', // New
      thisMonth: 'This Month', // New
    },
    date: {
      tonight: 'Tonight / Last Night',
      dateFormat: 'en-US',
      weekdays: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    },
    settings: {
      title: 'Settings',
      iconSectionTitle: 'iOS Home Screen Icon',
      iconSectionDesc: 'Download the icon for your iPhone/iPad\'s "Add to Home Screen" feature. Place the downloaded {file} in the {folder} directory of the UI.',
      iconDownloadBtn: 'Download 180x180 PNG',
      moreSettingsTitle: 'More Settings',
      moreSettingsDesc: 'More configuration options will be available here in the future.',
    },
    login: {
      title: 'Dream Catcher',
      subtitle: 'Enter Access Code to Continue',
      placeholder: 'Access Code',
      button: 'Enter',
      verifying: 'Verifying...',
      errors: {
        empty: 'Please enter the access code.',
        failed: 'Login failed. Please check the code and try again.',
        tooManyAttempts: 'Too many attempts. Please try again later.',
        unknown: 'An error occurred. Please try again later.',
      }
    }
  },
  zh: {
    appTitle: '梦语者',
    tabs: {
      recordings: '录音记录',
      insights: '数据分析',
    },
    search: {
      placeholder: '搜索梦话内容...',
      onlyFavorites: '仅看收藏',
    },
    timeline: {
      title: '时间轴',
      eventsDetected: '个事件',
      noEvents: '未检测到梦话',
      silence: '昨晚很安静，一夜无梦。',
      noResults: '没有找到匹配的记录。',
    },
    card: {
      match: '置信度',
      listen: '播放录音',
      playing: '播放中...',
      duration: '秒',
      tags: '标签',
    },
    heatmap: {
      title: '高频词汇热度',
      categories: {
        emotion: '情绪',
        object: '物品',
        action: '动作',
        abstract: '抽象',
      },
      legend: {
        emotion: '情绪',
        object: '物品',
        action: '动作',
        abstract: '抽象',
      },
    },
    stats: {
      title: '梦话数据概览',
      last7Days: '近7日趋势',
      hourlyDist: '时段分布 (生物钟)',
      tagDist: '声音类型占比',
      totalEvents: '累计事件',
      avgDuration: '平均时长',
      peakHour: '高峰时段',
      loudestDay: '最活跃日',
      axisCount: '次数',
      axisDuration: '平均秒数',
      last7DaysShort: '近7天', // New
      last30DaysShort: '近30天', // New
      thisMonth: '本月', // New
    },
    date: {
      tonight: '今晚 / 昨晚',
      dateFormat: 'zh-CN',
      weekdays: ['日', '一', '二', '三', '四', '五', '六'],
    },
    settings: {
      title: '设置',
      iconSectionTitle: 'iOS 主屏幕图标',
      iconSectionDesc: '为您的 iPhone/iPad “添加到主屏幕”功能下载图标。请将下载的 {file} 文件放置到前端的 {folder} 目录下。',
      iconDownloadBtn: '下载 180x180 PNG',
      moreSettingsTitle: '更多设置',
      moreSettingsDesc: '未来将在此处提供更多配置选项。',
    },
    login: {
      title: '梦语者',
      subtitle: '请输入访问码以继续',
      placeholder: '访问码',
      button: '进入',
      verifying: '验证中...',
      errors: {
        empty: '请输入访问码。',
        failed: '登录失败，请检查访问码后重试。',
        tooManyAttempts: '尝试次数过多，请稍后再试。',
        unknown: '发生未知错误，请稍后重试。',
      }
    }
  },
}
