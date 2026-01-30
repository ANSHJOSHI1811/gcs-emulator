# 🎯 GCP Simulator UI - Complete Specification

## 📋 Quick Overview

**Mission:** Build a GCP Console-like UI that covers Storage, Compute, VPC, and IAM with full CRUD operations and proper testing.

**Tech Stack:** React + TypeScript + Vite + Material-UI + React Router + React Query + Vitest + Cypress

---

## 🏗️ Pages Required

### 1. **Dashboard (Home)**
- Project selector dropdown (top navigation)
- Resource count cards (Storage, Compute, VPC, IAM)
- Recent activity feed (last 50 operations)
- Quick action buttons (Create VM, Create Bucket, Create Network, Create Service Account)
- Real-time updates via polling every 5 seconds
- Resource usage graphs (optional)

**APIs:**
- `GET /projects` - List all projects
- `GET /storage/v1/b?project={project}` - Count buckets
- `GET /compute/v1/projects/{project}/aggregated/instances` - Count instances
- `GET /compute/v1/projects/{project}/global/networks` - Count networks
- `GET /iam/v1/projects/{project}/serviceAccounts` - Count service accounts
- `GET /operations?project={project}&limit=50` - Recent operations

**State:**
- Selected project ID
- Resource counts (buckets, instances, networks, service accounts)
- Recent operations list

---

### 2. **Cloud Storage**

#### **Bucket List Page** (`/storage`)
- **Table Columns:** Name, Location, Storage Class, Size (formatted), Created, Actions
- **Features:**
  - Search/filter by name, location, storage class
  - Create Bucket button (opens modal)
  - Delete bucket button (with confirmation)
  - Multi-select for bulk delete operations
  - Sort by name/size/created date
  - Pagination (50 items per page)
  - Click row to navigate to bucket details

**APIs:**
- `GET /storage/v1/b?project={project}` - List buckets
- `POST /storage/v1/b?project={project}` - Create bucket
- `DELETE /storage/v1/b/{bucket}` - Delete bucket

**State:**
- Bucket list
- Search query
- Selected buckets (for bulk operations)
- Sort column and direction

#### **Bucket Details Page** (`/storage/:bucketName`)
- **Tabs:** Objects, Configuration, Permissions, Lifecycle
- **Breadcrumb:** Storage > Bucket Name

**Objects Tab:**
- File browser with folder support (prefix-based)
- Upload file button (drag-drop zone + file picker)
- Upload progress bar with cancel button
- Create folder button
- Download file button
- Delete file/folder button (with confirmation)
- File preview for text/images (optional)
- Pagination (100 items per page)

**APIs:**
- `GET /storage/v1/b/{bucket}/o?prefix={prefix}` - List objects
- `POST /storage/v1/b/{bucket}/o` - Upload object (multipart)
- `GET /storage/v1/b/{bucket}/o/{object}?alt=media` - Download object
- `DELETE /storage/v1/b/{bucket}/o/{object}` - Delete object

**Configuration Tab:**
- Bucket location (read-only)
- Storage class (editable dropdown)
- Versioning (toggle)
- Default event-based hold (toggle)
- Retention policy (optional)
- Save button to update configuration

**APIs:**
- `GET /storage/v1/b/{bucket}` - Get bucket metadata
- `PATCH /storage/v1/b/{bucket}` - Update bucket

**Permissions Tab:**
- IAM policy table (Principal, Role, Actions)
- Grant Access button (opens modal)
- Remove access button
- Make Public / Make Private quick actions

**APIs:**
- `GET /storage/v1/b/{bucket}/iam` - Get IAM policy
- `PUT /storage/v1/b/{bucket}/iam` - Set IAM policy

**Lifecycle Tab:**
- Lifecycle rules table (Action, Condition, Status)
- Add Rule button (opens modal)
- Delete rule button
- Enable/disable rule toggle

**APIs:**
- `GET /storage/v1/b/{bucket}` - Get lifecycle rules
- `PATCH /storage/v1/b/{bucket}` - Update lifecycle rules

---

### 3. **Compute Engine**

#### **VM Instance List Page** (`/compute/instances`)
- **Table Columns:** Name, Zone, Status (🟢Running/🔴Stopped/🟡Starting), Machine Type, Internal IP, External IP, Actions
- **Features:**
  - Real-time status polling every 5s
  - Filter by zone, status, labels
  - Search by name
  - Quick actions: Start, Stop, Restart, Delete
  - Multi-select for bulk operations (start all, stop all, delete all)
  - Create Instance button
  - Pagination (50 items per page)

**APIs:**
- `GET /compute/v1/projects/{project}/aggregated/instances` - List all instances
- `GET /compute/v1/projects/{project}/zones/{zone}/instances` - List instances in zone
- `POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/start` - Start instance
- `POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/stop` - Stop instance
- `POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/reset` - Restart instance
- `DELETE /compute/v1/projects/{project}/zones/{zone}/instances/{instance}` - Delete instance

**State:**
- Instance list with status
- Filter criteria (zone, status, search query)
- Selected instances (for bulk operations)
- Polling interval handle

#### **Create Instance Page** (`/compute/instances/create`)
- **Form Fields:**
  - Name (required, alphanumeric + hyphens)
  - Zone (required, dropdown with all zones)
  - Machine Type (required, dropdown: e2-micro, e2-small, e2-medium, n1-standard-1, etc.)
  - Boot Disk:
    - Image (dropdown: ubuntu-2004, debian-11, centos-7, etc.)
    - Size (GB, default 10)
  - Network (required, dropdown of existing networks)
  - Subnet (required, dropdown filtered by zone)
  - External IP (toggle: None, Ephemeral, Static)
  - Service Account (dropdown: None, Compute default, Custom)
  - Scopes (if service account selected): Allow full access to all Cloud APIs
  - Network Tags (comma-separated)
  - Firewall:
    - [ ] Allow HTTP traffic
    - [ ] Allow HTTPS traffic
  - Startup Script (optional, textarea)
  - Labels (key-value pairs, add/remove buttons)

