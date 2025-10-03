export interface AIModelSettings {
  modelType: 'claude' | 'gemini' | 'copilot';
  version: string;
  capabilities: ModelCapabilities;
  configuration: ModelConfiguration;
  compatibility: CompatibilityInfo;
}

export interface ModelCapabilities {
  maxTokens: number;
  supportedFormats: string[];
  features: ModelFeature[];
  rateLimit: RateLimit;
}

export interface ModelFeature {
  name: string;
  enabled: boolean;
  description: string;
  requirements?: string[];
}

export interface RateLimit {
  requestsPerMinute: number;
  tokensPerMinute: number;
  dailyLimit?: number;
}

export interface ModelConfiguration {
  apiEndpoint?: string;
  apiKey?: string;
  temperature?: number;
  maxOutputTokens?: number;
  customSettings?: Record<string, unknown>;
}

export interface CompatibilityInfo {
  supportedVersions: string[];
  migrationSupport: boolean;
  deprecationWarning?: string;
  minimumCliVersion: string;
}

export class AIModelSettingsProvider {
  private static readonly MODEL_DEFINITIONS: Record<string, AIModelSettings> = {
    claude: {
      modelType: 'claude',
      version: '3.0',
      capabilities: {
        maxTokens: 200000,
        supportedFormats: ['text', 'json', 'markdown', 'code'],
        features: [
          {
            name: 'code-generation',
            enabled: true,
            description: 'Generate and refactor code',
            requirements: ['typescript', 'javascript'],
          },
          {
            name: 'spec-analysis',
            enabled: true,
            description: 'Analyze and validate specifications',
          },
          {
            name: 'task-tracking',
            enabled: true,
            description: 'Track and update task progress',
          },
        ],
        rateLimit: {
          requestsPerMinute: 60,
          tokensPerMinute: 100000,
          dailyLimit: 1000000,
        },
      },
      configuration: {
        temperature: 0.7,
        maxOutputTokens: 4096,
        customSettings: {},
      },
      compatibility: {
        supportedVersions: ['2.1', '3.0'],
        migrationSupport: true,
        minimumCliVersion: '0.1.0',
      },
    },
    gemini: {
      modelType: 'gemini',
      version: '1.5',
      capabilities: {
        maxTokens: 100000,
        supportedFormats: ['text', 'json', 'markdown'],
        features: [
          {
            name: 'code-generation',
            enabled: true,
            description: 'Generate and refactor code',
          },
          {
            name: 'spec-analysis',
            enabled: true,
            description: 'Analyze specifications',
          },
        ],
        rateLimit: {
          requestsPerMinute: 30,
          tokensPerMinute: 50000,
        },
      },
      configuration: {
        temperature: 0.8,
        maxOutputTokens: 2048,
        customSettings: {},
      },
      compatibility: {
        supportedVersions: ['1.0', '1.5'],
        migrationSupport: true,
        minimumCliVersion: '0.1.0',
      },
    },
    copilot: {
      modelType: 'copilot',
      version: '1.0',
      capabilities: {
        maxTokens: 8000,
        supportedFormats: ['text', 'code'],
        features: [
          {
            name: 'code-generation',
            enabled: true,
            description: 'AI-powered code completion and generation',
            requirements: ['github-copilot-extension'],
          },
          {
            name: 'code-explanation',
            enabled: true,
            description: 'Explain existing code',
          },
          {
            name: 'refactoring',
            enabled: true,
            description: 'Suggest code improvements',
          },
        ],
        rateLimit: {
          requestsPerMinute: 100,
          tokensPerMinute: 200000,
        },
      },
      configuration: {
        temperature: 0.6,
        maxOutputTokens: 1024,
        customSettings: {},
      },
      compatibility: {
        supportedVersions: ['1.0'],
        migrationSupport: true,
        minimumCliVersion: '0.1.0',
      },
    },
  };

  static getSettings(modelType: 'claude' | 'gemini' | 'copilot'): AIModelSettings | null {
    return this.MODEL_DEFINITIONS[modelType] || null;
  }

  static getAllModels(): AIModelSettings[] {
    return Object.values(this.MODEL_DEFINITIONS);
  }

  static isCompatible(
    modelType: 'claude' | 'gemini' | 'copilot',
    cliVersion: string
  ): boolean {
    const settings = this.getSettings(modelType);
    if (!settings) return false;

    // Simple version comparison (should use semver in production)
    return cliVersion >= settings.compatibility.minimumCliVersion;
  }
}