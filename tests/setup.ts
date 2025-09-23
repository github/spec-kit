// Test setup for Jest
import 'jest-dom/extend-expect';

// Mock Azure DevOps SDK
global.VSS = {
    ready: jest.fn((callback) => callback()),
    require: jest.fn((modules, callback) => {
        const mockModules = modules.map(() => ({
            getService: jest.fn(),
            getClient: jest.fn(),
            getContributionId: jest.fn(() => 'test-contribution'),
            getExtensionContext: jest.fn(() => ({
                publisherId: 'test-publisher',
                extensionId: 'test-extension',
                version: '1.0.0'
            }))
        }));
        callback(...mockModules);
    }),
    getConfiguration: jest.fn(() => ({})),
    getExtensionContext: jest.fn(() => ({
        publisherId: 'test-publisher',
        extensionId: 'test-extension',
        version: '1.0.0'
    })),
    getContributionId: jest.fn(() => 'test-contribution'),
    getWebContext: jest.fn(() => ({
        account: { id: 'test-account' },
        project: { id: 'test-project', name: 'Test Project' },
        team: { id: 'test-team', name: 'Test Team' },
        user: { id: 'test-user', name: 'Test User' },
        collection: { id: 'test-collection' },
        host: { id: 'test-host' }
    }))
};

// Mock Azure DevOps API
global.TFS = {
    WorkItemTracking: {
        RestClient: {
            WorkItemTrackingHttpClient: jest.fn(() => ({
                getWorkItem: jest.fn(),
                updateWorkItem: jest.fn(),
                createWorkItem: jest.fn()
            }))
        }
    },
    Core: {
        RestClient: {
            CoreHttpClient: jest.fn(() => ({
                getProject: jest.fn(),
                getTeams: jest.fn()
            }))
        }
    },
    Build: {
        RestClient: {
            BuildHttpClient: jest.fn(() => ({
                getBuilds: jest.fn(),
                getBuild: jest.fn()
            }))
        }
    }
};

// Mock DOM APIs that might be missing in test environment
Object.defineProperty(window, 'localStorage', {
    value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn()
    },
    writable: true
});

Object.defineProperty(window, 'sessionStorage', {
    value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn()
    },
    writable: true
});

// Mock fetch if needed
global.fetch = jest.fn();

// Suppress console warnings in tests unless explicitly needed
global.console = {
    ...console,
    warn: jest.fn(),
    error: jest.fn()
};