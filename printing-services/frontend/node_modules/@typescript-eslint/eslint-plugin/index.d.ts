import type { ClassicConfig } from '@typescript-eslint/utils/ts-eslint';

import type rules from './rules';

declare const cjsExport: {
  configs: Record<string, ClassicConfig.Config>;
  rules: typeof rules;
};
export = cjsExport;
