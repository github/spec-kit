import * as SDK from "azure-devops-extension-sdk";

class LeadTimeWidget {
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
            const leadTimeData = {
                avgLeadTime: 5.2,
                trend: '+0.8',
                breakdown: [
                    { stage: 'Specification', avgDays: 1.2 },
                    { stage: 'Planning', avgDays: 0.8 },
                    { stage: 'Development', avgDays: 2.5 },
                    { stage: 'Review', avgDays: 0.7 }
                ],
                percentile90: 8.1,
                percentile95: 12.3
            };

            this.renderWidget(leadTimeData);
        } catch (error) {
            console.error('Error loading lead time data:', error);
            this.renderError('Failed to load lead time metrics');
        }
    }

    renderWidget(data: any): void {
        const container = document.getElementById('leadtime-widget');
        if (!container) return;

        container.innerHTML = `
            <div class="leadtime-widget">
                <div class="metric-header">
                    <h3>Average Lead Time</h3>
                    <span class="trend ${data.trend.startsWith('+') ? 'positive' : 'negative'}">
                        ${data.trend} days
                    </span>
                </div>
                
                <div class="primary-metric">
                    <span class="value">${data.avgLeadTime}</span>
                    <span class="unit">days</span>
                </div>
                
                <div class="breakdown">
                    <h4>Stage Breakdown</h4>
                    ${data.breakdown.map((stage: any) => `
                        <div class="stage-item">
                            <span class="stage-name">${stage.stage}</span>
                            <span class="stage-value">${stage.avgDays}d</span>
                        </div>
                    `).join('')}
                </div>
                
                <div class="percentiles">
                    <div class="percentile">
                        <span class="label">90th percentile</span>
                        <span class="value">${data.percentile90}d</span>
                    </div>
                    <div class="percentile">
                        <span class="label">95th percentile</span>
                        <span class="value">${data.percentile95}d</span>
                    </div>
                </div>
            </div>
        `;
    }

    renderError(message: string): void {
        const container = document.getElementById('leadtime-widget');
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
    new LeadTimeWidget();
});