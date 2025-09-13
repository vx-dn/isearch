<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <div class="w-64 bg-white shadow-sm border-r border-gray-200 flex flex-col">
      <!-- Header -->
      <div class="p-4 border-b border-gray-200">
        <h1 class="text-xl font-bold text-gray-900">Receipt Search</h1>
        <p class="text-sm text-gray-600">Ask me anything about your receipts</p>
      </div>

      <!-- Quick Actions -->
      <div class="p-4 space-y-2">
        <button 
          @click="startNewChat"
          class="w-full text-left p-3 text-sm text-gray-700 hover:bg-gray-50 rounded-lg border border-gray-200"
        >
          + New Chat
        </button>
        
        <button 
          @click="showUploadModal = true"
          class="w-full text-left p-3 text-sm text-blue-700 hover:bg-blue-50 rounded-lg border border-blue-200"
        >
          📤 Upload Receipt
        </button>
      </div>

      <!-- Quick Examples -->
      <div class="p-4 flex-1">
        <h3 class="text-sm font-medium text-gray-700 mb-2">Try asking:</h3>
        <div class="space-y-1">
          <button 
            v-for="example in quickExamples"
            :key="example"
            @click="sendMessage(example)"
            class="w-full text-left p-2 text-xs text-gray-600 hover:bg-gray-50 rounded"
          >
            "{{ example }}"
          </button>
        </div>
      </div>

      <!-- User Info -->
      <div class="p-4 border-t border-gray-200">
        <div class="flex items-center space-x-3">
          <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <span class="text-sm font-medium text-blue-700">
              {{ user?.email?.charAt(0).toUpperCase() }}
            </span>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">
              {{ user?.display_name || user?.email }}
            </p>
            <p class="text-xs text-gray-500">{{ user?.subscription_tier }}</p>
          </div>
          <button 
            @click="logout"
            class="text-gray-400 hover:text-gray-600"
            title="Logout"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Main Chat Area -->
    <div class="flex-1 flex flex-col">
      <!-- Chat Messages -->
      <div 
        ref="chatContainer"
        class="flex-1 overflow-y-auto p-4 chat-container"
      >
        <div class="max-w-4xl mx-auto space-y-4">
          <!-- Welcome Message -->
          <div v-if="messages.length === 0" class="text-center py-12">
            <div class="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
              <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h2 class="text-xl font-semibold text-gray-900 mb-2">Welcome to Receipt Search!</h2>
            <p class="text-gray-600 mb-6">Ask me anything about your receipts. I can help you find, organize, and analyze your expenses.</p>
          </div>

          <!-- Chat Messages -->
          <ChatMessage 
            v-for="message in messages"
            :key="message.id"
            :message="message"
          />
        </div>
      </div>

      <!-- Chat Input -->
      <div class="border-t border-gray-200 bg-white p-4">
        <div class="max-w-4xl mx-auto">
          <ChatInput 
            v-model="currentMessage"
            :is-loading="isLoading"
            @send="sendMessage"
            @upload="showUploadModal = true"
          />
        </div>
      </div>
    </div>

    <!-- Upload Modal -->
    <UploadModal 
      v-if="showUploadModal"
      @close="showUploadModal = false"
      @uploaded="handleReceiptUploaded"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { searchService } from '@/services/searchService'
import { receiptService } from '@/services/receiptService'
import ChatMessage from '@/components/ChatMessage.vue'
import ChatInput from '@/components/ChatInput.vue'
import UploadModal from '@/components/UploadModal.vue'
import { useRouter } from 'vue-router'
import type { ChatMessage as ChatMessageType, Receipt, SearchRequest } from '@/types'
import { v4 as uuidv4 } from 'uuid'

const authStore = useAuthStore()
const router = useRouter()

const messages = ref<ChatMessageType[]>([])
const currentMessage = ref('')
const isLoading = ref(false)
const showUploadModal = ref(false)
const chatContainer = ref<HTMLElement>()

const user = computed(() => authStore.user)

const quickExamples = [
  "Show me all receipts from last month",
  "Find receipts over $100",
  "What did I spend at grocery stores?",
  "Show receipts from Starbucks",
  "Find all business expenses"
]

