# GCP Stimulator UI

A modern React + TypeScript UI for the GCP Stimulator backend, providing a Google Cloud Console-like interface for managing Storage, Compute Engine, VPC Networks, and IAM resources.

## 🚀 Tech Stack

- **React 18.2** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Material-UI v5** - Google Cloud-inspired design system
- **React Router v6** - Client-side routing
- **React Query (TanStack Query)** - Data fetching and caching
- **Zustand** - Lightweight state management
- **React Hook Form + Zod** - Form validation
- **Axios** - HTTP client with interceptors
- **React Toastify** - Toast notifications
- **Vitest** - Unit and integration testing
- **Cypress** - End-to-end testing

## 📁 Project Structure

```
gcp-stimulator-ui/
├── src/
│   ├── api/                    # API client and endpoints
│   │   └── client.ts
│   ├── components/             # Reusable components
│   │   ├── common/
│   │   ├── storage/
│   │   ├── compute/
│   │   ├── vpc/
│   │   ├── iam/
│   │   └── navigation/
│   ├── hooks/                  # Custom React hooks
│   ├── layouts/                # Layout components
│   │   └── Layout.tsx
│   ├── pages/                  # Page components
│   │   ├── Dashboard.tsx
│   │   ├── storage/
│   │   ├── compute/
│   │   ├── vpc/
│   │   └── iam/
│   ├── stores/                 # Zustand stores
│   │   └── projectStore.ts
│   ├── types/                  # TypeScript types
│   ├── utils/                  # Utility functions
│   ├── schemas/                # Zod validation schemas
│   ├── routes.tsx              # Route configuration
│   ├── App.tsx                 # Root component
│   ├── main.tsx                # Entry point
│   └── index.css               # Global styles
├── test/                       # Test utilities
├── cypress/                    # E2E tests
├── public/                     # Static assets
├── index.html                  # HTML entry point
├── package.json
├── tsconfig.json
├── vite.config.ts
└── vitest.config.ts
```

## 🛠️ Setup

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running on http://localhost:8080

### Installation

```bash
# Navigate to UI directory
cd /home/ubuntu/gcs-stimulator/gcp-stimulator-ui

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will open at http://localhost:5173

### Environment Variables

Create or update `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8080
VITE_PROJECT_ID=test-project
```

## 📜 Available Scripts

### Development

```bash
# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Testing

```bash
# Run unit tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Open Cypress UI
npm run test:e2e:ui
```

### Linting

```bash
# Run ESLint
npm run lint

# Fix ESLint issues
npm run lint:fix
```

## 🎯 Features (Planned)

### Dashboard
- ✅ Resource count cards (Storage, Compute, VPC, IAM)
- 🔄 Recent activity feed (last 50 operations)
- 🔄 Quick action buttons
- 🔄 Real-time updates via polling

### Cloud Storage
- 🔄 Bucket list with search and filter
- 🔄 Create/delete buckets
- 🔄 Bucket details with tabs (Objects, Configuration, Permissions, Lifecycle)
- 🔄 Upload/download files with progress bar
- 🔄 IAM policy management

### Compute Engine
- 🔄 VM instance list with status polling
- 🔄 Create instance with form validation
- 🔄 Start/stop/delete instances
- 🔄 Instance details with tabs
- 🔄 Machine type and network selection

### VPC Network
- 🔄 Network list and details
- 🔄 Subnet management
- 🔄 Firewall rule creation and management
- 🔄 Route management

### IAM & Admin
- 🔄 Service account list and details
- 🔄 Service account key generation
- 🔄 IAM policy management
- 🔄 Role browser

## 🧪 Testing

### Unit Tests (Target: 80% coverage)

```bash
npm run test -- src/components/common/
```

### Integration Tests (Target: 70% coverage)

```bash
npm run test -- src/pages/
```

### E2E Tests (Target: 50% of critical paths)

```bash
npm run test:e2e
```

## 🎨 Design System

### Colors
- **Primary**: #1976d2 (GCP Blue)
- **Secondary**: #757575 (Gray)
- **Success**: #4caf50 (Green)
- **Error**: #f44336 (Red)
- **Warning**: #ff9800 (Orange)

### Typography
- **Font**: Roboto
- **Headings**: 24px/20px/16px
- **Body**: 14px
- **Small**: 12px

## 📊 Current Implementation Status

**Overall Progress: 20%**

✅ **Completed:**
- Project setup and configuration
- Dependencies installed
- TypeScript configuration
- Vite build setup
- Routing configuration
- API client with interceptors
- State management setup
- Layout structure
- Placeholder pages

🔄 **In Progress:**
- Page implementations
- Component library
- API integration
- Form validation
- Testing

See [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) for detailed progress tracking.

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

Build output will be in `dist/` directory.

### Docker Deployment

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 📝 Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Run linting and tests
5. Submit a pull request

## 📄 License

MIT

## 🔗 Related Documentation

- [UI Specification](../UI_SPECIFICATION.md) - Complete UI requirements
- [Implementation Status](./IMPLEMENTATION_STATUS.md) - Detailed progress tracking
- [Backend API Documentation](../gcp-stimulator-package/README.md)

---

**Status**: 🏗️ Under Development  
**Last Updated**: January 30, 2026
