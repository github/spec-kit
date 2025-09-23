import * as SDK from "azure-devops-extension-sdk";

interface GuardrailRule {
    name: string;
    category: 'security' | 'performance' | 'quality';
    status: 'passed' | 'failed' | 'warning';
    description: string;
    lastChecked: Date;
}

class GuardrailsWidget {
    private projectId: string = '';
    private widgetSettings: any = {};

    constructor() {
        this.initialize();
    }

    async initialize(): Promise<void> {
        await SDK.init();
        await SDK.ready();

        const webContext = SDK.getWebContext();
        this.projectId = webContext.project?.id || '';

        await this.loadData();
    }

    async loadData(): Promise<void> {
        try {
            // Mock data for demo
            const guardrailsData = {
                overallScore: 87,
                totalRules: 24,
                passed: 19,
                warnings: 3,
                failed: 2,
                recentChecks: [
                    {
                        name: 'Input Validation Required',
                        category: 'security' as const,
                        status: 'passed' as const,
                        description: 'All user inputs are properly validated',
                        lastChecked: new Date()
                    },
                    {
                        name: 'Response Time < 2s',
                        category: 'performance' as const,
                        status: 'warning' as const,
                        description: 'Some endpoints exceed 2-second threshold',
                        lastChecked: new Date()
                    },
                    {
                        name: 'Code Coverage > 80%',
                        category: 'quality' as const,
                        status: 'failed' as const,
                        description: 'Current coverage: 76%',
                        lastChecked: new Date()
                    },
                    {
                        name: 'Authentication Required',
                        category: 'security' as const,
                        status: 'passed' as const,
                        description: 'All protected endpoints require auth',
                        lastChecked: new Date()
                    },
                    {
                        name: 'Database Query Optimization',
                        category: 'performance' as const,
                        status: 'warning' as const,
                        description: 'Some queries missing indexes',
                        lastChecked: new Date()
                    }
                ],
                trendData: [
                    { date: '2024-01-01', score: 82 },
                    { date: '2024-01-15', score: 85 },
                    { date: '2024-02-01', score: 87 }
                ]
            };

            this.renderWidget(guardrailsData);
        } catch (error) {
            console.error('Error loading guardrails data:', error);
            this.renderError('Failed to load guardrails status');
        }
    }

    renderWidget(data: any): void {
        const container = document.getElementById('guardrails-widget');
        if (!container) return;

        container.innerHTML = `
            <div class="guardrails-widget">
                <div class="metric-header">
                    <h3>Guardrails Compliance</h3>
                    <span class="score ${this.getScoreClass(data.overallScore)}">${data.overallScore}%</span>
                </div>
                
                <div class="summary-stats">
                    <div class="stat passed">
                        <span class="value">${data.passed}</span>
                        <span class="label">Passed</span>
                    </div>
                    <div class="stat warnings">
                        <span class="value">${data.warnings}</span>
                        <span class="label">Warnings</span>
                    </div>
                    <div class="stat failed">
                        <span class="value">${data.failed}</span>
                        <span class="label">Failed</span>
                    </div>
                </div>
                
                <div class="recent-checks">
                    <h4>Recent Checks</h4>
                    <div class="checks-list">
                        ${data.recentChecks.map((rule: GuardrailRule) => `
                            <div class="check-item ${rule.status}">
                                <div class="check-info">
                                    <span class="check-name">${rule.name}</span>
                                    <span class="check-category">${rule.category}</span>
                                </div>
                                <div class="check-status">
                                    <span class="status-icon">${this.getStatusIcon(rule.status)}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="actions">
                    <button class="btn primary" onclick="window.open('/_admin/_work/guardrails', '_blank')">
                        View All Rules
                    </button>
                    <button class="btn secondary" onclick="this.runAllChecks()">
                        Run Checks
                    </button>
                </div>
            </div>
        `;
    }

    getScoreClass(score: number): string {
        if (score >= 90) return 'excellent';
        if (score >= 80) return 'good';
        if (score >= 70) return 'warning';
        return 'poor';
    }

    getStatusIcon(status: string): string {
        switch (status) {
            case 'passed': return '✅';
            case 'warning': return '⚠️';
            case 'failed': return '❌';
            default: return '❓';
        }
    }

    renderError(message: string): void {
        const container = document.getElementById('guardrails-widget');
        if (!container) return;

        container.innerHTML = `
            <div class="widget-error">
                <div class="error-icon">⚠️</div>
                <div class="error-message">${message}</div>
            </div>
        `;
    }

    async runAllChecks(): Promise<void> {
        // In a real implementation, this would trigger guardrails validation
        console.log('Running all guardrails checks...');
        await this.loadData();
    }
}

// Initialize widget when page loads
SDK.ready().then(() => {
    new GuardrailsWidget();
});