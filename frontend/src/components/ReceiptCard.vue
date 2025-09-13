<template>
  <div class="receipt-card">
    <div class="flex items-start justify-between">
      <!-- Receipt Info -->
      <div class="flex-1">
        <div class="flex items-center space-x-2 mb-2">
          <h3 class="font-medium text-gray-900">{{ receipt.merchant_name }}</h3>
          <span 
            class="px-2 py-1 text-xs rounded-full"
            :class="getTypeColor(receipt.receipt_type)"
          >
            {{ formatReceiptType(receipt.receipt_type) }}
          </span>
        </div>
        
        <div class="text-sm text-gray-600 space-y-1">
          <p class="flex items-center">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
            </svg>
            <span class="font-medium text-green-600">${{ receipt.amount.toFixed(2) }}</span>
            <span class="ml-1 text-gray-500">{{ receipt.currency || 'USD' }}</span>
          </p>
          
          <p class="flex items-center">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3a1 1 0 011-1h6a1 1 0 011 1v4m-9 4h10a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V7a2 2 0 012-2z" />
            </svg>
            {{ formatDate(receipt.date) }}
          </p>
        </div>

        <!-- Items -->
        <div v-if="receipt.items && receipt.items.length > 0" class="mt-3">
          <div class="text-xs text-gray-500 mb-1">Items:</div>
          <div class="space-y-1">
            <div 
              v-for="(item, index) in receipt.items.slice(0, 3)"
              :key="index"
              class="text-sm text-gray-700 flex justify-between"
            >
              <span>{{ item.name }} ({{ item.quantity }}x)</span>
              <span>${{ (item.unit_price * item.quantity).toFixed(2) }}</span>
            </div>
            <div v-if="receipt.items.length > 3" class="text-xs text-gray-500">
              ... and {{ receipt.items.length - 3 }} more items
            </div>
          </div>
        </div>

        <!-- Tags -->
        <div v-if="receipt.tags && receipt.tags.length > 0" class="mt-3">
          <div class="flex flex-wrap gap-1">
            <span 
              v-for="tag in receipt.tags.slice(0, 3)"
              :key="tag"
              class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
            >
              {{ tag }}
            </span>
            <span v-if="receipt.tags.length > 3" class="text-xs text-gray-500">
              +{{ receipt.tags.length - 3 }} more
            </span>
          </div>
        </div>
      </div>

      <!-- Receipt Image/Actions -->
      <div class="ml-4 flex flex-col items-end space-y-2">
        <button 
          v-if="receipt.image_url"
          @click="showImage = true"
          class="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center hover:bg-gray-200"
          title="View receipt image"
        >
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </button>

        <div class="flex space-x-1">
          <button 
            @click="$emit('edit', receipt)"
            class="p-1 text-gray-400 hover:text-blue-600"
            title="Edit receipt"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          
          <button 
            @click="$emit('delete', receipt)"
            class="p-1 text-gray-400 hover:text-red-600"
            title="Delete receipt"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Confidence Score -->
    <div v-if="receipt.confidence_score" class="mt-3 flex items-center text-xs text-gray-500">
      <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      {{ Math.round(receipt.confidence_score * 100) }}% confidence
    </div>

    <!-- Image Modal -->
    <div 
      v-if="showImage && receipt.image_url"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click="showImage = false"
    >
      <div class="max-w-4xl max-h-full p-4">
        <img 
          :src="receipt.image_url" 
          :alt="`Receipt from ${receipt.merchant_name}`"
          class="max-w-full max-h-full object-contain rounded-lg"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { format } from 'date-fns'
import type { Receipt } from '@/types'

defineProps<{
  receipt: Receipt
}>()

defineEmits<{
  edit: [receipt: Receipt]
  delete: [receipt: Receipt]
}>()

const showImage = ref(false)

const formatDate = (dateString: string): string => {
  return format(new Date(dateString), 'MMM dd, yyyy')
}

const formatReceiptType = (type: string): string => {
  return type.charAt(0).toUpperCase() + type.slice(1)
}

const getTypeColor = (type: string): string => {
  const colors = {
    grocery: 'bg-green-100 text-green-800',
    restaurant: 'bg-orange-100 text-orange-800',
    gas: 'bg-blue-100 text-blue-800',
    retail: 'bg-purple-100 text-purple-800',
    medical: 'bg-red-100 text-red-800',
    business: 'bg-gray-100 text-gray-800',
    other: 'bg-gray-100 text-gray-800'
  }
  return colors[type as keyof typeof colors] || colors.other
}
</script>