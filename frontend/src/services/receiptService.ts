import { apiClient } from './apiClient'
import type { 
  Receipt, 
  ReceiptCreateRequest, 
  PaginatedResponse,
  ImageUploadResponse,
  ImageProcessingStatus 
} from '@/types'

class ReceiptService {
  async createReceipt(data: ReceiptCreateRequest): Promise<Receipt> {
    try {
      return await apiClient.post<Receipt>('/receipts/', data)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to create receipt')
    }
  }

  async getReceipts(page: number = 1, pageSize: number = 20): Promise<PaginatedResponse<Receipt>> {
    try {
      return await apiClient.get<PaginatedResponse<Receipt>>(
        `/receipts/?page=${page}&page_size=${pageSize}`
      )
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get receipts')
    }
  }

  async getReceipt(receiptId: string): Promise<Receipt> {
    try {
      return await apiClient.get<Receipt>(`/receipts/${receiptId}`)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get receipt')
    }
  }

  async updateReceipt(receiptId: string, data: Partial<ReceiptCreateRequest>): Promise<Receipt> {
    try {
      return await apiClient.put<Receipt>(`/receipts/${receiptId}`, data)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to update receipt')
    }
  }

  async deleteReceipt(receiptId: string): Promise<void> {
    try {
      await apiClient.delete(`/receipts/${receiptId}`)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to delete receipt')
    }
  }

  async generateUploadUrl(): Promise<ImageUploadResponse> {
    try {
      return await apiClient.post<ImageUploadResponse>('/receipts/upload-url')
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to generate upload URL')
    }
  }

  async processImage(imageId: string): Promise<ImageProcessingStatus> {
    try {
      return await apiClient.post<ImageProcessingStatus>(`/receipts/process-image/${imageId}`)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to process image')
    }
  }

  async getProcessingStatus(imageId: string): Promise<ImageProcessingStatus> {
    try {
      return await apiClient.get<ImageProcessingStatus>(`/receipts/processing-status/${imageId}`)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get processing status')
    }
  }

  async getReceiptsByDateRange(
    startDate: string,
    endDate: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<PaginatedResponse<Receipt>> {
    try {
      return await apiClient.get<PaginatedResponse<Receipt>>(
        `/receipts/by-date-range/?start_date=${startDate}&end_date=${endDate}&page=${page}&page_size=${pageSize}`
      )
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get receipts by date range')
    }
  }

  async getReceiptsByMerchant(
    merchantName: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<PaginatedResponse<Receipt>> {
    try {
      return await apiClient.get<PaginatedResponse<Receipt>>(
        `/receipts/by-merchant/?merchant_name=${encodeURIComponent(merchantName)}&page=${page}&page_size=${pageSize}`
      )
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get receipts by merchant')
    }
  }
}

export const receiptService = new ReceiptService()