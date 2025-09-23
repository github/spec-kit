import * as SDK from "azure-devops-extension-sdk";
import { TelemetryService } from "../../services/telemetry";

interface ThroughputData {
    totalSpecs: number;
    totalPlans: number;
    totalTasks: number;
    weeklyAverage: number;
    trends: {
        specs: 'up' | 'down' | 'neutral';
        plans: 'up' | 'down' | 'neutral';
        tasks: 'up' | 'down' | 'neutral';
        overall: 'up' | 'down' | 'neutral';
    };
    chartData: { date: string; count: number }[];
}

class ThroughputWidget {
    private telemetryService: TelemetryService;
    private projectId: string = '';
    private timeframe: string = '30d';

    constructor() {
        this.telemetryService = new TelemetryService();
    }

    public async initialize(): Promise<void> {
        await SDK.init();
        await SDK.ready();

        const webContext = SDK.getWebContext();
        this.projectId = webContext.project?.id || '';

        await this.loadData();
    }

    private async loadData(): Promise<void> {
        try {
            const data = await this.getThroughputData();
            this.renderWidget(data);
        } catch (error) {
            this.renderError(`Failed to load throughput data: ${error}`);
        }
    }

    private async getThroughputData(): Promise<ThroughputData> {
        const metrics = await this.telemetryService.getProjectMetrics(this.projectId);
        const runs = await this.telemetryService.getRecentRuns(this.projectId, 1000);

        // Calculate throughput for the last 30 days
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        
        const recentRuns = runs.filter(run => 
            run.timestamp >= thirtyDaysAgo && run.status === 'success'
        );

        const totalSpecs = recentRuns.filter(run => run.workflow === 'specify').length;
        const totalPlans = recentRuns.filter(run => run.workflow === 'plan').length;
        const totalTasks = recentRuns.filter(run => run.workflow === 'tasks').length;
        
        const weeklyAverage = (totalSpecs + totalPlans + totalTasks) / 4.3; // ~30 days / 7 days

        // Calculate trends (simplified)
        const trends = this.calculateTrends(recentRuns);
        
        // Generate chart data
        const chartData = this.generateChartData(recentRuns);

        return {
            totalSpecs,
            totalPlans,
            totalTasks,
            weeklyAverage,
            trends,
            chartData
        };
    }

    private calculateTrends(runs: any[]): ThroughputData['trends'] {
        // Simplified trend calculation - would be more sophisticated in real implementation
        const midpoint = Math.floor(runs.length / 2);
        const firstHalf = runs.slice(0, midpoint);
        const secondHalf = runs.slice(midpoint);

        const firstHalfSpecs = firstHalf.filter(run => run.workflow === 'specify').length;
        const secondHalfSpecs = secondHalf.filter(run => run.workflow === 'specify').length;
        
        const firstHalfPlans = firstHalf.filter(run => run.workflow === 'plan').length;
        const secondHalfPlans = secondHalf.filter(run => run.workflow === 'plan').length;
        
        const firstHalfTasks = firstHalf.filter(run => run.workflow === 'tasks').length;
        const secondHalfTasks = secondHalf.filter(run => run.workflow === 'tasks').length;

        return {
            specs: secondHalfSpecs > firstHalfSpecs ? 'up' : secondHalfSpecs < firstHalfSpecs ? 'down' : 'neutral',
            plans: secondHalfPlans > firstHalfPlans ? 'up' : secondHalfPlans < firstHalfPlans ? 'down' : 'neutral',
            tasks: secondHalfTasks > firstHalfTasks ? 'up' : secondHalfTasks < firstHalfTasks ? 'down' : 'neutral',
            overall: (secondHalfSpecs + secondHalfPlans + secondHalfTasks) > (firstHalfSpecs + firstHalfPlans + firstHalfTasks) ? 'up' : 'down'
        };
    }

    private generateChartData(runs: any[]): { date: string; count: number }[] {
        const chartData: { date: string; count: number }[] = [];
        const dailyCounts: Record<string, number> = {};

        // Group runs by date
        runs.forEach(run => {
            const date = run.timestamp.toISOString().split('T')[0];
            dailyCounts[date] = (dailyCounts[date] || 0) + 1;
        });

        // Generate data for last 7 days
        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            
            chartData.push({
                date: dateStr,
                count: dailyCounts[dateStr] || 0
            });
        }

        return chartData;
    }

    private renderWidget(data: ThroughputData): void {
        const container = document.getElementById('widget-container');
        if (!container) return;

        container.innerHTML = `
            <div class="widget-header">
                <h3 class="widget-title">Spec Throughput</h3>
                <span class="widget-timeframe">Last 30 days</span>
            </div>
            <div class="metrics-container">
                <div class="metric-card">
                    <div class="metric-value">${data.totalSpecs}</div>
                    <div class="metric-label">Specifications</div>
                    <div class="metric-trend trend-${data.trends.specs}">
                        ${this.getTrendIcon(data.trends.specs)} ${this.getTrendText(data.trends.specs)}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.totalPlans}</div>
                    <div class="metric-label">Plans</div>
                    <div class="metric-trend trend-${data.trends.plans}">
                        ${this.getTrendIcon(data.trends.plans)} ${this.getTrendText(data.trends.plans)}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.totalTasks}</div>
                    <div class="metric-label">Task Groups</div>
                    <div class="metric-trend trend-${data.trends.tasks}">
                        ${this.getTrendIcon(data.trends.tasks)} ${this.getTrendText(data.trends.tasks)}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.weeklyAverage.toFixed(1)}</div>
                    <div class="metric-label">Weekly Avg</div>
                    <div class="metric-trend trend-${data.trends.overall}">
                        ${this.getTrendIcon(data.trends.overall)} Overall
                    </div>
                </div>
            </div>
            <div class="chart-container">
                <div class="chart-placeholder">
                    ${this.renderMiniChart(data.chartData)}
                </div>
            </div>
        `;
    }

    private getTrendIcon(trend: 'up' | 'down' | 'neutral'): string {
        switch (trend) {
            case 'up': return '↗';
            case 'down': return '↘';
            default: return '→';
        }
    }

    private getTrendText(trend: 'up' | 'down' | 'neutral'): string {
        switch (trend) {
            case 'up': return 'Trending up';
            case 'down': return 'Trending down';
            default: return 'Stable';
        }
    }

    private renderMiniChart(data: { date: string; count: number }[]): string {
        const maxCount = Math.max(...data.map(d => d.count), 1);
        const barWidth = 100 / data.length;
        
        const bars = data.map((point, index) => {
            const height = (point.count / maxCount) * 60; // 60px max height
            const x = index * barWidth;
            return `<div style="
                position: absolute;
                left: ${x}%;
                bottom: 0;
                width: ${barWidth * 0.8}%;
                height: ${height}px;
                background: #0078d4;
                border-radius: 2px 2px 0 0;
            "></div>`;
        }).join('');

        return `<div style="position: relative; width: 100%; height: 60px;">${bars}</div>`;
    }

    private renderError(message: string): void {
        const container = document.getElementById('widget-container');
        if (container) {
            container.innerHTML = `<div class="error">${message}</div>`;
        }
    }

    private renderNoData(): void {
        const container = document.getElementById('widget-container');
        if (container) {
            container.innerHTML = `<div class="no-data">No throughput data available.<br>Start using Spec Kit workflows to see metrics here.</div>`;
        }
    }
}

// Initialize the widget
const widget = new ThroughputWidget();
widget.initialize().catch(console.error);