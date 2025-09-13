<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Upload Receipt</h2>
        <button 
          @click="$emit('close')"
          class="text-gray-400 hover:text-gray-600"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Upload Methods -->
      <div class="p-6">
        <div class="space-y-4">
          <!-- Image Upload -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Upload Receipt Image
            </label>
            <div 
              @drop="handleDrop"
              @dragover.prevent
              @dragenter.prevent
              class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors"
              :class="{ 'border-blue-400 bg-blue-50': isDragging }"
            >
              <input
                ref="fileInput"
                type="file"
                accept="image/*"
                @change="handleFileSelect"
                class="hidden"
              />
              
              <div v-if="!selectedFile">
                <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <div class="mt-4">
                  <button 
                    @click="$refs.fileInput.click()"
                    class="text-blue-600 hover:text-blue-500"
                  >
                    Click to upload
                  </button>
                  <p class="text-gray-500">or drag and drop</p>
                </div>
                <p class="text-xs text-gray-400 mt-2">PNG, JPG, GIF up to 10MB</p>
              </div>

              <div v-else class="space-y-3">
                <div class="w-24 h-24 mx-auto bg-gray-100 rounded-lg flex items-center justify-center">
                  <img 
                    v-if="imagePreview"
                    :src="imagePreview" 
                    alt="Preview"
                    class="w-full h-full object-cover rounded-lg"
                  />
                  <svg v-else class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <p class="text-sm text-gray-600">{{ selectedFile.name }}</p>
                <button 
                  @click="clearFile"
                  class="text-sm text-red-600 hover:text-red-500"
                >
                  Remove
                </button>
              </div>
            </div>
          </div>

          <!-- OR Manual Entry -->
          <div class="relative">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-gray-300" />
            </div>
            <div class="relative flex justify-center text-sm">
              <span class="px-2 bg-white text-gray-500">Or enter manually</span>
            </div>
          </div>

          <!-- Manual Form -->
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Merchant Name</label>
              <input
                v-model="manualReceipt.merchant_name"
                type="text"
                class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., Starbucks"
              />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Amount</label>
                <input
                  v-model.number="manualReceipt.amount"
                  type="number"
                  step="0.01"
                  class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  placeholder="0.00"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Date</label>
                <input
                  v-model="manualReceipt.date"
                  type="date"
                  class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Type</label>
              <select
                v-model="manualReceipt.receipt_type"
                class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="grocery">Grocery</option>
                <option value="restaurant">Restaurant</option>
                <option value="gas">Gas</option>
                <option value="retail">Retail</option>
                <option value="medical">Medical</option>
                <option value="business">Business</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Tags (optional)</label>
              <input
                v-model="tagsInput"
                type="text"
                class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="food, lunch, business (comma separated)"
              />
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="text-red-600 text-sm">
            {{ error }}
          </div>

          <!-- Upload Progress -->
          <div v-if="isUploading" class="space-y-2">
            <div class="flex items-center text-sm text-gray-600">
              <svg class="animate-spin -ml-1 mr-3 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ uploadStatus }}
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div 
                class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                :style="{ width: `${uploadProgress}%` }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex justify-end space-x-3 p-6 border-t border-gray-200">
        <button 
          @click="$emit('close')"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
          :disabled="isUploading"
        >
          Cancel
        </button>
        <button 
          @click="handleUpload"
          :disabled="!canUpload || isUploading"
          class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ isUploading ? 'Uploading...' : 'Upload' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { receiptService } from '@/services/receiptService'
import type { Receipt, ReceiptCreateRequest } from '@/types'

defineEmits<{
  close: []
  uploaded: [receipt: Receipt]
}>()

// Define emit function properly
const emit = defineEmits<{
  close: []
  uploaded: [receipt: Receipt]
}>()

const selectedFile = ref<File | null>(null)
const imagePreview = ref<string | null>(null)
const isDragging = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const error = ref('')
const tagsInput = ref('')

const manualReceipt = reactive<ReceiptCreateRequest>({
  merchant_name: '',
  amount: 0,
  date: new Date().toISOString().split('T')[0],
  receipt_type: 'other',
  currency: 'USD'
})

const canUpload = computed(() => {
  return selectedFile.value || (manualReceipt.merchant_name && manualReceipt.amount > 0)
})

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    setSelectedFile(target.files[0])
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = false
  
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    setSelectedFile(event.dataTransfer.files[0])
  }
}

const setSelectedFile = (file: File) => {
  if (file.size > 10 * 1024 * 1024) {
    error.value = 'File size must be less than 10MB'
    return
  }
  
  if (!file.type.startsWith('image/')) {
    error.value = 'Please select an image file'
    return
  }
  
  selectedFile.value = file
  error.value = ''
  
  // Create preview
  const reader = new FileReader()
  reader.onload = (e) => {
    imagePreview.value = e.target?.result as string
  }
  reader.readAsDataURL(file)
}

const clearFile = () => {
  selectedFile.value = null
  imagePreview.value = null
}

const handleUpload = async () => {
  error.value = ''
  isUploading.value = true
  uploadProgress.value = 0
  
  try {
    if (selectedFile.value) {
      await uploadImage()
    } else {
      await createManualReceipt()
    }
  } catch (err: any) {
    error.value = err.message || 'Upload failed'
  } finally {
    isUploading.value = false
    uploadProgress.value = 0
    uploadStatus.value = ''
  }
}

const uploadImage = async () => {
  if (!selectedFile.value) return
  
  uploadStatus.value = 'Getting upload URL...'
  uploadProgress.value = 10
  
  // Get presigned URL
  const uploadResponse = await receiptService.generateUploadUrl()
  uploadProgress.value = 20
  
  uploadStatus.value = 'Uploading image...'
  
  // Upload to S3
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  
  const uploadResult = await fetch(uploadResponse.upload_url, {
    method: 'POST',
    body: formData
  })
  
  if (!uploadResult.ok) {
    throw new Error('Failed to upload image')
  }
  
  uploadProgress.value = 70
  uploadStatus.value = 'Processing receipt...'
  
  // Start processing
  const processingResponse = await receiptService.processImage(uploadResponse.image_id)
  uploadProgress.value = 80
  
  // Poll for completion
  let attempts = 0
  const maxAttempts = 30
  
  while (attempts < maxAttempts) {
    uploadStatus.value = 'Extracting receipt data...'
    const status = await receiptService.getProcessingStatus(uploadResponse.image_id)
    
    if (status.status === 'completed' && status.receipt) {
      uploadProgress.value = 100
      uploadStatus.value = 'Complete!'
      
      setTimeout(() => {
        emit('uploaded', status.receipt!)
      }, 500)
      return
    } else if (status.status === 'failed') {
      throw new Error(status.error_message || 'Image processing failed')
    }
    
    attempts++
    uploadProgress.value = 80 + (attempts / maxAttempts) * 15
    
    await new Promise(resolve => setTimeout(resolve, 2000))
  }
  
  throw new Error('Processing timeout - please try again')
}

const createManualReceipt = async () => {
  uploadStatus.value = 'Creating receipt...'
  uploadProgress.value = 50
  
  const receiptData: ReceiptCreateRequest = {
    ...manualReceipt,
    tags: tagsInput.value ? tagsInput.value.split(',').map(tag => tag.trim()) : undefined
  }
  
  const receipt = await receiptService.createReceipt(receiptData)
  
  uploadProgress.value = 100
  uploadStatus.value = 'Complete!'
  
  setTimeout(() => {
    emit('uploaded', receipt)
  }, 500)
}
</script>