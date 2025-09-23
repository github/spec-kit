export interface LLMConnection {
    id: string;
    name: string;
    baseUrl: string;
    model: string;
    region?: string;
    temperatureCap?: number;
    isDefault: boolean;
    isActive: boolean;
    createdDate: Date;
    lastTestDate?: Date;
}
export interface LLMTestResult {
    success: boolean;
    model?: string;
    error?: string;
    latency?: number;
}
export declare class LLMService {
    private connectionCache;
    getProjectConnections(projectId: string): Promise<LLMConnection[]>;
    private fetchServiceConnections;
    testConnection(connectionId: string): Promise<LLMTestResult>;
    private getConnectionById;
    private makeTestCall;
    setDefaultConnection(projectId: string, connectionId: string): Promise<void>;
    executePrompt(connectionId: string, prompt: string, options?: {
        temperature?: number;
        maxTokens?: number;
        systemMessage?: string;
    }): Promise<{
        response: string;
        cost: number;
        tokens: {
            input: number;
            output: number;
        };
    }>;
    private calculateCost;
    clearCache(): void;
}
