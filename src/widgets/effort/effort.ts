import * as SDK from "azure-devops-extension-sdk";

class EffortWidget {
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
            const effortData = {
                totalEstimated: 142,
                totalActual: 136,
                accuracy: 95.8,
                trend: '+2.1%',
                breakdown: [
                    { type: 'Specification', estimated: 24, actual: 22, accuracy: 91.7 },
                    { type: 'Planning', estimated: 18, actual: 16, accuracy: 88.9 },
                    { type: 'Development', estimated: 85, actual: 84, accuracy: 98.8 },
                    { type: 'Testing', estimated: 15, actual: 14, accuracy: 93.3 }
                ],
                monthlyTrend: [
                    { month: 'Jan', accuracy: 89.2 },
                    { month: 'Feb', accuracy: 92.1 },
                    { month: 'Mar', accuracy: 95.8 }
                ]
            };

            this.renderWidget(effortData);
        } catch (error) {
            console.error('Error loading effort data:', error);
            this.renderError('Failed to load effort metrics');
        }
    }

    renderWidget(data: any): void {
        const container = document.getElementById('effort-widget');
        if (!container) return;

        container.innerHTML = `
            <div class="effort-widget">
                <div class="metric-header">
                    <h3>Effort Estimation Accuracy</h3>
                    <span class="trend positive">${data.trend}</span>
                </div>
                
                <div class="primary-metric">
                    <span class="value">${data.accuracy}%</span>
                    <span class="unit">accuracy</span>
                </div>
                
                <div class="effort-summary">
                    <div class="summary-item">
                        <span class="label">Estimated</span>
                        <span class="value">${data.totalEstimated}h</span>
                    </div>
                    <div class="summary-item">
                        <span class="label">Actual</span>
                        <span class="value">${data.totalActual}h</span>
                    </div>
                </div>
                
                <div class="breakdown">
                    <h4>By Activity Type</h4>
                    ${data.breakdown.map((item: any) => `
                        <div class="effort-item">
                            <span class="type-name">${item.type}</span>
                            <div class="effort-bars">
                                <div class="estimated-bar" style="width: ${(item.estimated / data.totalEstimated * 100)}%"></div>
                                <div class="actual-bar" style="width: ${(item.actual / data.totalEstimated * 100)}%"></div>
                            </div>
                            <span class="accuracy">${item.accuracy}%</span>
                        </div>
                    `).join('')}
                </div>
                
                <div class="monthly-trend">
                    <h4>3-Month Trend</h4>
                    <div class="trend-chart">
                        ${data.monthlyTrend.map((month: any) => `
                            <div class="trend-bar">
                                <div class="bar" style="height: ${month.accuracy}%"></div>
                                <span class="month">${month.month}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    renderError(message: string): void {
        const container = document.getElementById('effort-widget');
        if (!container) return;

        container.innerHTML = `
            <div class="widget-error">
                <div class="error-icon">⚠️</div>
                <div class="error-message">${message}</div>
            </div>
        `;
    }
}

// Initialize widget when page loads
SDK.ready().then(() => {
    new EffortWidget();
});