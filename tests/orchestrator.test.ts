import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { WorkflowOrchestrator } from '../src/services/orchestrator';
import { LLMService } from '../src/services/llm';
import { RepositoryService } from '../src/services/repository';
import { TelemetryService } from '../src/services/telemetry';

// Mock dependencies
jest.mock('../src/services/llm');
jest.mock('../src/services/repository');
jest.mock('../src/services/telemetry');

describe('WorkflowOrchestrator', () => {
    let orchestrator: WorkflowOrchestrator;
    let mockLLMService: jest.Mocked<LLMService>;
    let mockRepositoryService: jest.Mocked<RepositoryService>;
    let mockTelemetryService: jest.Mocked<TelemetryService>;

    beforeEach(() => {
        mockLLMService = new LLMService() as jest.Mocked<LLMService>;
        mockRepositoryService = new RepositoryService() as jest.Mocked<RepositoryService>;
        mockTelemetryService = new TelemetryService() as jest.Mocked<TelemetryService>;
        
        orchestrator = new WorkflowOrchestrator();
    });

    describe('executeWorkflow', () => {
        it('should execute specify workflow successfully', async () => {
            const mockWorkItem = {
                id: 123,
                fields: {
                    'System.Title': 'Test Work Item',
                    'System.Description': 'Test description'
                }
            };

            const mockResult = {
                artifacts: [
                    {
                        content: '# Test Specification\n\nTest content',
                        extension: 'md',
                        type: 'specification'
                    }
                ],
                cost: 0.05,
                tokens: { input: 1000, output: 500 }
            };

            mockLLMService.generateContent.mockResolvedValue(mockResult);

            const result = await orchestrator.executeWorkflow('specify', mockWorkItem, {
                temperature: 0.7,
                maxTokens: 2000
            });

            expect(result.success).toBe(true);
            expect(result.artifacts).toHaveLength(1);
            expect(result.artifacts[0].content).toContain('Test Specification');
            expect(mockTelemetryService.trackWorkflowExecution).toHaveBeenCalled();
        });

        it('should handle workflow execution errors', async () => {
            const mockWorkItem = {
                id: 123,
                fields: {
                    'System.Title': 'Test Work Item'
                }
            };

            mockLLMService.generateContent.mockRejectedValue(new Error('LLM service error'));

            const result = await orchestrator.executeWorkflow('specify', mockWorkItem, {});

            expect(result.success).toBe(false);
            expect(result.error).toContain('LLM service error');
            expect(mockTelemetryService.trackWorkflowError).toHaveBeenCalled();
        });

        it('should validate workflow inputs', async () => {
            const result = await orchestrator.executeWorkflow('invalid-workflow' as any, null as any, {});

            expect(result.success).toBe(false);
            expect(result.error).toContain('Invalid workflow');
        });
    });

    describe('getWorkflowHistory', () => {
        it('should return workflow execution history', async () => {
            const history = await orchestrator.getWorkflowHistory(123);

            expect(Array.isArray(history)).toBe(true);
            expect(mockTelemetryService.getWorkflowHistory).toHaveBeenCalledWith(123);
        });
    });

    describe('getWorkflowStatus', () => {
        it('should return current workflow status', async () => {
            const status = await orchestrator.getWorkflowStatus(123);

            expect(status).toHaveProperty('workItemId', 123);
            expect(status).toHaveProperty('currentWorkflow');
            expect(status).toHaveProperty('progress');
        });
    });
});