**Validation:**
- Name: 1-63 chars, lowercase, start with letter, hyphens allowed
- Machine type: required
- Network: required
- Subnet: required, must be in selected zone

**APIs:**
- `GET /compute/v1/projects/{project}/zones` - List zones
- `GET /compute/v1/projects/{project}/zones/{zone}/machineTypes` - List machine types
- `GET /compute/v1/projects/{project}/global/networks` - List networks
- `GET /compute/v1/projects/{project}/regions/{region}/subnetworks` - List subnets
- `GET /iam/v1/projects/{project}/serviceAccounts` - List service accounts
- `POST /compute/v1/projects/{project}/zones/{zone}/instances` - Create instance

**State:**
- Form data
- Validation errors
- Available zones, machine types, networks, subnets, service accounts
- Form submission status

#### **Instance Details Page** (`/compute/instances/:zone/:name`)
- **Tabs:** Details, Monitoring, Logs
- **Breadcrumb:** Compute Engine > VM Instances > Instance Name
- **Actions Bar:** Start, Stop, Restart, Delete, Edit buttons

**Details Tab:**
- Status with icon (🟢Running/🔴Stopped)
- Machine Type
- Zone
- Internal IP
- External IP
- Network
- Subnet
- Service Account
- Scopes
- Disk (name, size, type)
- Network Tags
- Labels (key-value list)
- Firewall Rules applied (list)
- Created timestamp

**APIs:**
- `GET /compute/v1/projects/{project}/zones/{zone}/instances/{instance}` - Get instance details

**Monitoring Tab:**
- CPU usage graph (last 1 hour)
- Memory usage graph
- Disk I/O graph
- Network I/O graph
- Uptime

**APIs:**
- `GET /monitoring/v3/projects/{project}/timeSeries` - Get metrics (optional, can be mocked)

**Logs Tab:**
- Serial port output (last 100 lines)
- Refresh button

**APIs:**
- `GET /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/serialPort?port=1` - Get serial output

---

### 4. **VPC Network**

#### **VPC Networks List Page** (`/vpc/networks`)
- **Table Columns:** Name, Subnets Count, Mode (Auto/Custom), Firewall Rules Count, Created, Actions
- **Features:**
  - Create Network button
  - Delete network button (with confirmation)
  - Search by name
  - Click row to navigate to network details
  - Pagination (50 items per page)

**APIs:**
- `GET /compute/v1/projects/{project}/global/networks` - List networks
- `POST /compute/v1/projects/{project}/global/networks` - Create network
- `DELETE /compute/v1/projects/{project}/global/networks/{network}` - Delete network

**State:**
- Network list
- Search query

#### **Network Details Page** (`/vpc/networks/:name`)
- **Tabs:** Subnets, Firewall Rules, Routes, Details
- **Breadcrumb:** VPC Network > Network Name
- **Actions Bar:** Delete Network button

**Subnets Tab:**
- Table: Name, Region, IP Range, Gateway, Private Google Access, Flow Logs
- Add Subnet button (opens modal)
- Delete subnet button (with confirmation)
- Edit subnet button (opens modal)

**APIs:**
- `GET /compute/v1/projects/{project}/aggregated/subnetworks?filter=network={network}` - List subnets
- `POST /compute/v1/projects/{project}/regions/{region}/subnetworks` - Create subnet
- `PATCH /compute/v1/projects/{project}/regions/{region}/subnetworks/{subnet}` - Update subnet
- `DELETE /compute/v1/projects/{project}/regions/{region}/subnetworks/{subnet}` - Delete subnet

**Firewall Rules Tab:**
- Table: Name, Type, Targets, Filters (Source), Protocols/Ports, Priority, Action
- Create Firewall Rule button (navigates to create page)
- Delete rule button (with confirmation)
- Enable/Disable rule toggle
- Filter by ingress/egress, allow/deny

**APIs:**
- `GET /compute/v1/projects/{project}/global/firewalls?filter=network={network}` - List firewall rules
- `DELETE /compute/v1/projects/{project}/global/firewalls/{firewall}` - Delete firewall

**Routes Tab:**
- Table: Name, Destination IP Range, Next Hop, Priority
- Create Route button (opens modal)
- Delete route button

**APIs:**
- `GET /compute/v1/projects/{project}/global/routes?filter=network={network}` - List routes

**Details Tab:**
- Network name (read-only)
- Mode (Auto/Custom, read-only)
- Subnet creation mode (read-only)
- Created timestamp
- Description (editable)

**APIs:**
- `GET /compute/v1/projects/{project}/global/networks/{network}` - Get network details

#### **Create Firewall Rule Page** (`/vpc/firewalls/create`)
- **Form Fields:**
  - Name (required, alphanumeric + hyphens)
  - Description (optional)
  - Network (required, dropdown of existing networks)
  - Priority (required, 0-65535, default 1000)
  - Direction (required, radio: Ingress / Egress)
  - Action (required, radio: Allow / Deny)
  - Targets (required, radio):
    - All instances in network
    - Specified target tags
    - Specified service account
  - Target tags (if "target tags" selected, comma-separated)
  - Target service account (if "service account" selected, dropdown)
  - Source filter (for Ingress, radio):
    - IP ranges (text input, comma-separated CIDR)
    - Source tags (text input, comma-separated)
    - Source service account (dropdown)
  - Destination filter (for Egress, same as source filter)
  - Protocols and ports:
    - [ ] Allow all protocols and ports
    - Or specify:
      - TCP ports (comma-separated or ranges: 80, 443, 8000-9000)
      - UDP ports (same format)
      - Other protocols (ICMP, etc.)
  - Enforcement (toggle: Enabled / Disabled)

