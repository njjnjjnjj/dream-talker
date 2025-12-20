import { ref } from 'vue';
import type { SleepRecord, MonthlyActivity, StatisticsResponse } from '../types';

const API_BASE_URL = '/api';

const authedFetch = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const token = sessionStorage.getItem('access_token');
  
  const headers = new Headers(options.headers || {});
  if (token) {
    headers.append('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    // Token is invalid or expired, redirect to login
    sessionStorage.removeItem('access_token');
    // Use location.href to force a full page reload to clear any state
    window.location.href = '/login';
    // Throw an error to stop further execution in the current call chain
    throw new Error('Unauthorized');
  }

  return response;
};


export function useRecordsApi() {
  const records = ref<SleepRecord[]>([]);
  const monthlyActivity = ref<MonthlyActivity | null>(null);
  const statistics = ref<StatisticsResponse | null>(null);
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
      const response = await authedFetch(`${API_BASE_URL}/records?date=${dateString}`);
      if (!response.ok) {
        // authedFetch will handle 401, this is for other errors
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
      const response = await authedFetch(`${API_BASE_URL}/records/activity?year=${year}&month=${month}`);
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

  /**
   * Updates the favorite status of a sleep record.
   * @param recordId - The ID of the record to update
   * @param isFavorite - The new favorite status
   */
  const updateRecordFavoriteStatus = async (recordId: string, isFavorite: boolean) => {
    isLoading.value = true;
    error.value = null;
    try {
      const response = await authedFetch(`${API_BASE_URL}/records/${recordId}/favorite`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_favorite: isFavorite }),
      });
      if (!response.ok) {
        throw new Error('Failed to update favorite status');
      }
      // Optionally, update the local records array if needed
    } catch (err: any) {
      error.value = err.message || 'An unknown error occurred';
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * Fetches statistics data.
   * @param params - Query parameters (days or startDate+endDate)
   */
  const fetchStatistics = async (params: { days?: number; startDate?: Date; endDate?: Date } = { days: 7 }) => {
    isLoading.value = true;
    error.value = null;
    try {
      let query = '';
      if (params.startDate && params.endDate) {
          const start = params.startDate.toISOString().split('T')[0];
          const end = params.endDate.toISOString().split('T')[0];
          query = `start_date=${start}&end_date=${end}`;
      } else if (params.days) {
          query = `days=${params.days}`;
      } else {
          query = `days=7`;
      }

      const response = await authedFetch(`${API_BASE_URL}/statistics?${query}`);
      if (!response.ok) {
        throw new Error('Failed to fetch statistics');
      }
      statistics.value = await response.json();
    } catch (err: any) {
      error.value = err.message || 'An unknown error occurred';
    } finally {
      isLoading.value = false;
    }
  };

  return {
    records,
    monthlyActivity,
    statistics,
    isLoading,
    error,
    fetchRecordsByDate,
    getAudioUrl,
    fetchMonthlyActivity,
    updateRecordFavoriteStatus,
    fetchStatistics,
  };
}