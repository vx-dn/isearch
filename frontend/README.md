# Receipt Search Frontend

A modern Vue.js frontend for the receipt search application with a ChatGPT-like interface.

## Features

- 🤖 **ChatGPT-like Interface**: Natural language queries for receipt search
- 📸 **Image Upload**: Upload receipt images with automatic text extraction
- 🔍 **Smart Search**: Search by merchant, date range, amount, tags, and more
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🎨 **Modern UI**: Clean, intuitive interface with Tailwind CSS
- 🔐 **Secure Authentication**: JWT-based auth with user management

## Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Pinia** - State management
- **Vue Router** - Client-side routing
- **Axios** - HTTP client for API calls

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running (see backend README)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Copy environment file:
```bash
cp .env.example .env.local
```

3. Update environment variables in `.env.local`:
```env
VITE_API_URL=http://localhost:8000  # Your backend API URL
```

4. Start development server:
```bash
npm run dev
```

5. Open http://localhost:3000 in your browser

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` folder.

## Project Structure

```
src/
├── components/          # Reusable Vue components
│   ├── ChatInput.vue   # Chat input with suggestions
│   ├── ChatMessage.vue # Message bubbles
│   ├── ReceiptCard.vue # Receipt display cards
│   └── UploadModal.vue # File upload modal
├── services/           # API service layer
│   ├── apiClient.ts    # HTTP client setup
│   ├── authService.ts  # Authentication API
│   ├── receiptService.ts # Receipt management API
│   └── searchService.ts # Search functionality API
├── stores/             # Pinia state management
│   └── auth.ts        # Authentication state
├── types/              # TypeScript type definitions
├── views/              # Page components
│   ├── ChatView.vue    # Main chat interface
│   ├── LoginView.vue   # Login page
│   └── RegisterView.vue # Registration page
├── router/             # Vue Router configuration
└── style.css          # Global styles
```

## Usage

### Chat Interface

The main interface works like ChatGPT where you can ask natural language questions about your receipts:

- "Show me all receipts from last month"
- "Find receipts over $100"
- "What did I spend at grocery stores?"
- "Show receipts from Starbucks"
- "Find all business expenses"

### Receipt Upload

You can upload receipts in two ways:

1. **Image Upload**: Take a photo or upload an image - the system will automatically extract the data
2. **Manual Entry**: Enter receipt details manually

### Search Features

- **Text Search**: Search across merchant names, items, and extracted text
- **Date Range**: Find receipts within specific date ranges
- **Amount Range**: Filter by spending amounts
- **Merchant**: Search by specific merchants
- **Tags**: Organize and search by custom tags
- **Categories**: Filter by receipt types (grocery, restaurant, etc.)

## API Integration

The frontend communicates with the FastAPI backend through:

- **Authentication**: `/auth/*` endpoints for login/register
- **Receipts**: `/receipts/*` endpoints for CRUD operations
- **Search**: `/search/*` endpoints for various search methods
- **Image Processing**: S3 upload and processing workflows

## Development

### Adding New Components

1. Create component in `src/components/`
2. Export types in `src/types/index.ts` if needed
3. Add API methods to appropriate service
4. Update state management if needed

### Styling

The project uses Tailwind CSS with custom components defined in `src/style.css`. Follow the existing patterns for consistency.

### State Management

Pinia stores are used for:
- Authentication state (`stores/auth.ts`)
- Add more stores as needed for other features

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.