<script setup lang="ts">
import { ref, computed } from 'vue';
import { useLanguage } from '../composables/useLanguage';
import { type DailyStats, type HourlyStat, type TagStat, type KeywordStat } from '../types';
import KeywordHeatmap from './KeywordHeatmap.vue';
import VChart from 'vue-echarts';
import { use, graphic } from 'echarts/core';
import { BarChart, PieChart, LineChart } from 'echarts/charts';
import {
    GridComponent,
    TooltipComponent,
    LegendComponent,
    GraphicComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

use([
    BarChart,
    PieChart,
    LineChart,
    GridComponent,
    TooltipComponent,
    LegendComponent,
    GraphicComponent,
    CanvasRenderer,
]);

interface StatisticsPanelProps {
    dailyStats: DailyStats[];
    hourlyStats: HourlyStat[];
    tagStats: TagStat[];
    keywordData: KeywordStat[];
}

const props = defineProps<StatisticsPanelProps>();
const { t, language } = useLanguage();

const totalEvents = computed(() => props.dailyStats.reduce((acc, curr) => acc + curr.count, 0));
const avgDuration = computed(() => Math.round(props.dailyStats.reduce((acc, curr) => acc + curr.avgDuration, 0) / (props.dailyStats.length || 1)));
const maxDay = computed(() => props.dailyStats.length === 0 ? { date: '-', count: 0, avgDuration: 0 } : props.dailyStats.reduce((prev, current) => (prev.count > current.count) ? prev : current));

const COLORS = ['#6366f1', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6'];

// Echarts options for Weekly Activity
const weeklyActivityOptions = computed(() => ({
    grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
    },
    xAxis: {
        type: 'category',
        data: props.dailyStats.map(stat => stat.date),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#94a3b8', fontSize: 12, margin: 10 },
    },
    yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#64748b', fontSize: 11 },
        splitLine: { lineStyle: { type: 'dashed', color: '#334155' } },
    },
    tooltip: {
        trigger: 'axis',
        backgroundColor: '#1e293b',
        borderColor: '#334155',
        textStyle: { color: '#f1f5f9' },
        borderRadius: 8,
        shadowStyle: {
            shadowColor: 'rgba(0, 0, 0, 0.1)',
            shadowBlur: 6,
            shadowOffsetY: 4,
        },
    },
    legend: {
        data: [t.value.stats.axisCount, t.value.stats.axisDuration],
        textStyle: { color: '#94a3b8' },
        top: 'top',
        right: 'right',
    },
    series: [
        {
            name: t.value.stats.axisCount,
            type: 'bar',
            data: props.dailyStats.map(stat => stat.count),
            itemStyle: {
                color: '#6366f1',
                borderRadius: [],
            },
            barMaxWidth: 50,
        },
        {
            name: t.value.stats.axisDuration,
            type: 'bar',
            data: props.dailyStats.map(stat => stat.avgDuration),
            itemStyle: {
                color: '#334155',
                borderRadius: [],
            },
            barMaxWidth: 50,
        },
    ],
}));

// Echarts options for Hourly Distribution
const hourlyDistributionOptions = computed(() => ({
    grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
    },
    xAxis: {
        type: 'category',
        data: props.hourlyStats.map(stat => stat.hour),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#94a3b8', fontSize: 11, margin: 10, interval: 1 },
    },
    yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false },
        splitLine: { show: false },
    },
    tooltip: {
        trigger: 'axis',
        backgroundColor: '#1e293b',
        borderColor: '#334155',
        textStyle: { color: '#f1f5f9' },
        borderRadius: 8,
        shadowStyle: {
            shadowColor: 'rgba(0, 0, 0, 0.1)',
            shadowBlur: 6,
            shadowOffsetY: 4,
        },
    },
    series: [
        {
            name: t.value.stats.axisCount,
            type: 'line',
            smooth: true,
            areaStyle: {
                opacity: 1,
                color: new graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0.05, color: 'rgba(16, 185, 129, 0.3)' },
                    { offset: 0.95, color: 'rgba(16, 185, 129, 0)' },
                ]),
            },
            itemStyle: {
                color: '#10b981',
            },
            lineStyle: {
                width: 3,
            },
            data: props.hourlyStats.map(stat => stat.count),
        },
    ],
}));

