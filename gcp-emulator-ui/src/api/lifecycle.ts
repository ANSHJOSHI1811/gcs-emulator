import { apiClient } from './client';
import { LifecycleRulesResponse, LifecycleRule, CreateLifecycleRuleRequest } from '../types';

// Phase 4: Lifecycle Rules API
export async function listLifecycleRules(bucketName?: string): Promise<LifecycleRule[]> {
  const url = bucketName 
    ? `/internal/lifecycle/rules?bucket=${bucketName}` 
    : '/internal/lifecycle/rules';
  
  const response = await apiClient.get<LifecycleRulesResponse>(url);
  return response.data.items || [];
}

export async function createLifecycleRule(rule: CreateLifecycleRuleRequest): Promise<LifecycleRule> {
  const response = await apiClient.post<LifecycleRule>('/internal/lifecycle/rules', rule);
  return response.data;
}

export async function deleteLifecycleRule(ruleId: string): Promise<void> {
  await apiClient.delete(`/internal/lifecycle/rules/${ruleId}`);
}

export async function evaluateLifecycleRules(): Promise<void> {
  await apiClient.post('/internal/lifecycle/evaluate');
}
