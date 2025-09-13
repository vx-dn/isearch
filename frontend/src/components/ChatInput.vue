<template>
  <div class="flex space-x-3">
    <!-- Text Input -->
    <div class="flex-1 relative">
      <input
        ref="inputRef"
        v-model="message"
        type="text"
        placeholder="Ask about your receipts... (e.g., 'Show me all receipts from last month')"
        class="chat-input"
        :disabled="isLoading"
        @keypress.enter="handleSend"
        @keydown="handleKeyDown"
      />
      
      <!-- Suggestions Dropdown -->
      <div 
        v-if="showSuggestions && suggestions.length > 0"
        class="absolute z-10 w-full bg-white border border-gray-300 rounded-lg shadow-lg mt-1 max-h-40 overflow-y-auto"
      >
        <button
          v-for="(suggestion, index) in suggestions"
          :key="index"
          @click="selectSuggestion(suggestion)"
          class="w-full text-left px-4 py-2 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
        >
          {{ suggestion }}
        </button>
      </div>
    </div>

    <!-- Upload Button -->
    <button
      @click="$emit('upload')"
      class="p-3 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg border border-gray-300"
      title="Upload receipt"
      :disabled="isLoading"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
    </button>

    <!-- Send Button -->
    <button
      @click="handleSend"
      :disabled="!message.trim() || isLoading"
      class="p-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <svg 
        v-if="isLoading"
        class="w-5 h-5 animate-spin" 
        xmlns="http://www.w3.org/2000/svg" 
        fill="none" 
        viewBox="0 0 24 24"
      >
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <svg 
        v-else
        class="w-5 h-5" 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { searchService } from '@/services/searchService'

const props = defineProps<{
  modelValue: string
  isLoading: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'send': [message: string]
  'upload': []
}>()

const message = ref('')
const suggestions = ref<string[]>([])
const showSuggestions = ref(false)
const inputRef = ref<HTMLInputElement>()
const suggestionTimeout = ref<number>()

// Sync with v-model
watch(() => props.modelValue, (newValue) => {
  message.value = newValue
})

watch(message, (newValue) => {
  emit('update:modelValue', newValue)
  
  // Clear previous timeout
  if (suggestionTimeout.value) {
    clearTimeout(suggestionTimeout.value)
  }
  
  // Debounce suggestions
  if (newValue.trim().length > 2) {
    suggestionTimeout.value = setTimeout(() => {
      getSuggestions(newValue)
    }, 300) as unknown as number
  } else {
    showSuggestions.value = false
  }
})

const getSuggestions = async (query: string) => {
  try {
    const results = await searchService.getSuggestions(query, 5)
    suggestions.value = results
    showSuggestions.value = results.length > 0
  } catch (error) {
    console.error('Failed to get suggestions:', error)
    showSuggestions.value = false
  }
}

const selectSuggestion = (suggestion: string) => {
  message.value = suggestion
  emit('update:modelValue', suggestion)
  showSuggestions.value = false
  inputRef.value?.focus()
}

const handleSend = () => {
  if (message.value.trim() && !props.isLoading) {
    emit('send', message.value.trim())
    message.value = ''
    emit('update:modelValue', '')
    showSuggestions.value = false
  }
}

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    showSuggestions.value = false
  }
}

// Handle click outside to close suggestions
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as Element
  if (inputRef.value && !inputRef.value.contains(target)) {
    showSuggestions.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (suggestionTimeout.value) {
    clearTimeout(suggestionTimeout.value)
  }
})
</script>