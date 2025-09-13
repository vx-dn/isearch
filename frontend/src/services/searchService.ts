import { apiClient } from './apiClient'
import type { 
  SearchRequest, 
  SearchResponse, 
  Receipt,
  PaginatedResponse 
} from '@/types'

class SearchService {
  async searchReceipts(request: SearchRequest): Promise<SearchResponse> {
    try {
      return await apiClient.post<SearchResponse>('/search/', request)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Search failed')
    }
  }

  async searchByMerchant(
    merchantName: string, 
    limit: number = 20, 
    offset: number = 0
  ): Promise<SearchResponse> {
    try {
      return await apiClient.get<SearchResponse>(
        `/search/merchant/${encodeURIComponent(merchantName)}?limit=${limit}&offset=${offset}`
      )
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Merchant search failed')
    }
  }

  async searchByDateRange(
    startDate: string,
    endDate: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<SearchResponse> {
    try {
      return await apiClient.post<SearchResponse>('/search/date-range', {
        start_date: startDate,
        end_date: endDate,
        limit,
        offset
      })
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Date range search failed')
    }
  }

  async searchByAmountRange(
    minAmount: number,
    maxAmount: number,
    limit: number = 20,
    offset: number = 0
  ): Promise<SearchResponse> {
    try {
      return await apiClient.post<SearchResponse>('/search/amount-range', {
        min_amount: minAmount,
        max_amount: maxAmount,
        limit,
        offset
      })
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Amount range search failed')
    }
  }

  async searchByTags(
    tags: string[],
    limit: number = 20,
    offset: number = 0
  ): Promise<SearchResponse> {
    try {
      return await apiClient.post<SearchResponse>('/search/tags', {
        tags,
        limit,
        offset
      })
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Tag search failed')
    }
  }

  async getSuggestions(query: string, limit: number = 5): Promise<string[]> {
    try {
      return await apiClient.get<string[]>(
        `/search/suggestions?query=${encodeURIComponent(query)}&limit=${limit}`
      )
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get suggestions')
    }
  }

  async getPopularMerchants(limit: number = 10): Promise<Array<{ name: string; count: number }>> {
    try {
      return await apiClient.get<Array<{ name: string; count: number }>>(
        `/search/popular-merchants?limit=${limit}`
      )
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get popular merchants')
    }
  }

  async getPopularTags(limit: number = 20): Promise<Array<{ name: string; count: number }>> {
    try {
      return await apiClient.get<Array<{ name: string; count: number }>>(
        `/search/popular-tags?limit=${limit}`
      )
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get popular tags')
    }
  }
}

export const searchService = new SearchService()