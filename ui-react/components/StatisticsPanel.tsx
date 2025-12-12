import React from 'react';
import { 
  BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend 
} from 'recharts';
import { DailyStats, HourlyStat, TagStat, KeywordStat } from '../types';
import { useLanguage } from '../contexts/LanguageContext';
import { Clock, Activity, Mic2, Calendar, Sparkles } from 'lucide-react';
import KeywordHeatmap from './KeywordHeatmap';

interface StatisticsPanelProps {
  dailyStats: DailyStats[];
  hourlyStats: HourlyStat[];
  tagStats: TagStat[];
  keywordData: KeywordStat[];
}

const COLORS = ['#6366f1', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6'];

const StatisticsPanel: React.FC<StatisticsPanelProps> = ({ dailyStats, hourlyStats, tagStats, keywordData }) => {
  const { t, language } = useLanguage();

  const totalEvents = dailyStats.reduce((acc, curr) => acc + curr.count, 0);
  const avgDuration = Math.round(dailyStats.reduce((acc, curr) => acc + curr.avgDuration, 0) / (dailyStats.length || 1));
  const maxDay = dailyStats.reduce((prev, current) => (prev.count > current.count) ? prev : current, dailyStats[0] || {date: '-', count: 0});

  // Custom Tooltip Styles
  const tooltipStyle = { 
    backgroundColor: '#1e293b', 
    borderColor: '#334155', 
    color: '#f1f5f9', 
    borderRadius: '8px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
  };

  return (
    <div className="flex flex-col gap-6 w-full max-w-6xl mx-auto">
        
        {/* 1. Header Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm">
                <div className="flex items-center gap-2 text-slate-400 mb-2">
                    <Activity size={16} />
                    <span className="text-xs uppercase font-semibold tracking-wider">{t.stats.totalEvents}</span>
                </div>
                <div className="text-3xl font-bold text-white">{totalEvents}</div>
            </div>
            <div className="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm">
                <div className="flex items-center gap-2 text-slate-400 mb-2">
                    <Clock size={16} />
                    <span className="text-xs uppercase font-semibold tracking-wider">{t.stats.avgDuration}</span>
                </div>
                <div className="text-3xl font-bold text-white">{avgDuration} <span className="text-sm font-normal text-slate-500">{t.card.duration}</span></div>
            </div>
            <div className="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm">
                <div className="flex items-center gap-2 text-slate-400 mb-2">
                    <Calendar size={16} />
                    <span className="text-xs uppercase font-semibold tracking-wider">{t.stats.loudestDay}</span>
                </div>
                <div className="text-3xl font-bold text-white">{maxDay.date}</div>
            </div>
            <div className="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm">
                <div className="flex items-center gap-2 text-slate-400 mb-2">
                    <Mic2 size={16} />
                    <span className="text-xs uppercase font-semibold tracking-wider">{t.stats.peakHour}</span>
                </div>
                <div className="text-3xl font-bold text-white">03:00</div>
            </div>
        </div>

        {/* 2. Text Summary / Insight */}
        <div className="bg-gradient-to-r from-indigo-900/40 to-slate-800 rounded-xl border border-indigo-500/30 p-6 shadow-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10 pointer-events-none">
                <Sparkles size={100} />
            </div>
            <div className="flex items-start gap-3 relative z-10">
                <div className="p-2 bg-indigo-500/20 rounded-lg text-indigo-300 mt-1">
                    <Sparkles size={20} />
                </div>
                <div>
                    <h3 className="text-indigo-200 font-semibold mb-2">{t.stats.title}</h3>
                    <p className="text-slate-300 text-base leading-relaxed max-w-3xl">
                        {language === 'zh' 
                            ? "本周您的梦话活动略有增加，主要集中在凌晨 3 点左右。情绪关键词多为中性或轻微焦虑，建议睡前减少屏幕使用时间，尝试冥想以改善深度睡眠质量。"
                            : "Sleep talk activity has increased slightly this week, peaking around 3 AM. Keywords remain mostly neutral or mildly anxious. Consider reducing screen time before bed and trying meditation to improve deep sleep quality."}
                    </p>
                </div>
            </div>
        </div>

        {/* 3. Heatmap (Full Width) */}
        <KeywordHeatmap data={keywordData} />

        {/* 4. Detailed Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
             {/* Weekly Activity */}
             <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg lg:col-span-2">
                <h3 className="text-slate-300 font-semibold mb-6 flex items-center gap-2">
                    <Activity size={18} className="text-indigo-400"/> {t.stats.last7Days}
                </h3>
                <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dailyStats}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                        <XAxis 
                            dataKey="date" 
                            stroke="#64748b" 
                            tick={{ fill: '#94a3b8', fontSize: 12 }} 
                            axisLine={false}
                            tickLine={false}
                            dy={10}
                        />
                        <YAxis stroke="#64748b" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}/>
                        <Tooltip cursor={{ fill: '#334155', opacity: 0.4 }} contentStyle={tooltipStyle} />
                        <Legend />
                        <Bar dataKey="count" name={t.stats.axisCount} fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={50} />
                        <Bar dataKey="avgDuration" name={t.stats.axisDuration} fill="#334155" radius={[4, 4, 0, 0]} maxBarSize={50} />
                    </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Hourly Distribution */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg">
                <h3 className="text-slate-300 font-semibold mb-6 flex items-center gap-2">
                    <Clock size={18} className="text-emerald-400"/> {t.stats.hourlyDist}
                </h3>
                <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={hourlyStats}>
                        <defs>
                            <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                        <XAxis dataKey="hour" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} dy={10} interval={1} />
                        <YAxis hide />
                        <Tooltip contentStyle={tooltipStyle} />
                        <Area type="monotone" dataKey="count" stroke="#10b981" fillOpacity={1} fill="url(#colorCount)" strokeWidth={3} />
                    </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Tag Distribution */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg">
                <h3 className="text-slate-300 font-semibold mb-6 flex items-center gap-2">
                    <Mic2 size={18} className="text-pink-400"/> {t.stats.tagDist}
                </h3>
                <div className="h-64 w-full flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={tagStats}
                                cx="50%"
                                cy="50%"
                                innerRadius={70}
                                outerRadius={90}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {tagStats.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="rgba(0,0,0,0)" />
                                ))}
                            </Pie>
                            <Tooltip contentStyle={tooltipStyle} />
                            <Legend layout="vertical" verticalAlign="middle" align="right" wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }}/>
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    </div>
  );
};

export default StatisticsPanel;