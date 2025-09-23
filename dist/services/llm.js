"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LLMService = void 0;
class LLMService {
    constructor() {
        this.connectionCache = new Map();
    }
    async getProjectConnections(projectId) {
        // Check cache first
        if (this.connectionCache.has(projectId)) {
            return this.connectionCache.get(projectId);
        }
        // This would fetch from Azure DevOps service connections API
        const connections = await this.fetchServiceConnections(projectId);
        this.connectionCache.set(projectId, connections);
        return connections;
    }
    async fetchServiceConnections(projectId) {
        // Mock data for now - would integrate with Azure DevOps REST API
        return [
            {
                id: 'openai-connection-1',
                name: 'OpenAI GPT-4',
                baseUrl: 'https://api.openai.com/v1',
                model: 'gpt-4',
                temperatureCap: 0.7,
                isDefault: true,
                isActive: true,
                createdDate: new Date('2024-01-15'),
                lastTestDate: new Date('2024-01-20')
            },
            {
                id: 'azure-openai-connection-1',
                name: 'Azure OpenAI',
                baseUrl: 'https://my-resource.openai.azure.com',
                model: 'gpt-4',
                region: 'East US',
                temperatureCap: 0.5,
                isDefault: false,
                isActive: true,
                createdDate: new Date('2024-01-10')
            }
        ];
    }
    async testConnection(connectionId) {
        const startTime = Date.now();
        try {
            const connection = await this.getConnectionById(connectionId);
            if (!connection) {
                throw new Error('Connection not found');
            }
            // This would make an actual API call to test the connection
            const result = await this.makeTestCall(connection);
            const latency = Date.now() - startTime;
            return {
                success: true,
                model: result.model,
                latency
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    async getConnectionById(connectionId) {
        // This would fetch a specific connection by ID
        return {
            id: connectionId,
            name: 'Test Connection',
            baseUrl: 'https://api.openai.com/v1',
            model: 'gpt-4',
            isDefault: false,
            isActive: true,
            createdDate: new Date()
        };
    }
    async makeTestCall(connection) {
        // Mock test call - would make actual HTTP request
        return {
            model: connection.model,
            response: 'Test successful'
        };
    }
    async setDefaultConnection(projectId, connectionId) {
        const connections = await this.getProjectConnections(projectId);
        // Update default status
        connections.forEach(conn => {
            conn.isDefault = conn.id === connectionId;
        });
        // Would save to Azure DevOps project settings
        console.log(`Setting default LLM connection to ${connectionId} for project ${projectId}`);
        // Update cache
        this.connectionCache.set(projectId, connections);
    }
    async executePrompt(connectionId, prompt, options) {
        const connection = await this.getConnectionById(connectionId);
        if (!connection) {
            throw new Error('LLM connection not found');
        }
        // This would make the actual LLM API call
        // For now, return mock response
        const inputTokens = Math.ceil(prompt.length / 4); // Rough estimate
        const outputTokens = Math.ceil(Math.random() * 1000 + 200);
        return {
            response: `Mock response to: ${prompt.substring(0, 50)}...`,
            cost: this.calculateCost(connection.model, inputTokens, outputTokens),
            tokens: {
                input: inputTokens,
                output: outputTokens
            }
        };
    }
    calculateCost(model, inputTokens, outputTokens) {
        // Pricing based on model type
        const pricing = {
            'gpt-4': { input: 0.03 / 1000, output: 0.06 / 1000 },
            'gpt-3.5-turbo': { input: 0.001 / 1000, output: 0.002 / 1000 },
            'claude-3': { input: 0.015 / 1000, output: 0.075 / 1000 }
        };
        const modelPricing = pricing[model] || pricing['gpt-4'];
        return (inputTokens * modelPricing.input) + (outputTokens * modelPricing.output);
    }
    clearCache() {
        this.connectionCache.clear();
    }
}
exports.LLMService = LLMService;
//# sourceMappingURL=llm.js.map