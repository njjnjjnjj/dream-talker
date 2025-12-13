import { ref } from 'vue';
import type { SleepRecord, MonthlyActivity } from '../types';

const API_BASE_URL = '/api';

export function useRecordsApi() {
  const records = ref<SleepRecord[]>([]);
  const monthlyActivity = ref<MonthlyActivity | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  /**
   * Fetches sleep records for a specific date.
   * @param date - The selected date
   */
  const fetchRecordsByDate = async (date: Date) => {
    isLoading.value = true;
    error.value = null;
    try {
      const dateString = date.toISOString().split('T')[0];
      const response = await fetch(`${API_BASE_URL}/records?date=${dateString}`);
      if (!response.ok) {
        throw new Error('Failed to fetch records');
      }
      records.value = await response.json();
    } catch (err: any) {
      error.value = err.message || 'An unknown error occurred';
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * Constructs the full URL for an audio file.
   * @param audioPath - The relative path of the audio file
   * @returns The full URL to stream the audio
   */
  const getAudioUrl = (audioPath: string): string => {
    // The path should be like "YYYY-MM-DD/filename.wav"
    // We can directly use it, but let's be safe and join parts.
    if (!audioPath) return '';
    const parts = audioPath.replace(/\\/g, '/').split('/');
    if (parts.length < 2) {
      console.error('Invalid audio path format:', audioPath);
      return '';
    }
    return `${API_BASE_URL}/audio/${parts.join('/')}`;
  };

  /**
   * Fetches monthly activity data (record counts per day).
   * @param year - The year to fetch activity for
   * @param month - The month (1-12) to fetch activity for
   */
  const fetchMonthlyActivity = async (year: number, month: number) => {
    isLoading.value = true;
    error.value = null;
    try {
      const response = await fetch(`${API_BASE_URL}/records/activity?year=${year}&month=${month}`);
      if (!response.ok) {
        throw new Error('Failed to fetch monthly activity');
      }
      const data = await response.json();
      monthlyActivity.value = data;
    } catch (err: any) {
      error.value = err.message || 'An unknown error occurred';
    } finally {
      isLoading.value = false;
    }
  };

  return {
    records,
    monthlyActivity,
    isLoading,
    error,
    fetchRecordsByDate,
    getAudioUrl,
    fetchMonthlyActivity,
  };
}