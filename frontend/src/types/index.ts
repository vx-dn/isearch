// User types
export interface User {
  user_id: string
  email: string
  username?: string
  display_name?: string
  subscription_tier: 'free' | 'premium' | 'enterprise'
  preferences?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  username?: string
  display_name?: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

// Receipt types
export interface Receipt {
  receipt_id: string
  user_id: string
  merchant_name: string
  amount: number
  currency: string
  date: string
  items: ReceiptItem[]
  tags: string[]
  receipt_type: 'grocery' | 'restaurant' | 'gas' | 'retail' | 'medical' | 'business' | 'other'
  image_url?: string
  extracted_text?: string
  confidence_score?: number
  created_at: string
  updated_at: string
}

export interface ReceiptItem {
  name: string
  quantity: number
  unit_price: number
  total_price: number
  category?: string
}

export interface ReceiptCreateRequest {
  merchant_name: string
  amount: number
  currency?: string
  date: string
  items?: ReceiptItem[]
  tags?: string[]
  receipt_type?: string
}

// Search types
export interface SearchRequest {
  query: string
  limit?: number
  offset?: number
  filters?: SearchFilters
}

export interface SearchFilters {
  date_range?: {
    start_date: string
    end_date: string
  }
  amount_range?: {
    min_amount: number
    max_amount: number
  }
  merchants?: string[]
  tags?: string[]
  receipt_types?: string[]
}

export interface SearchResponse {
  results: Receipt[]
  total: number
  query: string
  filters_applied: SearchFilters
}

// Chat types
export interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  receipts?: Receipt[]
  isLoading?: boolean
}

export interface ImageUploadResponse {
  upload_url: string
  image_id: string
  expires_at: string
}

export interface ImageProcessingStatus {
  image_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  receipt?: Receipt
  error_message?: string
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

export interface PaginationParams {
  page: number
  page_size: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}