import * as SDK from "azure-devops-extension-sdk";

interface LLMConnectionConfig {
    id: string;
    name: string;
    provider: 'openai' | 'azure-openai' | 'anthropic' | 'custom';
    baseUrl: string;
    model: string;
    apiKey: string;
    maxTokens: number;
    temperature: number;
    isDefault: boolean;
    isActive: boolean;
}

class ServiceConnectionManager {
    private projectId: string = '';
    private connections: LLMConnectionConfig[] = [];

    constructor() {
        this.initialize();
    }

    async initialize(): Promise<void> {
        await SDK.init();
        await SDK.ready();

        const webContext = SDK.getWebContext();
        this.projectId = webContext.project?.id || '';

        await this.loadConnections();
        this.setupEventHandlers();
        this.renderUI();
    }

    async loadConnections(): Promise<void> {
        try {
            // In a real implementation, this would load from Azure DevOps service connections
            this.connections = [
                {
                    id: 'openai-gpt4',
                    name: 'OpenAI GPT-4',
                    provider: 'openai',
                    baseUrl: 'https://api.openai.com/v1',
                    model: 'gpt-4',
                    apiKey: '*********************',
                    maxTokens: 2000,
                    temperature: 0.7,
                    isDefault: true,
                    isActive: true
                },
                {
                    id: 'azure-openai-gpt4',
                    name: 'Azure OpenAI GPT-4',
                    provider: 'azure-openai',
                    baseUrl: 'https://your-resource.openai.azure.com',
                    model: 'gpt-4',
                    apiKey: '*********************',
                    maxTokens: 2000,
                    temperature: 0.7,
                    isDefault: false,
                    isActive: false
                }
            ];
        } catch (error) {
            console.error('Error loading connections:', error);
        }
    }

    renderUI(): void {
        const container = document.getElementById('service-connection-container');
        if (!container) return;

        container.innerHTML = `
            <div class="service-connection-manager">
                <div class="header">
                    <h2>LLM Service Connections</h2>
                    <button class="btn primary" onclick="this.showAddConnectionDialog()">
                        + Add Connection
                    </button>
                </div>
                
                <div class="connections-list">
                    ${this.connections.map(conn => this.renderConnectionCard(conn)).join('')}
                </div>
                
                <div class="connection-dialog" id="connection-dialog" style="display: none;">
                    ${this.renderConnectionDialog()}
                </div>
            </div>
        `;
    }

