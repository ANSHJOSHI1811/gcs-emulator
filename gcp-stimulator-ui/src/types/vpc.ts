export interface Network {
  id: string;
  name: string;
  description?: string;
  autoCreateSubnetworks: boolean;
  subnetworks?: string[];
  creationTimestamp: string;
  selfLink?: string;
  routingConfig?: {
    routingMode: 'REGIONAL' | 'GLOBAL';
  };
  mtu?: number;
}

export interface Subnet {
  id: string;
  name: string;
  network: string;
  ipCidrRange: string;
  region: string;
  gatewayAddress: string;
  creationTimestamp: string;
  selfLink?: string;
  description?: string;
  privateIpGoogleAccess?: boolean;
  enableFlowLogs?: boolean;
  secondaryIpRanges?: SecondaryIpRange[];
  purpose?: string;
  role?: string;
}

export interface SecondaryIpRange {
  rangeName: string;
  ipCidrRange: string;
}

export interface FirewallRule {
  id: string;
  name: string;
  network: string;
  direction: 'INGRESS' | 'EGRESS';
  priority: number;
  description?: string;
  creationTimestamp: string;
  selfLink?: string;
  allowed?: FirewallRuleAction[];
  denied?: FirewallRuleAction[];
  sourceRanges?: string[];
  destinationRanges?: string[];
  sourceTags?: string[];
  targetTags?: string[];
  sourceServiceAccounts?: string[];
  targetServiceAccounts?: string[];
  disabled?: boolean;
  logConfig?: {
    enable: boolean;
  };
}

export interface FirewallRuleAction {
  IPProtocol: string;
  ports?: string[];
}

export interface Route {
  id: string;
  name: string;
  network: string;
  destRange: string;
  priority: number;
  description?: string;
  creationTimestamp: string;
  selfLink?: string;
  nextHopGateway?: string;
  nextHopIp?: string;
  nextHopInstance?: string;
  nextHopNetwork?: string;
  nextHopPeering?: string;
  nextHopVpnTunnel?: string;
  tags?: string[];
  warnings?: RouteWarning[];
}

export interface RouteWarning {
  code: string;
  message: string;
  data?: Record<string, string>;
}

export interface Router {
  id: string;
  name: string;
  network: string;
  region: string;
  description?: string;
  creationTimestamp: string;
  selfLink?: string;
  bgp?: {
    asn: number;
    advertiseMode?: string;
    advertisedGroups?: string[];
    advertisedIpRanges?: AdvertisedIpRange[];
  };
  bgpPeers?: BgpPeer[];
  nats?: RouterNat[];
}

export interface AdvertisedIpRange {
  range: string;
  description?: string;
}

export interface BgpPeer {
  name: string;
  interfaceName: string;
  ipAddress: string;
  peerIpAddress: string;
  peerAsn: number;
  advertisedRoutePriority?: number;
  advertiseMode?: string;
  managementType?: string;
}

export interface RouterNat {
  name: string;
  natIpAllocateOption: string;
  sourceSubnetworkIpRangesToNat: string;
  natIps?: string[];
  subnetworks?: RouterNatSubnetwork[];
  minPortsPerVm?: number;
  maxPortsPerVm?: number;
  enableEndpointIndependentMapping?: boolean;
  logConfig?: {
    enable: boolean;
    filter: string;
  };
}

export interface RouterNatSubnetwork {
  name: string;
  sourceIpRangesToNat: string[];
  secondaryIpRangeNames?: string[];
}

export interface Address {
  id: string;
  name: string;
  address?: string;
  status: string;
  region: string;
  description?: string;
  creationTimestamp: string;
  selfLink?: string;
  addressType?: 'INTERNAL' | 'EXTERNAL';
  purpose?: string;
  network?: string;
  subnetwork?: string;
  prefixLength?: number;
  ipVersion?: 'IPV4' | 'IPV6';
  users?: string[];
}

export interface CreateNetworkRequest {
  name: string;
  autoCreateSubnetworks: boolean;
  description?: string;
  routingConfig?: {
    routingMode: 'REGIONAL' | 'GLOBAL';
  };
  mtu?: number;
}

export interface CreateSubnetRequest {
  name: string;
  network: string;
  ipCidrRange: string;
  region: string;
  description?: string;
  privateIpGoogleAccess?: boolean;
  enableFlowLogs?: boolean;
  secondaryIpRanges?: SecondaryIpRange[];
}

export interface CreateFirewallRequest {
  name: string;
  network: string;
  direction: 'INGRESS' | 'EGRESS';
  priority: number;
  description?: string;
  allowed?: FirewallRuleAction[];
  denied?: FirewallRuleAction[];
  sourceRanges?: string[];
  destinationRanges?: string[];
  sourceTags?: string[];
  targetTags?: string[];
  disabled?: boolean;
}