**Validation:**
- Name: 1-63 chars, lowercase, start with letter
- Priority: 0-65535
- IP ranges: valid CIDR notation
- Port ranges: valid format (1-65535, ranges allowed)

**APIs:**
- `GET /compute/v1/projects/{project}/global/networks` - List networks
- `GET /iam/v1/projects/{project}/serviceAccounts` - List service accounts
- `POST /compute/v1/projects/{project}/global/firewalls` - Create firewall rule

**State:**
- Form data
- Validation errors
- Available networks, service accounts
- Form submission status

---

### 5. **IAM & Admin**

#### **Service Accounts List Page** (`/iam/serviceAccounts`)
- **Table Columns:** Name, Email, Status (Enabled/Disabled), Keys Count, Created, Actions
- **Features:**
  - Create Service Account button (opens modal)
  - Delete service account button (with confirmation)
  - Search by name or email
  - Actions menu: Manage Keys, Grant Access, Enable/Disable
  - Click row to navigate to service account details
  - Pagination (50 items per page)

**APIs:**
- `GET /iam/v1/projects/{project}/serviceAccounts` - List service accounts
- `POST /iam/v1/projects/{project}/serviceAccounts` - Create service account
- `DELETE /iam/v1/projects/{project}/serviceAccounts/{email}` - Delete service account
- `PATCH /iam/v1/projects/{project}/serviceAccounts/{email}` - Enable/disable service account

**State:**
- Service account list
- Search query

#### **Service Account Details Page** (`/iam/serviceAccounts/:email`)
- **Tabs:** Keys, Permissions, Details
- **Breadcrumb:** IAM & Admin > Service Accounts > Service Account Name
- **Actions Bar:** Delete Service Account, Enable/Disable buttons

**Keys Tab:**
- Table: Key ID, Type (JSON/P12), Created, Expires, Status
- Create Key button (opens modal with type selection)
- Delete key button (with confirmation)
- Download key button (only within 5 minutes of creation)

**APIs:**
- `GET /iam/v1/projects/{project}/serviceAccounts/{email}/keys` - List keys
- `POST /iam/v1/projects/{project}/serviceAccounts/{email}/keys` - Create key
- `DELETE /iam/v1/projects/{project}/serviceAccounts/{email}/keys/{keyId}` - Delete key

**Permissions Tab:**
- Table: Resource Type, Resource Name, Roles
- Grant Access button (opens modal)
- Revoke access button

**APIs:**
- `GET /iam/v1/projects/{project}/serviceAccounts/{email}/roles` - Get roles (custom endpoint)

**Details Tab:**
- Service account name
- Email (read-only)
- Project ID (read-only)
- Unique ID (read-only)
- Created timestamp
- Description (editable)

**APIs:**
- `GET /iam/v1/projects/{project}/serviceAccounts/{email}` - Get service account details
- `PATCH /iam/v1/projects/{project}/serviceAccounts/{email}` - Update description

#### **IAM Policies Page** (`/iam/policies`)
- **Table Columns:** Principal (user/SA email), Role, Resource Type, Actions
- **Features:**
  - Grant Access button (opens modal)
  - Remove access button (with confirmation)
  - Filter by principal type (User, Service Account)
  - Filter by role
  - Search by principal email or role name
  - Pagination (50 items per page)

**APIs:**
- `GET /projects/{project}/iam` - Get project IAM policy
- `POST /projects/{project}/iam` - Set project IAM policy (add/remove bindings)

**State:**
- IAM policy bindings
- Filter criteria
- Search query

#### **Roles Page** (`/iam/roles`)
- **Table Columns:** Role Name, Title, Type (Predefined/Custom), Service, Permissions Count, Actions
- **Features:**
  - Filter by type (Predefined/Custom)
  - Filter by service (Compute, Storage, IAM, etc.)
  - Search by role name or title
  - View permissions button (opens modal showing all permissions)
  - Create Custom Role button (for custom roles)
  - Delete role button (for custom roles only)
  - Pagination (100 items per page)

**APIs:**
- `GET /iam/v1/roles` - List all roles
- `GET /iam/v1/roles/{roleId}` - Get role details with permissions

**State:**
- Roles list
- Filter criteria (type, service)
- Search query

---

## 🎨 Common UI Components

### **Required Components**

#### 1. **Loading States**
- **Skeleton Loaders:** For tables, cards, forms (Material-UI Skeleton)
- **Spinners:** For button actions, full-page loading
- **Progress Bars:** For file uploads, long operations

#### 2. **Error Handling**
- **Error Alert:** Red banner with error message and retry button
- **Empty State:** Icon + message for empty lists ("No resources yet")
- **Toast Notifications:** Success (green), Error (red), Info (blue), Warning (yellow)
  - Position: Top-right corner
  - Auto-dismiss after 5s (error: 10s)
  - Close button

#### 3. **Confirmation Dialogs**
- **Delete Confirmation:** "Are you sure you want to delete {resource}?"
- **Destructive Action Warning:** "This action cannot be undone"
- **Buttons:** Cancel (secondary), Confirm (danger red)

#### 4. **Forms**
- **Text Input:** With validation error messages below
- **Dropdown/Select:** With search support for long lists
- **Multi-select:** With chips for selected items
- **Checkbox/Toggle:** For boolean options
- **File Upload:** Drag-drop zone with file picker fallback
- **Textarea:** For scripts, descriptions
- **Key-Value Editor:** For labels, metadata (add/remove rows)

#### 5. **Tables**
- **Sortable Columns:** Click header to sort
- **Pagination:** Show 50/100 per page, page selector
- **Multi-select:** Checkboxes in first column, "Select All" header
- **Action Menu:** Three-dot menu in last column
- **Row Click:** Navigate to details page
- **Empty State:** Show when no data

