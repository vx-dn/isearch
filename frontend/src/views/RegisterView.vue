<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <!-- Header -->
      <div class="text-center">
        <h1 class="text-3xl font-bold text-gray-900">Receipt Search</h1>
        <h2 class="mt-6 text-2xl font-semibold text-gray-700">Create your account</h2>
        <p class="mt-2 text-gray-600">
          Or 
          <router-link to="/login" class="text-blue-600 hover:text-blue-500">
            sign in to existing account
          </router-link>
        </p>
      </div>

      <!-- Registration Form -->
      <form @submit.prevent="handleRegister" class="mt-8 space-y-6">
        <div class="space-y-4">
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">
              Email address *
            </label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
              placeholder="Enter your email"
              :disabled="isLoading"
            />
          </div>

          <div>
            <label for="username" class="block text-sm font-medium text-gray-700">
              Username (optional)
            </label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
              placeholder="Choose a username"
              :disabled="isLoading"
            />
          </div>

          <div>
            <label for="display_name" class="block text-sm font-medium text-gray-700">
              Display name (optional)
            </label>
            <input
              id="display_name"
              v-model="form.display_name"
              type="text"
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
              placeholder="Your display name"
              :disabled="isLoading"
            />
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">
              Password *
            </label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              minlength="8"
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
              placeholder="Create a password (min. 8 characters)"
              :disabled="isLoading"
            />
          </div>

          <div>
            <label for="confirm_password" class="block text-sm font-medium text-gray-700">
              Confirm Password *
            </label>
            <input
              id="confirm_password"
              v-model="confirmPassword"
              type="password"
              required
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
              placeholder="Confirm your password"
              :disabled="isLoading"
            />
          </div>
        </div>

        <!-- Password Requirements -->
        <div class="text-sm text-gray-600">
          <p class="font-medium">Password requirements:</p>
          <ul class="mt-1 space-y-1">
            <li class="flex items-center">
              <span class="mr-2" :class="form.password.length >= 8 ? 'text-green-500' : 'text-gray-400'">
                ✓
              </span>
              At least 8 characters
            </li>
          </ul>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="rounded-md bg-red-50 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3">
              <p class="text-sm text-red-800">{{ error }}</p>
            </div>
          </div>
        </div>

        <!-- Submit Button -->
        <div>
          <button
            type="submit"
            :disabled="!canSubmit || isLoading"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isLoading" class="absolute left-0 inset-y-0 flex items-center pl-3">
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </span>
            {{ isLoading ? 'Creating account...' : 'Create account' }}
          </button>
        </div>
      </form>

      <!-- Terms -->
      <div class="text-center text-xs text-gray-500">
        By creating an account, you agree to our Terms of Service and Privacy Policy
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  email: '',
  username: '',
  display_name: '',
  password: ''
})

const confirmPassword = ref('')

const isLoading = computed(() => authStore.isLoading)
const error = computed(() => authStore.error)

const canSubmit = computed(() => {
  return form.email && 
         form.password && 
         form.password.length >= 8 &&
         confirmPassword.value === form.password
})

const handleRegister = async () => {
  if (form.password !== confirmPassword.value) {
    authStore.error = 'Passwords do not match'
    return
  }

  authStore.clearError()
  
  const success = await authStore.register({
    email: form.email,
    username: form.username || undefined,
    display_name: form.display_name || undefined,
    password: form.password
  })
  
  if (success) {
    alert('Account created successfully! Please check your email for verification.')
    router.push('/login')
  }
}
</script>