// Echarts options for Tag Distribution
const tagDistributionOptions = computed(() => ({
    tooltip: {
        trigger: 'item',
        backgroundColor: '#1e293b',
        borderColor: '#334155',
        textStyle: { color: '#f1f5f9' },
        borderRadius: 8,
        shadowStyle: {
            shadowColor: 'rgba(0, 0, 0, 0.1)',
            shadowBlur: 6,
            shadowOffsetY: 4,
        },
    },
    legend: {
        orient: 'vertical',
        left: 'right',
        top: 'middle',
        textStyle: { color: '#94a3b8', fontSize: 12 },
    },
    series: [
        {
            name: t.value.stats.tagDist,
            type: 'pie',
            radius: ['70%', '90%'],
            center: ['50%', '50%'],
            avoidLabelOverlap: false,
            itemStyle: {
                borderRadius: 5,
                borderColor: '#000',
                borderWidth: 0,
            },
            label: {
                show: false,
                position: 'center',
            },
            emphasis: {
                label: {
                    show: true,
                    fontSize: 20,
                    fontWeight: 'bold',
                    color: '#f1f5f9',
                },
            },
            labelLine: {
                show: false,
            },
            data: props.tagStats.map((stat, index) => ({
                value: stat.value,
                name: stat.name,
                itemStyle: {
                    color: COLORS[index % COLORS.length],
                },
            })),
        },
    ],
}));
</script>

