import { Command } from 'commander';
import { AIModelSettingsProvider } from '@models/AIModelSettings';
import { ProjectDetector } from '@services/ProjectDetector';
import chalk from 'chalk';

export interface ListModelsOptions {
  format?: 'table' | 'json' | 'yaml';
  details?: boolean;
  current?: boolean;
  compatibility?: boolean;
}

export class ListModelsCommand {
  private projectDetector: ProjectDetector;

  constructor() {
    this.projectDetector = new ProjectDetector();
  }

  create(): Command {
    const command = new Command('list-models');

    command
      .description('Show available AI models and compatibility information')
      .option('-f, --format <format>', 'Output format (table, json, yaml)', 'table')
      .option('-d, --details', 'Show detailed model information', false)
      .option('-c, --current', 'Show current project model only', false)
      .option('--compatibility', 'Show compatibility information', false)
      .action(async (options) => {
        await this.execute(options);
      });

    return command;
  }

  async execute(options: ListModelsOptions): Promise<void> {
    try {
      // Get current project info if available
      let currentProject = null;
      try {
        const detection = await this.projectDetector.detectProject();
        if (detection.found && detection.config) {
          currentProject = detection.config;
        }
      } catch (error) {
        // No project found, continue without project context
      }

      // Get all available models
      const allModels = AIModelSettingsProvider.getAllModels();

      // Filter to current model only if requested
      const models = options.current && currentProject
        ? allModels.filter(model => model.modelType === currentProject.aiModel)
        : allModels;

      if (models.length === 0) {
        if (options.current) {
          console.error(chalk.red('❌ No current project found or invalid model configuration'));
        } else {
          console.error(chalk.red('❌ No models available'));
        }
        process.exit(1);
      }

      // Output based on format
      switch (options.format) {
        case 'json':
          await this.outputJson(models, currentProject, options);
          break;
        case 'yaml':
          await this.outputYaml(models, currentProject, options);
          break;
        case 'table':
        default:
          await this.outputTable(models, currentProject, options);
          break;
      }

    } catch (error) {
      console.error(chalk.red(`❌ Error listing models: ${error}`));
      process.exit(1);
    }
  }

  private async outputTable(
    models: any[],
    currentProject: any,
    options: ListModelsOptions
  ): Promise<void> {
    console.log(chalk.blue('🤖 Available AI Models\n'));

    if (currentProject) {
      console.log(chalk.gray(`Current project: ${currentProject.name} (${currentProject.aiModel})\n`));
    }

    for (const model of models) {
      const isCurrent = currentProject?.aiModel === model.modelType;
      const marker = isCurrent ? chalk.green('● ') : '  ';
      const name = isCurrent
        ? chalk.green.bold(model.modelType)
        : chalk.white(model.modelType);

      console.log(`${marker}${name} v${model.version}`);

      if (options.details) {
        console.log(chalk.gray(`    Max tokens: ${model.capabilities.maxTokens.toLocaleString()}`));
        console.log(chalk.gray(`    Rate limit: ${model.capabilities.rateLimit.requestsPerMinute}/min`));
        console.log(chalk.gray(`    Features: ${model.capabilities.features.length} available`));

        if (model.capabilities.features.length > 0) {
          const enabledFeatures = model.capabilities.features
            .filter((f: any) => f.enabled)
            .map((f: any) => f.name);
          console.log(chalk.gray(`    Enabled: ${enabledFeatures.join(', ')}`));
        }

        if (options.compatibility) {
          const compatible = currentProject
            ? AIModelSettingsProvider.isCompatible(model.modelType, '0.1.0')
            : true;

          console.log(chalk.gray(`    Compatible: ${compatible ? '✅' : '❌'}`));
          console.log(chalk.gray(`    Min CLI version: ${model.compatibility.minimumCliVersion}`));
        }

        if (model.compatibility.deprecationWarning) {
          console.log(chalk.yellow(`    ⚠️  ${model.compatibility.deprecationWarning}`));
        }

        console.log();
      }
    }

    if (!options.details) {
      console.log(chalk.gray('\nUse --details for more information'));
    }

    // Show migration info if multiple models available
    if (models.length > 1 && currentProject) {
      const otherModels = models.filter(m => m.modelType !== currentProject.aiModel);
      if (otherModels.length > 0) {
        console.log(chalk.blue('\n🔄 Migration Options:'));
        for (const model of otherModels) {
          console.log(chalk.gray(`  specify switch-model ${model.modelType}`));
        }
      }
    }
  }