    renderConnectionCard(connection: LLMConnectionConfig): string {
        return `
            <div class="connection-card ${connection.isActive ? 'active' : ''} ${connection.isDefault ? 'default' : ''}">
                <div class="connection-header">
                    <div class="connection-info">
                        <h3>${connection.name}</h3>
                        <span class="provider">${connection.provider}</span>
                        ${connection.isDefault ? '<span class="badge default">Default</span>' : ''}
                    </div>
                    <div class="connection-actions">
                        <button class="btn-icon" onclick="this.editConnection('${connection.id}')" title="Edit">
                            ✏️
                        </button>
                        <button class="btn-icon" onclick="this.testConnection('${connection.id}')" title="Test">
                            🔍
                        </button>
                        <button class="btn-icon delete" onclick="this.deleteConnection('${connection.id}')" title="Delete">
                            🗑️
                        </button>
                    </div>
                </div>
                
                <div class="connection-details">
                    <div class="detail-row">
                        <span class="label">Model:</span>
                        <span class="value">${connection.model}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Base URL:</span>
                        <span class="value">${connection.baseUrl}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Max Tokens:</span>
                        <span class="value">${connection.maxTokens}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Temperature:</span>
                        <span class="value">${connection.temperature}</span>
                    </div>
                </div>
                
                <div class="connection-status">
                    <span class="status ${connection.isActive ? 'active' : 'inactive'}">
                        ${connection.isActive ? '🟢 Active' : '🔴 Inactive'}
                    </span>
                    <button class="btn secondary small" onclick="this.toggleConnection('${connection.id}')">
                        ${connection.isActive ? 'Deactivate' : 'Activate'}
                    </button>
                    ${!connection.isDefault ? `
                        <button class="btn secondary small" onclick="this.setAsDefault('${connection.id}')">
                            Set as Default
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    renderConnectionDialog(): string {
        return `
            <div class="dialog-content">
                <div class="dialog-header">
                    <h3 id="dialog-title">Add LLM Connection</h3>
                    <button class="btn-close" onclick="this.hideConnectionDialog()">×</button>
                </div>
                
                <form id="connection-form" onsubmit="this.saveConnection(event)">
                    <div class="form-group">
                        <label for="connection-name">Connection Name</label>
                        <input type="text" id="connection-name" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="connection-provider">Provider</label>
                        <select id="connection-provider" onchange="this.onProviderChange()">
                            <option value="openai">OpenAI</option>
                            <option value="azure-openai">Azure OpenAI</option>
                            <option value="anthropic">Anthropic</option>
                            <option value="custom">Custom</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="connection-base-url">Base URL</label>
                        <input type="url" id="connection-base-url" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="connection-model">Model</label>
                        <input type="text" id="connection-model" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="connection-api-key">API Key</label>
                        <input type="password" id="connection-api-key" required>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="connection-max-tokens">Max Tokens</label>
                            <input type="number" id="connection-max-tokens" value="2000" min="1" max="8000">
                        </div>
                        
                        <div class="form-group">
                            <label for="connection-temperature">Temperature</label>
                            <input type="number" id="connection-temperature" value="0.7" min="0" max="2" step="0.1">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="connection-default"> Set as default connection
                        </label>
                    </div>
                    
                    <div class="dialog-actions">
                        <button type="button" class="btn secondary" onclick="this.hideConnectionDialog()">
                            Cancel
                        </button>
                        <button type="submit" class="btn primary">
                            Save Connection
                        </button>
                    </div>
                </form>
            </div>
        `;
    }

    setupEventHandlers(): void {
        // Add event listeners for dynamic interactions
        // In a real implementation, these would be properly bound
    }

    showAddConnectionDialog(): void {
        const dialog = document.getElementById('connection-dialog');
        if (dialog) {
            dialog.style.display = 'block';
        }
    }

    hideConnectionDialog(): void {
        const dialog = document.getElementById('connection-dialog');
        if (dialog) {
            dialog.style.display = 'none';
        }
    }

    async testConnection(connectionId: string): Promise<void> {
        const connection = this.connections.find(c => c.id === connectionId);
        if (!connection) return;

        try {
            // Test connection by making a simple API call
            console.log(`Testing connection: ${connection.name}`);
            // Show success/failure feedback
        } catch (error) {
            console.error('Connection test failed:', error);
        }
    }

    async toggleConnection(connectionId: string): Promise<void> {
        const connection = this.connections.find(c => c.id === connectionId);
        if (connection) {
            connection.isActive = !connection.isActive;
            this.renderUI();
        }
    }

    async setAsDefault(connectionId: string): Promise<void> {
        this.connections.forEach(c => c.isDefault = c.id === connectionId);
        this.renderUI();
    }

    async deleteConnection(connectionId: string): Promise<void> {
        if (confirm('Are you sure you want to delete this connection?')) {
            this.connections = this.connections.filter(c => c.id !== connectionId);
            this.renderUI();
        }
    }

    async saveConnection(event: Event): Promise<void> {
        event.preventDefault();
        // Save connection logic would go here
        this.hideConnectionDialog();
        await this.loadConnections();
        this.renderUI();
    }

    onProviderChange(): void {
        const provider = (document.getElementById('connection-provider') as HTMLSelectElement)?.value;
        const baseUrlInput = document.getElementById('connection-base-url') as HTMLInputElement;
        const modelInput = document.getElementById('connection-model') as HTMLInputElement;

        if (provider === 'openai') {
            baseUrlInput.value = 'https://api.openai.com/v1';
            modelInput.value = 'gpt-4';
        } else if (provider === 'azure-openai') {
            baseUrlInput.value = 'https://your-resource.openai.azure.com';
            modelInput.value = 'gpt-4';
        } else if (provider === 'anthropic') {
            baseUrlInput.value = 'https://api.anthropic.com';
            modelInput.value = 'claude-3-opus-20240229';
        }
    }
}

// Initialize when page loads
SDK.ready().then(() => {
    new ServiceConnectionManager();
});