/**
 * CIDR Validation and Utility Functions
 */

export interface CIDRValidationResult {
  valid: boolean;
  error?: string;
}

/**
 * Validates a CIDR notation string (e.g., "10.0.0.0/16")
 */
export const validateCIDR = (cidr: string): CIDRValidationResult => {
  if (!cidr) {
    return { valid: false, error: 'CIDR is required' };
  }

  const cidrRegex = /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;
  if (!cidrRegex.test(cidr)) {
    return { valid: false, error: 'Invalid CIDR format (e.g., 10.0.0.0/16)' };
  }

  const [ip, prefixStr] = cidr.split('/');
  const prefix = parseInt(prefixStr, 10);

  // Validate prefix length
  if (prefix < 8 || prefix > 29) {
    return { valid: false, error: 'Prefix must be between /8 and /29' };
  }

  // Validate IP octets
  const octets = ip.split('.').map(Number);
  if (octets.some(octet => octet < 0 || octet > 255 || isNaN(octet))) {
    return { valid: false, error: 'Invalid IP address' };
  }

  // Check if IP is within valid private ranges (RFC 1918)
  const firstOctet = octets[0];
  const secondOctet = octets[1];
  
  const isPrivate = 
    firstOctet === 10 || // 10.0.0.0/8
    (firstOctet === 172 && secondOctet >= 16 && secondOctet <= 31) || // 172.16.0.0/12
    (firstOctet === 192 && secondOctet === 168); // 192.168.0.0/16

  if (!isPrivate) {
    return { valid: false, error: 'CIDR must be within private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)' };
  }

  return { valid: true };
};

/**
 * Calculates the number of usable IPs in a CIDR block
 */
export const calculateUsableIPs = (cidr: string): number => {
  const prefix = parseInt(cidr.split('/')[1], 10);
  const totalIPs = Math.pow(2, 32 - prefix);
  // Subtract network and broadcast addresses
  return Math.max(0, totalIPs - 2);
};

/**
 * Gets the gateway IP (first usable IP) from a CIDR block
 */
export const getGatewayIP = (cidr: string): string => {
  const [ip] = cidr.split('/');
  const octets = ip.split('.').map(Number);
  octets[3] = 1; // Gateway is always .1
  return octets.join('.');
};

/**
 * Checks if a subnet CIDR is within a VPC CIDR
 */
export const isSubnetWithinVPC = (vpcCidr: string, subnetCidr: string): boolean => {
  const ipToNumber = (ip: string): number => {
    return ip.split('.').reduce((acc, octet) => (acc << 8) + parseInt(octet, 10), 0);
  };

  const [vpcIP, vpcPrefix] = vpcCidr.split('/');
  const [subnetIP, subnetPrefix] = subnetCidr.split('/');

  const vpcPrefixNum = parseInt(vpcPrefix, 10);
  const subnetPrefixNum = parseInt(subnetPrefix, 10);

  // Subnet must have equal or smaller range (larger prefix)
  if (subnetPrefixNum < vpcPrefixNum) {
    return false;
  }

  const vpcIPNum = ipToNumber(vpcIP);
  const subnetIPNum = ipToNumber(subnetIP);

  const mask = ~0 << (32 - vpcPrefixNum);
  return (vpcIPNum & mask) === (subnetIPNum & mask);
};

/**
 * Formats CIDR for display with additional information
 */
export const formatCIDRInfo = (cidr: string): string => {
  const usableIPs = calculateUsableIPs(cidr);
  const gateway = getGatewayIP(cidr);
  return `${cidr} (${usableIPs.toLocaleString()} usable IPs, Gateway: ${gateway})`;
};

/**
 * Suggests valid CIDR ranges based on VPC CIDR
 */
export const suggestSubnetCIDRs = (vpcCidr: string, count: number = 4): string[] => {
  const [vpcIP, vpcPrefix] = vpcCidr.split('/');
  const vpcPrefixNum = parseInt(vpcPrefix, 10);
  
  // Suggest subnets with /24 (or VPC prefix + 8, whichever is smaller)
  const subnetPrefix = Math.min(24, vpcPrefixNum + 8);
  
  const octets = vpcIP.split('.').map(Number);
  const suggestions: string[] = [];
  
  for (let i = 0; i < count; i++) {
    const newOctets = [...octets];
    newOctets[2] = (newOctets[2] + i) % 256;
    suggestions.push(`${newOctets.join('.')}/${subnetPrefix}`);
  }
  
  return suggestions;
};
