import { ListrOptions } from '../interfaces/listr.interface';
import { SupportedRenderer, ListrRendererValue } from '../interfaces/renderer.interface';
export declare function getRenderer(renderer: ListrRendererValue, fallbackRenderer?: ListrRendererValue, fallbackCondition?: ListrOptions['rendererFallback'], silentCondition?: ListrOptions['rendererSilent']): SupportedRenderer;