const sendMessage = async (message?: string) => {
  const messageText = message || currentMessage.value.trim()
  if (!messageText || isLoading.value) return

  // Add user message
  const userMessage: ChatMessageType = {
    id: uuidv4(),
    type: 'user',
    content: messageText,
    timestamp: new Date()
  }
  messages.value.push(userMessage)

  // Clear input
  currentMessage.value = ''
  
  // Add loading assistant message
  const assistantMessage: ChatMessageType = {
    id: uuidv4(),
    type: 'assistant',
    content: 'Searching your receipts...',
    timestamp: new Date(),
    isLoading: true
  }
  messages.value.push(assistantMessage)

  isLoading.value = true

  try {
    // Parse user intent and search receipts
    const searchResults = await performSmartSearch(messageText)
    
    // Update assistant message with results
    const messageIndex = messages.value.findIndex(m => m.id === assistantMessage.id)
    if (messageIndex !== -1) {
      messages.value[messageIndex] = {
        ...assistantMessage,
        content: generateResponseMessage(messageText, searchResults),
        receipts: searchResults.results,
        isLoading: false
      }
    }
  } catch (error) {
    console.error('Search error:', error)
    const messageIndex = messages.value.findIndex(m => m.id === assistantMessage.id)
    if (messageIndex !== -1) {
      messages.value[messageIndex] = {
        ...assistantMessage,
        content: 'Sorry, I encountered an error while searching your receipts. Please try again.',
        isLoading: false
      }
    }
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const performSmartSearch = async (query: string): Promise<{ results: Receipt[], total: number }> => {
  const lowerQuery = query.toLowerCase()
  
  // Smart parsing of different query types
  if (lowerQuery.includes('last month') || lowerQuery.includes('this month')) {
    const now = new Date()
    const startDate = new Date(now.getFullYear(), now.getMonth() - (lowerQuery.includes('last') ? 1 : 0), 1)
    const endDate = new Date(now.getFullYear(), now.getMonth() + (lowerQuery.includes('last') ? 0 : 1), 0)
    
    return await searchService.searchByDateRange(
      startDate.toISOString().split('T')[0],
      endDate.toISOString().split('T')[0]
    )
  }
  
  // Amount search
  const amountMatch = lowerQuery.match(/over \$?(\d+)|above \$?(\d+)|more than \$?(\d+)/)
  if (amountMatch) {
    const amount = parseInt(amountMatch[1] || amountMatch[2] || amountMatch[3])
    return await searchService.searchByAmountRange(amount, 999999)
  }
  
  // Merchant search
  const merchantKeywords = ['from', 'at', 'starbucks', 'walmart', 'target', 'amazon', 'grocery', 'restaurant']
  const merchantMatch = merchantKeywords.find(keyword => lowerQuery.includes(keyword))
  if (merchantMatch && merchantMatch !== 'from' && merchantMatch !== 'at') {
    return await searchService.searchByMerchant(merchantMatch)
  }
  
  // Default text search
  const searchRequest: SearchRequest = {
    query: query,
    limit: 20,
    offset: 0
  }
  
  return await searchService.searchReceipts(searchRequest)
}

const generateResponseMessage = (query: string, results: { results: Receipt[], total: number }): string => {
  const { results: receipts, total } = results
  
  if (total === 0) {
    return `I couldn't find any receipts matching "${query}". Try a different search or upload some receipts first.`
  }
  
  const totalAmount = receipts.reduce((sum, receipt) => sum + receipt.amount, 0)
  
  let message = `I found ${total} receipt${total === 1 ? '' : 's'} matching "${query}".`
  
  if (receipts.length > 0) {
    message += ` The total amount is $${totalAmount.toFixed(2)}.`
    
    if (total > receipts.length) {
      message += ` Showing the first ${receipts.length} results.`
    }
  }
  
  return message
}

const startNewChat = () => {
  messages.value = []
}

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}

const handleReceiptUploaded = (receipt: Receipt) => {
  showUploadModal.value = false
  
  // Add a message about the successful upload
  const message: ChatMessageType = {
    id: uuidv4(),
    type: 'assistant',
    content: `Successfully uploaded receipt from ${receipt.merchant_name} for $${receipt.amount.toFixed(2)}! You can now search for it.`,
    timestamp: new Date(),
    receipts: [receipt]
  }
  messages.value.push(message)
  scrollToBottom()
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

onMounted(() => {
  scrollToBottom()
})
</script>