  private async outputJson(
    models: any[],
    currentProject: any,
    options: ListModelsOptions
  ): Promise<void> {
    const output = {
      currentProject: currentProject ? {
        name: currentProject.name,
        model: currentProject.aiModel,
        version: currentProject.version,
      } : null,
      models: models.map(model => ({
        type: model.modelType,
        version: model.version,
        current: currentProject?.aiModel === model.modelType,
        capabilities: options.details ? model.capabilities : {
          maxTokens: model.capabilities.maxTokens,
          features: model.capabilities.features.length,
        },
        compatibility: options.compatibility ? model.compatibility : {
          minimumCliVersion: model.compatibility.minimumCliVersion,
          migrationSupport: model.compatibility.migrationSupport,
        },
        configuration: options.details ? model.configuration : undefined,
      })),
      summary: {
        total: models.length,
        compatible: models.filter(m =>
          AIModelSettingsProvider.isCompatible(m.modelType, '0.1.0')
        ).length,
      },
    };

    console.log(JSON.stringify(output, null, 2));
  }

  private async outputYaml(
    models: any[],
    currentProject: any,
    options: ListModelsOptions
  ): Promise<void> {
    // Simple YAML-like output (in production, use a YAML library)
    console.log('models:');

    for (const model of models) {
      console.log(`  ${model.modelType}:`);
      console.log(`    version: "${model.version}"`);
      console.log(`    current: ${currentProject?.aiModel === model.modelType}`);

      if (options.details) {
        console.log(`    capabilities:`);
        console.log(`      maxTokens: ${model.capabilities.maxTokens}`);
        console.log(`      features: ${model.capabilities.features.length}`);
        console.log(`      rateLimit:`);
        console.log(`        requestsPerMinute: ${model.capabilities.rateLimit.requestsPerMinute}`);
      }

      if (options.compatibility) {
        console.log(`    compatibility:`);
        console.log(`      minimumCliVersion: "${model.compatibility.minimumCliVersion}"`);
        console.log(`      migrationSupport: ${model.compatibility.migrationSupport}`);
      }

      console.log();
    }

    if (currentProject) {
      console.log('currentProject:');
      console.log(`  name: "${currentProject.name}"`);
      console.log(`  model: "${currentProject.aiModel}"`);
      console.log(`  version: "${currentProject.version}"`);
    }
  }

  getUsageExamples(): string[] {
    return [
      'specify list-models',
      'specify list-models --details',
      'specify list-models --format json',
      'specify list-models --current --compatibility',
      'specify list-models --format yaml --details',
    ];
  }

  async getModelSuggestions(currentModel?: string): Promise<string[]> {
    const models = AIModelSettingsProvider.getAllModels();
    const suggestions: string[] = [];

    for (const model of models) {
      if (model.modelType !== currentModel) {
        const features = model.capabilities.features
          .filter(f => f.enabled)
          .map(f => f.name);

        suggestions.push(
          `${model.modelType}: ${features.join(', ')} (${model.capabilities.maxTokens.toLocaleString()} tokens)`
        );
      }
    }

    return suggestions;
  }

  async compareModels(model1: string, model2: string): Promise<{
    model1: any;
    model2: any;
    differences: string[];
    recommendation?: string;
  } | null> {
    const modelA = AIModelSettingsProvider.getSettings(model1 as any);
    const modelB = AIModelSettingsProvider.getSettings(model2 as any);

    if (!modelA || !modelB) {
      return null;
    }

    const differences: string[] = [];

    // Compare capabilities
    if (modelA.capabilities.maxTokens !== modelB.capabilities.maxTokens) {
      differences.push(
        `Max tokens: ${modelA.modelType} (${modelA.capabilities.maxTokens.toLocaleString()}) vs ` +
        `${modelB.modelType} (${modelB.capabilities.maxTokens.toLocaleString()})`
      );
    }

    // Compare features
    const featuresA = new Set(modelA.capabilities.features.map(f => f.name));
    const featuresB = new Set(modelB.capabilities.features.map(f => f.name));

    const onlyInA = [...featuresA].filter(f => !featuresB.has(f));
    const onlyInB = [...featuresB].filter(f => !featuresA.has(f));

    if (onlyInA.length > 0) {
      differences.push(`${modelA.modelType} exclusive features: ${onlyInA.join(', ')}`);
    }

    if (onlyInB.length > 0) {
      differences.push(`${modelB.modelType} exclusive features: ${onlyInB.join(', ')}`);
    }

    return {
      model1: modelA,
      model2: modelB,
      differences,
    };
  }
}