<template>
  <div 
    class="animate-slide-up"
    :class="message.type === 'user' ? 'flex justify-end' : 'flex justify-start'"
  >
    <div 
      class="message-bubble"
      :class="message.type === 'user' ? 'user-message' : 'assistant-message'"
    >
      <!-- Message Content -->
      <div class="prose prose-sm max-w-none">
        <p v-if="message.isLoading" class="flex items-center">
          <svg class="animate-spin -ml-1 mr-3 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ message.content }}
        </p>
        <p v-else>{{ message.content }}</p>
      </div>

      <!-- Receipt Cards -->
      <div v-if="message.receipts && message.receipts.length > 0" class="mt-4 space-y-3">
        <ReceiptCard 
          v-for="receipt in message.receipts.slice(0, 5)" 
          :key="receipt.receipt_id"
          :receipt="receipt"
        />
        
        <p v-if="message.receipts.length > 5" class="text-sm text-gray-500">
          ... and {{ message.receipts.length - 5 }} more receipts
        </p>
      </div>

      <!-- Timestamp -->
      <div 
        class="text-xs mt-2"
        :class="message.type === 'user' ? 'text-blue-200' : 'text-gray-500'"
      >
        {{ formatTime(message.timestamp) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { format } from 'date-fns'
import ReceiptCard from './ReceiptCard.vue'
import type { ChatMessage } from '@/types'

defineProps<{
  message: ChatMessage
}>()

const formatTime = (date: Date): string => {
  return format(date, 'HH:mm')
}
</script>

<style scoped>
.message-bubble {
  @apply max-w-3xl p-4 rounded-lg;
}

.user-message {
  @apply bg-blue-500 text-white ml-auto;
}

.assistant-message {
  @apply bg-white text-gray-900 border border-gray-200 shadow-sm;
}
</style>