<template>
    <div class="flex flex-col gap-6 w-full max-w-6xl mx-auto">

        <!-- 1. Header Summary Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm">
                <div class="flex items-center gap-2 text-slate-400 mb-2">
                    <!-- Activity size={16} -->
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                        class="lucide lucide-activity">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                    </svg>
                    <span class="text-xs uppercase font-semibold tracking-wider">{{ t.stats.totalEvents }}</span>
                </div>
                <div class="text-3xl font-bold text-white">{{ totalEvents }}</div>
            </div>
            <div class="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm">
                <div class="flex items-center gap-2 text-slate-400 mb-2">
                    <!-- Clock size={16} -->
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                        class="lucide lucide-clock">
                        <circle cx="12" cy="12" r="10" />
                        <polyline points="12 6 12 12 16 14" />
                    </svg>
                    <span class="text-xs uppercase font-semibold tracking-wider">{{ t.stats.avgDuration }}</span>
                </div>
                <div class="text-3xl font-bold text-white">{{ avgDuration }} <span
                        class="text-sm font-normal text-slate-500">{{ t.card.duration }}</span></div>
            </div>
            <div class="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm">
                <div class="flex items-center gap-2 text-slate-400 mb-2">
                    <!-- Calendar size={16} -->
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                        class="lucide lucide-calendar">
                        <path d="M8 2v4" />
                        <path d="M16 2v4" />
                        <rect width="18" height="18" x="3" y="4" rx="2" />
                        <path d="M3 10h18" />
                    </svg>
                    <span class="text-xs uppercase font-semibold tracking-wider">{{ t.stats.loudestDay }}</span>
                </div>
                <div class="text-3xl font-bold text-white">{{ maxDay.date }}</div>
            </div>
            <div class="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm">
                <div class="flex items-center gap-2 text-slate-400 mb-2">
                    <!-- Mic2 size={16} -->
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                        class="lucide lucide-mic-2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3Z" />
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                        <line x1="12" x2="12" y1="19" y2="22" />
                    </svg>
                    <span class="text-xs uppercase font-semibold tracking-wider">{{ t.stats.peakHour }}</span>
                </div>
                <div class="text-3xl font-bold text-white">03:00</div>
            </div>
        </div>

        <!-- 2. Text Summary / Insight -->
        <div
            class="bg-gradient-to-r from-indigo-900/40 to-slate-800 rounded-xl border border-indigo-500/30 p-6 shadow-lg relative overflow-hidden">
            <div class="absolute top-0 right-0 p-4 opacity-10 pointer-events-none">
                <!-- Sparkles size={100} -->
                <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                    class="lucide lucide-sparkles">
                    <path d="M9.9 10.9 8.5 13.5 7.1 10.9 4.5 9.5 7.1 8.1 8.5 5.5 9.9 8.1 12.5 9.5 9.9 10.9Z" />
                    <path d="M16.5 6.5 15.4 8.6 13.4 9.7 15.4 10.8 16.5 12.9 17.6 10.8 19.6 9.7 17.6 8.6 16.5 6.5Z" />
                    <path
                        d="M19.9 16.9 18.5 19.5 17.1 16.9 14.5 15.5 17.1 14.1 18.5 11.5 19.9 14.1 22.5 15.5 19.9 16.9Z" />
                </svg>
            </div>
            <div class="flex items-start gap-3 relative z-10">
                <div class="p-2 bg-indigo-500/20 rounded-lg text-indigo-300 mt-1">
                    <!-- Sparkles size={20} -->
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                        class="lucide lucide-sparkles">
                        <path d="M9.9 10.9 8.5 13.5 7.1 10.9 4.5 9.5 7.1 8.1 8.5 5.5 9.9 8.1 12.5 9.5 9.9 10.9Z" />
                        <path
                            d="M16.5 6.5 15.4 8.6 13.4 9.7 15.4 10.8 16.5 12.9 17.6 10.8 19.6 9.7 17.6 8.6 16.5 6.5Z" />
                        <path
                            d="M19.9 16.9 18.5 19.5 17.1 16.9 14.5 15.5 17.1 14.1 18.5 11.5 19.9 14.1 22.5 15.5 19.9 16.9Z" />
                    </svg>
                </div>
                <div>
                    <h3 class="text-indigo-200 font-semibold mb-2">{{ t.stats.title }}</h3>
                    <p class="text-slate-300 text-base leading-relaxed max-w-3xl">
                        {{ language === 'zh'
                            ? "本周您的梦话活动略有增加，主要集中在凌晨 3 点左右。情绪关键词多为中性或轻微焦虑，建议睡前减少屏幕使用时间，尝试冥想以改善深度睡眠质量。"
                            : `Sleep talk activity has increased slightly this week, peaking around 3 AM. Keywords remain
                        mostly neutral or mildly anxious.Consider reducing screen time before bed and trying meditation
                        to improve deep sleep quality.`}}
                    </p>
                </div>
            </div>
        </div>

        <!-- 3. Heatmap (Full Width) -->
        <KeywordHeatmap :data="keywordData" />

        <!-- 4. Detailed Charts Row -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

            <!-- Weekly Activity -->
            <div class="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg lg:col-span-2">
                <h3 class="text-slate-300 font-semibold mb-6 flex items-center gap-2">
                    <!-- Activity size={18} -->
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                        class="lucide lucide-activity text-indigo-400">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                    </svg>
                    {{ t.stats.last7Days }}
                </h3>
                <div class="h-64 w-full">
                    <VChart class="chart" :option="weeklyActivityOptions" autoresize />
                </div>
            </div>

            <!-- Hourly Distribution -->
            <div class="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg">
                <h3 class="text-slate-300 font-semibold mb-6 flex items-center gap-2">
                    <!-- Clock size={18} -->
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                        class="lucide lucide-clock text-emerald-400">
                        <circle cx="12" cy="12" r="10" />
                        <polyline points="12 6 12 12 16 14" />
                    </svg>
                    {{ t.stats.hourlyDist }}
                </h3>
                <div class="h-64 w-full">
                    <VChart class="chart" :option="hourlyDistributionOptions" autoresize />
                </div>
            </div>

            <!-- Tag Distribution -->
            <div class="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg">
                <h3 class="text-slate-300 font-semibold mb-6 flex items-center gap-2">
                    <!-- Mic2 size={18} -->
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                        class="lucide lucide-mic-2 text-pink-400">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3Z" />
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                        <line x1="12" x2="12" y1="19" y2="22" />
                    </svg>
                    {{ t.stats.tagDist }}
                </h3>
                <div class="h-64 w-full flex items-center justify-center">
                    <VChart class="chart" :option="tagDistributionOptions" autoresize />
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.chart {
    height: 100%;
    width: 100%;
}
</style>