#### 6. **Notifications**
- **Toast Component:** Using react-toastify or similar
- **Types:** success, error, info, warning
- **Position:** top-right
- **Duration:** 5s default, 10s for errors

#### 7. **Modals**
- **Create/Edit Modals:** Form in dialog
- **Confirmation Modals:** Simple yes/no dialog
- **Info Modals:** Display additional information
- **Size:** Small (400px), Medium (600px), Large (800px)

### **Design System**

#### **Colors**
- **Primary:** Blue (#1976d2) - GCP blue
- **Secondary:** Gray (#757575)
- **Success:** Green (#4caf50)
- **Error:** Red (#f44336)
- **Warning:** Orange (#ff9800)
- **Info:** Light Blue (#2196f3)
- **Background:** White (#ffffff)
- **Surface:** Light Gray (#f5f5f5)

#### **Typography**
- **Font:** Roboto (Google's official font)
- **Headings:** 24px/20px/16px (h1/h2/h3)
- **Body:** 14px
- **Small:** 12px

#### **Icons**
- Material Icons library
- Storage: 📁 folder, 💾 save
- Compute: 🖥️ computer, ▶️ start, ⏸️ stop
- Network: 🌐 public, 🔒 lock
- IAM: 👤 person, 🔑 key

#### **Spacing**
- Base unit: 8px
- Small: 8px
- Medium: 16px
- Large: 24px
- XLarge: 32px

#### **Layout**
- **Responsive:** Desktop (1200px+), Tablet (768px-1199px)
- **Max Width:** 1440px for content
- **Sidebar:** 240px fixed width
- **Top Nav:** 64px height

---

## 🧪 Testing Requirements

### **1. Unit Tests (80% coverage)**

**Tool:** Vitest + React Testing Library

**For each component test:**
- ✅ Renders correctly with data
- ✅ Renders empty state
- ✅ Renders loading state
- ✅ Renders error state
- ✅ Handles user interactions (click, input, submit)
- ✅ Form validation works
- ✅ API calls triggered correctly (mocked)

**Example Test Structure:**
```typescript
describe('BucketList', () => {
  test('renders bucket list with data', () => {
    // Mock API response
    // Render component
    // Assert table rows present
  });

  test('shows empty state when no buckets', () => {
    // Mock empty API response
    // Render component
    // Assert empty state message
  });

  test('filters by search term', () => {
    // Render with data
    // Type in search box
    // Assert filtered results
  });

  test('deletes bucket with confirmation', async () => {
    // Render with data
    // Click delete button
    // Assert confirmation dialog
    // Confirm deletion
    // Assert API called
    // Assert bucket removed from list
  });

  test('shows error on API failure', () => {
    // Mock API error
    // Render component
    // Assert error message
  });
});
```

**Coverage Targets:**
- Components: 85%
- Hooks: 90%
- Utils: 95%
- Overall: 80%

### **2. Integration Tests (70% coverage)**

**Tool:** Vitest + MSW (Mock Service Worker)

**Test API integration:**
- ✅ Create resource → Appears in list
- ✅ Update resource → Changes reflected
- ✅ Delete resource → Removed from list
- ✅ Error handling → Shows error message
- ✅ Navigation → Routes correctly
- ✅ State management → Redux/Zustand updates correctly

**Example Integration Test:**
```typescript
test('Create bucket workflow', async () => {
  // Setup MSW handlers
  server.use(
    rest.get('/storage/v1/b', (req, res, ctx) => {
      return res(ctx.json({ items: [] }));
    }),
    rest.post('/storage/v1/b', (req, res, ctx) => {
      return res(ctx.json({ name: 'test-bucket' }));
    })
  );

  // Navigate to storage page
  render(<App />);
  const storageLink = screen.getByText('Storage');
  await userEvent.click(storageLink);

  // Click Create Bucket
  const createButton = screen.getByText('Create Bucket');
  await userEvent.click(createButton);

  // Fill form
  const nameInput = screen.getByLabelText('Bucket Name');
  await userEvent.type(nameInput, 'test-bucket');
  
  const submitButton = screen.getByText('Create');
  await userEvent.click(submitButton);

  // Verify bucket in list
  await waitFor(() => {
    expect(screen.getByText('test-bucket')).toBeInTheDocument();
  });

  // Delete bucket
  const deleteButton = screen.getByLabelText('Delete test-bucket');
  await userEvent.click(deleteButton);
  
  const confirmButton = screen.getByText('Confirm');
  await userEvent.click(confirmButton);

  // Verify bucket removed
  await waitFor(() => {
    expect(screen.queryByText('test-bucket')).not.toBeInTheDocument();
  });
});
```

### **3. E2E Tests (50% of critical paths)**

**Tool:** Cypress

**Critical User Journeys:**

#### **Test 1: Complete Storage Workflow**
```typescript
describe('Storage E2E', () => {
  it('creates bucket, uploads file, downloads file, deletes bucket', () => {
    cy.visit('/');
    cy.selectProject('test-project');
    
    // Navigate to Storage
    cy.get('[data-testid="nav-storage"]').click();
    cy.url().should('include', '/storage');
    
    // Create bucket
    cy.get('[data-testid="create-bucket"]').click();
    cy.get('[name="bucketName"]').type('e2e-test-bucket');
    cy.get('[name="location"]').select('us-central1');
    cy.get('[type="submit"]').click();
    cy.get('[data-testid="toast-success"]').should('contain', 'Bucket created');
    
    // Navigate to bucket
    cy.get('[data-testid="bucket-e2e-test-bucket"]').click();
    
    // Upload file
    cy.get('[data-testid="upload-file"]').attachFile('test-file.txt');
    cy.get('[data-testid="toast-success"]').should('contain', 'File uploaded');
    
    // Download file
    cy.get('[data-testid="object-test-file.txt"]').click();
    cy.get('[data-testid="download"]').click();
    cy.readFile('cypress/downloads/test-file.txt').should('exist');
    
    // Delete file
    cy.get('[data-testid="object-test-file.txt"]').click();
    cy.get('[data-testid="delete"]').click();
    cy.get('[data-testid="confirm-delete"]').click();
    
    // Go back and delete bucket
    cy.get('[data-testid="breadcrumb-storage"]').click();
    cy.get('[data-testid="bucket-e2e-test-bucket"]')
      .find('[data-testid="delete"]').click();
    cy.get('[data-testid="confirm-delete"]').click();
    cy.get('[data-testid="toast-success"]').should('contain', 'Bucket deleted');
  });
});
```

#### **Test 2: Multi-tier Application Deployment**
```typescript
describe('Multi-tier App Deployment E2E', () => {
  it('deploys complete application infrastructure', () => {
    cy.visit('/');
    cy.selectProject('test-project');
    
    // Create custom VPC
    cy.navigateTo('VPC Network');
    cy.createNetwork({
      name: 'app-network',
      mode: 'custom'
    });
    
    // Create 3 subnets
    cy.navigateTo('app-network');
    cy.createSubnet({ name: 'web-subnet', region: 'us-central1', ipRange: '10.0.1.0/24' });
    cy.createSubnet({ name: 'app-subnet', region: 'us-central1', ipRange: '10.0.2.0/24' });
    cy.createSubnet({ name: 'db-subnet', region: 'us-central1', ipRange: '10.0.3.0/24' });
    
    // Create firewall rules
    cy.createFirewallRule({
      name: 'allow-http',
      network: 'app-network',
      targets: 'tag:web',
      sources: '0.0.0.0/0',
      protocols: 'tcp:80,443'
    });
    
    cy.createFirewallRule({
      name: 'allow-app-to-db',
      network: 'app-network',
      targets: 'tag:db',
      sources: 'tag:app',
      protocols: 'tcp:5432'
    });
    
    // Create service account
    cy.navigateTo('IAM & Admin > Service Accounts');
    cy.createServiceAccount({
      name: 'app-service-account',
      roles: ['roles/storage.objectViewer']
    });
    
    // Create storage bucket
    cy.navigateTo('Storage');
    cy.createBucket({ name: 'app-data-bucket' });
    cy.grantBucketAccess({
      bucket: 'app-data-bucket',
      member: 'serviceAccount:app-service-account@test-project.iam.gserviceaccount.com',
      role: 'roles/storage.objectAdmin'
    });
    
    // Upload application files
    cy.navigateTo('app-data-bucket');
    cy.uploadFile('app-config.json');
    
    // Create VMs
    cy.navigateTo('Compute Engine > VM Instances');
    
    cy.createInstance({
      name: 'web-server',
      zone: 'us-central1-a',
      machineType: 'e2-medium',
      network: 'app-network',
      subnet: 'web-subnet',
      tags: 'web',
      externalIP: 'ephemeral'
    });
    
    cy.createInstance({
      name: 'app-server',
      zone: 'us-central1-a',
      machineType: 'e2-medium',
      network: 'app-network',
      subnet: 'app-subnet',
      tags: 'app',
      serviceAccount: 'app-service-account',
      externalIP: 'none'
    });
    
    cy.createInstance({
      name: 'db-server',
      zone: 'us-central1-a',
      machineType: 'e2-medium',
      network: 'app-network',
      subnet: 'db-subnet',
      tags: 'db',
      externalIP: 'none'
    });
    
    // Verify VMs are running
    cy.get('[data-testid="instance-web-server"]')
      .should('contain', 'Running')
      .and('contain', '10.0.1.');
    
    cy.get('[data-testid="instance-app-server"]')
      .should('contain', 'Running')
      .and('contain', '10.0.2.');
    
    cy.get('[data-testid="instance-db-server"]')
      .should('contain', 'Running')
      .and('contain', '10.0.3.');
    
    // Clean up all resources
    cy.deleteAllInstances();
    cy.deleteServiceAccount('app-service-account');
    cy.deleteBucket('app-data-bucket');
    cy.deleteAllFirewallRules();
    cy.deleteAllSubnets();
    cy.deleteNetwork('app-network');
  });
});
```

#### **Test 3: IAM Permission Management**
```typescript
describe('IAM E2E', () => {
  it('manages service account permissions', () => {
    cy.visit('/');
    cy.selectProject('test-project');
    
    // Create service account
    cy.navigateTo('IAM & Admin > Service Accounts');
    cy.createServiceAccount({ name: 'test-sa' });
    
    // Create key
    cy.get('[data-testid="sa-test-sa"]').click();
    cy.get('[data-testid="tab-keys"]').click();
    cy.get('[data-testid="create-key"]').click();
    cy.get('[name="keyType"]').select('JSON');
    cy.get('[type="submit"]').click();
    cy.get('[data-testid="download-key"]').click();
    
    // Grant permissions
    cy.get('[data-testid="tab-permissions"]').click();
    cy.get('[data-testid="grant-access"]').click();
    cy.get('[name="resource"]').select('Bucket: my-bucket');
    cy.get('[name="role"]').select('Storage Object Viewer');
    cy.get('[type="submit"]').click();
    
    // Verify permission
    cy.get('[data-testid="permission-list"]')
      .should('contain', 'my-bucket')
      .and('contain', 'Storage Object Viewer');
    
    // Revoke permission
    cy.get('[data-testid="revoke-permission"]').click();
    cy.get('[data-testid="confirm"]').click();
    
    // Delete key
    cy.get('[data-testid="tab-keys"]').click();
    cy.get('[data-testid="delete-key"]').first().click();
    cy.get('[data-testid="confirm"]').click();
    
    // Delete service account
    cy.navigateTo('IAM & Admin > Service Accounts');
    cy.get('[data-testid="sa-test-sa"]').find('[data-testid="delete"]').click();
    cy.get('[data-testid="confirm"]').click();
  });
});
```

### **4. Performance Tests**

**Tool:** Lighthouse CI + Custom Performance Tests

**Targets:**
- ✅ List page with 100+ items loads in < 2s
- ✅ Form submission < 1s
- ✅ Page transitions < 300ms
- ✅ No memory leaks (heap size stable over 5 minutes)
- ✅ Bundle size < 500KB (gzipped)
- ✅ First Contentful Paint < 1.5s
- ✅ Time to Interactive < 3s

**Performance Test Example:**
```typescript
describe('Performance', () => {
  it('renders 1000 buckets without lag', () => {
    const buckets = Array.from({ length: 1000 }, (_, i) => ({
      name: `bucket-${i}`,
      location: 'us-central1',
      storageClass: 'STANDARD',
      size: Math.random() * 1000000
    }));
    
    const start = performance.now();
    render(<BucketList buckets={buckets} />);
    const end = performance.now();
    
    expect(end - start).toBeLessThan(2000); // 2 seconds
  });
  
  it('has no memory leaks', () => {
    const { unmount } = render(<App />);
    const initialHeap = performance.memory.usedJSHeapSize;
    
    // Simulate 5 minutes of usage
    for (let i = 0; i < 50; i++) {
      cy.visit('/storage');
      cy.visit('/compute');
      cy.visit('/vpc');
      cy.visit('/iam');
    }
    
    unmount();
    cy.wait(1000);
    
    const finalHeap = performance.memory.usedJSHeapSize;
    const heapGrowth = finalHeap - initialHeap;
    
    expect(heapGrowth).toBeLessThan(10 * 1024 * 1024); // < 10MB growth
  });
});
```

### **5. Accessibility Tests**

**Tool:** axe-core + Cypress Axe

**Requirements:**
- ✅ Keyboard navigation works (Tab, Enter, Escape, Arrow keys)
- ✅ Screen reader compatible (ARIA labels, roles, live regions)
- ✅ Color contrast passes WCAG AA (4.5:1 for text, 3:1 for large text)
- ✅ Focus indicators visible
- ✅ Form labels associated with inputs
- ✅ Error messages announced to screen readers

**Accessibility Test Example:**
```typescript
describe('Accessibility', () => {
  it('has no accessibility violations', () => {
    cy.visit('/');
    cy.injectAxe();
    cy.checkA11y();
    
    cy.visit('/storage');
    cy.checkA11y();
    
    cy.visit('/compute/instances/create');
    cy.checkA11y();
  });
  
  it('supports keyboard navigation', () => {
    cy.visit('/storage');
    
    // Tab through interactive elements
    cy.tab();
    cy.focused().should('have.attr', 'data-testid', 'create-bucket');
    
    cy.tab();
    cy.focused().should('have.attr', 'data-testid', 'search-input');
    
    cy.tab();
    cy.focused().should('have.attr', 'data-testid', 'bucket-row-0');
    
    // Press Enter to open bucket
    cy.realPress('Enter');
    cy.url().should('include', '/storage/');
    
    // Press Escape to close modal
    cy.get('[data-testid="create-bucket"]').click();
    cy.realPress('Escape');
    cy.get('[role="dialog"]').should('not.exist');
  });
});
```

---

## 📊 Feature Priority Matrix

### **P0 - Must Have (Week 1-2)** ⚠️ CRITICAL
- ✅ **Dashboard:** Project selector, resource count cards, recent activity feed
- ✅ **Storage:** Bucket list, create bucket, delete bucket, upload/download objects
- ✅ **Compute:** Instance list, create instance, start/stop/delete instance
- ✅ **Basic Error Handling:** Error messages, loading states
- ✅ **Navigation:** Sidebar, top nav, breadcrumbs
- ✅ **Authentication:** Project selection (no auth for now)

### **P1 - Important (Week 3-4)** 🔥 HIGH PRIORITY
- ✅ **Storage:** Bucket details tabs (configuration, permissions), IAM policies, lifecycle rules
- ✅ **Compute:** Instance details page, network configuration, machine type selection
- ✅ **VPC:** Network list, subnet management, firewall rules list
- ✅ **IAM:** Service accounts list, create/delete service account, key generation
- ✅ **Real-time Updates:** Status polling every 5s for instances
- ✅ **Form Validation:** All forms have validation with error messages

### **P2 - Nice to Have (Week 5-6)** 📝 MEDIUM PRIORITY
- ⚪ **Advanced Filtering:** Filter by multiple criteria, saved filters
- ⚪ **Bulk Operations:** Select all, bulk start/stop/delete
- ⚪ **Export to CSV:** Export resource lists
- ⚪ **Monitoring Tab:** CPU/memory graphs for instances
- ⚪ **Logs Tab:** Serial port output for instances
- ⚪ **Search:** Global search across all resources
- ⚪ **Dark Mode:** Theme toggle

### **P3 - Future (Week 7+)** 🌟 LOW PRIORITY
- ⚪ **WebSocket Updates:** Real-time updates instead of polling
- ⚪ **Notifications Center:** Bell icon with notification history
- ⚪ **Custom Dashboards:** User-configurable widgets
- ⚪ **Cost Estimation:** Show estimated costs
- ⚪ **Resource Graph:** Visualize resource relationships
- ⚪ **Audit Logs:** View all actions taken
- ⚪ **Mobile Support:** Responsive design for mobile

---

## 🎯 Acceptance Criteria

**UI is production-ready when:**

### **Functionality (100% required)**
- [x] All CRUD operations work for Storage (buckets, objects)
- [x] All CRUD operations work for Compute (instances)
- [x] All CRUD operations work for VPC (networks, subnets, firewall rules)
- [x] All CRUD operations work for IAM (service accounts, keys, policies)
- [ ] Forms have validation with clear error messages
- [ ] Real-time status updates work (polling every 5s)
- [ ] Error handling with retry functionality
- [ ] Empty states for all lists
- [ ] Loading states for all async operations

### **Testing (Required)**
- [ ] 80%+ unit test coverage
- [ ] 70%+ integration test coverage
- [ ] 50%+ E2E test coverage (critical paths)
- [ ] All tests pass in CI/CD pipeline
- [ ] No console errors or warnings

### **Performance (Required)**
- [ ] Page load < 2s (on 3G network)
- [ ] Form submit < 1s
- [ ] List 1000+ resources without lag
- [ ] Bundle size < 500KB (gzipped)
- [ ] No memory leaks (stable heap over 5 minutes)

### **Accessibility (Required)**
- [ ] Keyboard navigable (Tab, Enter, Escape work)
- [ ] Screen reader compatible (ARIA labels present)
- [ ] Color contrast passes WCAG AA
- [ ] Focus indicators visible
- [ ] No axe-core violations

### **UX (Required)**
- [ ] Matches GCP UI/UX patterns
- [ ] Responsive (desktop + tablet)
- [ ] Consistent styling across all pages
- [ ] Toast notifications for all actions
- [ ] Confirmation dialogs for destructive actions

### **Code Quality (Required)**
- [ ] TypeScript with strict mode
- [ ] ESLint + Prettier configured
- [ ] No TypeScript errors
- [ ] Component documentation (JSDoc)
- [ ] README with setup instructions

---

## 💡 Key Implementation Tips

### **1. State Management**
**Recommendation:** Zustand (simpler than Redux for this project)

```typescript
// stores/projectStore.ts
import create from 'zustand';

interface ProjectState {
  selectedProject: string | null;
  setSelectedProject: (projectId: string) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  selectedProject: localStorage.getItem('selectedProject'),
  setSelectedProject: (projectId) => {
    localStorage.setItem('selectedProject', projectId);
    set({ selectedProject: projectId });
  },
}));

// Usage in component
const { selectedProject, setSelectedProject } = useProjectStore();
```

### **2. API Client**
**Recommendation:** Axios with React Query

```typescript
// api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
  timeout: 10000,
});

// Request interceptor
apiClient.interceptors.request.use((config) => {
  const projectId = localStorage.getItem('selectedProject');
  if (projectId && config.params) {
    config.params.project = projectId;
  }
  return config;
});

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// api/storage.ts
export const storageApi = {
  listBuckets: (projectId: string) =>
    apiClient.get(`/storage/v1/b`, { params: { project: projectId } }),
  
  createBucket: (projectId: string, data: CreateBucketRequest) =>
    apiClient.post(`/storage/v1/b`, data, { params: { project: projectId } }),
  
  deleteBucket: (bucketName: string) =>
    apiClient.delete(`/storage/v1/b/${bucketName}`),
};

// hooks/useStorage.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export const useBuckets = (projectId: string) => {
  return useQuery({
    queryKey: ['buckets', projectId],
    queryFn: () => storageApi.listBuckets(projectId),
    enabled: !!projectId,
  });
};

export const useCreateBucket = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: { projectId: string; bucket: CreateBucketRequest }) =>
      storageApi.createBucket(data.projectId, data.bucket),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(['buckets', variables.projectId]);
      toast.success('Bucket created successfully');
    },
    onError: (error) => {
      toast.error(`Failed to create bucket: ${error.message}`);
    },
  });
};
```

### **3. Real-time Updates**
**Recommendation:** React Query with refetch interval

```typescript
// hooks/useInstances.ts
export const useInstances = (projectId: string, zone: string) => {
  return useQuery({
    queryKey: ['instances', projectId, zone],
    queryFn: () => computeApi.listInstances(projectId, zone),
    enabled: !!projectId && !!zone,
    refetchInterval: 5000, // Poll every 5 seconds
    refetchIntervalInBackground: true,
  });
};
```

### **4. Form Validation**
**Recommendation:** React Hook Form + Zod

```typescript
// schemas/instance.ts
import { z } from 'zod';

export const createInstanceSchema = z.object({
  name: z.string()
    .min(1, 'Name is required')
    .max(63, 'Name must be 63 characters or less')
    .regex(/^[a-z]([a-z0-9-]*[a-z0-9])?$/, 'Name must start with letter, lowercase, hyphens allowed'),
  zone: z.string().min(1, 'Zone is required'),
  machineType: z.string().min(1, 'Machine type is required'),
  network: z.string().min(1, 'Network is required'),
  subnet: z.string().min(1, 'Subnet is required'),
  externalIP: z.enum(['none', 'ephemeral', 'static']),
  serviceAccount: z.string().optional(),
  tags: z.string().optional(),
});

// components/CreateInstanceForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const CreateInstanceForm = () => {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(createInstanceSchema),
  });
  
  const onSubmit = (data) => {
    createInstance.mutate(data);
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <TextField
        {...register('name')}
        error={!!errors.name}
        helperText={errors.name?.message}
        label="Instance Name"
        required
      />
      {/* ... */}
    </form>
  );
};
```

### **5. Tables**
**Recommendation:** Material-UI DataGrid or TanStack Table

```typescript
// components/BucketList.tsx
import { DataGrid } from '@mui/x-data-grid';

const BucketList = () => {
  const { data: buckets, isLoading } = useBuckets(projectId);
  
  const columns = [
    { field: 'name', headerName: 'Name', flex: 1 },
    { field: 'location', headerName: 'Location', width: 150 },
    { field: 'storageClass', headerName: 'Storage Class', width: 150 },
    {
      field: 'size',
      headerName: 'Size',
      width: 120,
      valueFormatter: (params) => formatBytes(params.value),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 100,
      renderCell: (params) => (
        <IconButton onClick={() => deleteBucket(params.row.name)}>
          <DeleteIcon />
        </IconButton>
      ),
    },
  ];
  
  return (
    <DataGrid
      rows={buckets || []}
      columns={columns}
      loading={isLoading}
      pageSize={50}
      checkboxSelection
      disableSelectionOnClick
    />
  );
};
```

### **6. Routing**
**Recommendation:** React Router v6

```typescript
// routes.tsx
import { createBrowserRouter } from 'react-router-dom';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      {
        path: 'storage',
        children: [
          { index: true, element: <BucketList /> },
          { path: ':bucketName', element: <BucketDetails /> },
        ],
      },
      {
        path: 'compute',
        children: [
          { path: 'instances', element: <InstanceList /> },
          { path: 'instances/create', element: <CreateInstance /> },
          { path: 'instances/:zone/:name', element: <InstanceDetails /> },
        ],
      },
      // ... more routes
    ],
  },
]);

// App.tsx
import { RouterProvider } from 'react-router-dom';
import { router } from './routes';

function App() {
  return <RouterProvider router={router} />;
}
```

### **7. Testing Setup**

```typescript
// test/setup.ts
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

expect.extend(matchers);
afterEach(() => {
  cleanup();
});

// test/utils.tsx
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

export const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {ui}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

// Example test
import { renderWithProviders } from '@/test/utils';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('creates bucket', async () => {
  const user = userEvent.setup();
  renderWithProviders(<BucketList />);
  
  await user.click(screen.getByText('Create Bucket'));
  await user.type(screen.getByLabelText('Bucket Name'), 'test-bucket');
  await user.click(screen.getByText('Create'));
  
  expect(await screen.findByText('Bucket created')).toBeInTheDocument();
});
```

---

## 📦 Project Structure

```
gcp-stimulator-ui/
├── public/
│   └── vite.svg
├── src/
│   ├── api/                    # API client and endpoints
│   │   ├── client.ts
│   │   ├── storage.ts
│   │   ├── compute.ts
│   │   ├── vpc.ts
│   │   └── iam.ts
│   ├── components/             # Reusable components
│   │   ├── common/             # Common UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Table.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── ...
│   │   ├── storage/            # Storage-specific components
│   │   │   ├── BucketList.tsx
│   │   │   ├── CreateBucketModal.tsx
│   │   │   └── ...
│   │   ├── compute/            # Compute-specific components
│   │   │   ├── InstanceList.tsx
│   │   │   ├── CreateInstanceForm.tsx
│   │   │   └── ...
│   │   ├── vpc/                # VPC-specific components
│   │   └── iam/                # IAM-specific components
│   ├── hooks/                  # Custom hooks
│   │   ├── useStorage.ts
│   │   ├── useCompute.ts
│   │   ├── useVPC.ts
│   │   └── useIAM.ts
│   ├── layouts/                # Layout components
│   │   ├── Layout.tsx
│   │   ├── Sidebar.tsx
│   │   └── TopNav.tsx
│   ├── pages/                  # Page components
│   │   ├── Dashboard.tsx
│   │   ├── storage/
│   │   ├── compute/
│   │   ├── vpc/
│   │   └── iam/
│   ├── stores/                 # Zustand stores
│   │   ├── projectStore.ts
│   │   └── uiStore.ts
│   ├── types/                  # TypeScript types
│   │   ├── storage.ts
│   │   ├── compute.ts
│   │   ├── vpc.ts
│   │   └── iam.ts
│   ├── utils/                  # Utility functions
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   ├── schemas/                # Zod validation schemas
│   │   ├── storage.ts
│   │   ├── compute.ts
│   │   └── ...
│   ├── routes.tsx              # Route configuration
│   ├── App.tsx                 # Root component
│   ├── main.tsx                # Entry point
│   └── index.css               # Global styles
├── test/                       # Test utilities
│   ├── setup.ts
│   └── utils.tsx
├── cypress/                    # E2E tests
│   ├── e2e/
│   ├── fixtures/
│   └── support/
├── .env.example                # Environment variables template
├── package.json
├── tsconfig.json
├── vite.config.ts
├── vitest.config.ts
└── README.md
```

---

## 🚀 Getting Started

### **Prerequisites**
- Node.js 18+
- npm or yarn
- Backend API running on http://localhost:8080

### **Installation**
```bash
cd gcp-stimulator-ui
npm install
```

### **Development**
```bash
npm run dev
# Opens http://localhost:5173
```

### **Build**
```bash
npm run build
npm run preview
```

### **Testing**
```bash
# Unit tests
npm run test

# Unit tests with coverage
npm run test:coverage

# E2E tests
npm run test:e2e

# E2E tests in UI mode
npm run test:e2e:ui
```

### **Linting**
```bash
npm run lint
npm run lint:fix
```

---

## 📝 Environment Variables

Create `.env` file:
```env
VITE_API_URL=http://localhost:8080
VITE_ENABLE_MOCK=false
VITE_POLLING_INTERVAL=5000
```

---

## ✅ Definition of Done

A feature is considered "Done" when:
- [ ] Code is written and reviewed
- [ ] Unit tests pass with 80%+ coverage
- [ ] Integration tests pass
- [ ] E2E tests pass for critical path
- [ ] No TypeScript errors
- [ ] No ESLint warnings
- [ ] Accessible (keyboard + screen reader)
- [ ] Responsive (desktop + tablet)
- [ ] Performance meets targets (< 2s load)
- [ ] Documented (JSDoc + README)
- [ ] PR approved and merged

---

## 📞 Support

For questions or issues:
- Check existing issues in the repository
- Create a new issue with detailed description
- Contact the development team

---

**Last Updated:** January 30, 2026
**Version:** 1.0.0
**Status:** Ready for Implementation 🚀
