import { apiClient } from './apiClient'
import type { LoginCredentials, RegisterData, LoginResponse, User } from '@/types'

class AuthService {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      return await apiClient.post<LoginResponse>('/auth/login', credentials)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed')
    }
  }

  async register(data: RegisterData): Promise<User> {
    try {
      return await apiClient.post<User>('/auth/register', data)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Registration failed')
    }
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout')
    } catch (error: any) {
      console.error('Logout error:', error)
    }
  }

  async getProfile(): Promise<User> {
    try {
      return await apiClient.get<User>('/auth/profile')
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get profile')
    }
  }

  async forgotPassword(email: string): Promise<void> {
    try {
      await apiClient.post('/auth/forgot-password', { email })
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Password reset failed')
    }
  }

  async resetPassword(token: string, new_password: string): Promise<void> {
    try {
      await apiClient.post('/auth/reset-password', { 
        reset_token: token,
        new_password 
      })
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Password reset failed')
    }
  }
}

export const authService = new AuthService()