# UI Navigation Guide - Networking Features

## 🎯 Accessing the New Networking Features

### Starting the UI

```bash
cd /home/ubuntu/gcs-stimulator/gcp-stimulator-ui
npm run dev -- --host 0.0.0.0 --port 3000
```

Access at: **http://localhost:3000** or **http://16.16.160.48:3000**

---

## 📍 Navigation Flow

### 1. **VPC Networks** (`/services/vpc/networks`)

**Access:** Left Sidebar → **Networking** → **VPC Networks**

**Features:**
- ✅ List all VPC networks with CIDR ranges
- ✅ Create network button opens modal
- ✅ **Auto vs Custom Mode:**
  - **Automatic:** One subnet per region created automatically (Google manages CIDR)
  - **Custom:** You define CIDR range (e.g., 10.50.0.0/16) and manually create subnets
- ✅ When Custom mode selected → IPv4 CIDR Range field appears
- ✅ Real-time validation: Shows gateway IP and usable IPs count
- ✅ Each network row has **"Subnets"** button → Takes you to filtered subnet list

**Navigation Links:**
- Header: "View Subnets" → `/services/vpc/subnets`
- Header: "View Instances" → `/services/compute-engine`
- Per Network: "Subnets" button → `/services/vpc/subnets?network=<name>`

---

### 2. **Subnets** (`/services/vpc/subnets`)

**Access:** 
- Left Sidebar → **Networking** → **Subnets**
- From Networks page → Click "Subnets" button on any network
- From Instance creation → Click "Create a subnet" link

**Features:**
- ✅ Back arrow → Returns to Networks page
- ✅ Shows filtered view if accessed from a specific network
- ✅ "Show all" link to clear network filter
- ✅ Create Subnet button → Pre-selects network if filtered
- ✅ IP CIDR Range input with validation:
  - ✅ Green checkmark when valid
  - ✅ Shows gateway IP and available IPs count
  - ✅ Validates subnet is within VPC CIDR range
- ✅ Table shows Available IPs column

**Navigation Links:**
- Header: Back arrow → `/services/vpc/networks`
- Header: "View Networks" link
- If filtered: "Show all" → Removes network filter

---

### 3. **VM Instances** (`/services/compute-engine`)

**Access:** Left Sidebar → **Compute** → **VM Instances**

**Features:**
- ✅ Create Instance button opens modal
- ✅ Network dropdown (select VPC)
- ✅ **Subnet dropdown appears** after selecting network
  - Automatically filtered by selected zone's region
  - Shows subnet name with CIDR: `my-subnet (10.50.1.0/24)`
  - Auto-selects first available subnet
- ✅ Warning when no subnets: **"Create a subnet"** link (clickable)
  - Takes you to: `/services/vpc/subnets?network=<selected>`

**Navigation Links:**
- Header: "View Networks" → `/services/vpc/networks`
- Header: "View Subnets" → `/services/vpc/subnets`
- Form: "Create a subnet" link (when no subnets available)

---

## 🔄 Complete User Flow

### Creating a Multi-Tier Network Architecture

1. **Create VPC Network**
   - Go to **VPC Networks** → Click **"Create Network"**
   - Select **"Custom"** subnet mode
   - Enter CIDR: `10.50.0.0/16`
   - See: Gateway `10.50.0.1`, 65,534 usable IPs
   - Click **"Create"**

2. **Create Subnets**
   - From Networks page → Click **"Subnets"** button on your network
   - Or click **"View Subnets"** in header
   - Click **"Create Subnet"**
   - Network is pre-selected
   - Enter subnet details:
     - Name: `web-tier`
     - Region: `us-central1`
     - IP CIDR: `10.50.1.0/24`
   - See validation: ✓ Gateway `10.50.1.1`, 254 usable IPs
   - Click **"Create"**
   - Repeat for app-tier and db-tier

3. **Create VM Instances**
   - Go to **VM Instances** → Click **"Create Instance"**
   - Name: `web-server-1`
   - Zone: `us-central1-a`
   - Machine Type: `n1-standard-1`
   - Network: Select your custom VPC
   - Subnet: Select `web-tier (10.50.1.0/24)`
   - Click **"Create"**

---

## 🆕 What Changed

### Before:
- ❌ VPC Dashboard was a placeholder
- ❌ No CIDR input for custom VPCs
- ❌ No subnet selection in instance creation
- ❌ No navigation between related pages
- ❌ No explanation of "Auto" vs "Custom" mode

### After:
- ✅ VPC Dashboard redirects to Networks (no duplicates)
- ✅ CIDR input with real-time validation
- ✅ Subnet dropdown filtered by region
- ✅ Navigation links throughout (Networks ↔ Subnets ↔ Instances)
- ✅ Contextual help text explaining modes
- ✅ Direct action links (e.g., "Create a subnet" opens subnet creation with network pre-selected)
- ✅ Back navigation arrows
- ✅ Filtered views (e.g., show only subnets for a specific network)

---

## 🎨 UX Improvements

1. **Contextual Navigation:** Every page has links to related resources
2. **Smart Pre-selection:** When navigating from Network → Subnet, network is pre-selected
3. **Filtered Views:** URL params preserve context (e.g., `?network=my-vpc`)
4. **Visual Feedback:** ✓ checkmarks, IP calculations, help icons
5. **Actionable Warnings:** "No subnets" → Clickable link to create one
6. **Breadcrumb-style:** Back arrows and clear page hierarchy

---

## 📊 Network Statistics (Coming Soon)

The API module includes `getNetworkStats()` for future dashboard:
- Total networks, subnets, instances
- IP utilization per subnet
- Available IP pools
