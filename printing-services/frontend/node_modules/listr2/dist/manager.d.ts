import { Listr } from './listr';
import { ListrError } from './interfaces/listr-error.interface';
import { ListrBaseClassOptions, ListrContext, ListrSubClassOptions, ListrTask } from './interfaces/listr.interface';
import { ListrGetRendererClassFromValue, ListrRendererValue } from './interfaces/renderer.interface';
/**
 * Creates a new Listr2 task manager.
 *
 * Useful for creating a single instace of Listr2 with pre-set settings.
 */
export declare class Manager<Ctx = ListrContext, Renderer extends ListrRendererValue = 'default', FallbackRenderer extends ListrRendererValue = 'verbose'> {
    options?: ListrBaseClassOptions<Ctx, Renderer, FallbackRenderer>;
    err: ListrError[];
    private tasks;
    constructor(options?: ListrBaseClassOptions<Ctx, Renderer, FallbackRenderer>);
    set ctx(ctx: Ctx);
    add<InjectCtx = Ctx>(tasks: ListrTask<InjectCtx, ListrGetRendererClassFromValue<Renderer>>[] | ((ctx?: InjectCtx) => ListrTask<InjectCtx, ListrGetRendererClassFromValue<Renderer>>[]), options?: ListrSubClassOptions<InjectCtx, Renderer>): void;
    runAll<InjectCtx = Ctx>(options?: ListrBaseClassOptions<InjectCtx, Renderer, FallbackRenderer>): Promise<InjectCtx>;
    newListr<InjectCtx, InjectRenderer extends ListrRendererValue = Renderer, InjectFallbackRenderer extends ListrRendererValue = FallbackRenderer>(tasks: ListrTask<InjectCtx, ListrGetRendererClassFromValue<InjectRenderer>>[], options?: ListrBaseClassOptions<InjectCtx, InjectRenderer, InjectFallbackRenderer>): Listr<InjectCtx, InjectRenderer, InjectFallbackRenderer>;
    indent<InjectCtx = Ctx>(tasks: ListrTask<InjectCtx, ListrGetRendererClassFromValue<Renderer>>[] | ((ctx?: InjectCtx) => ListrTask<InjectCtx, ListrGetRendererClassFromValue<Renderer>>[]), options?: ListrBaseClassOptions<InjectCtx, Renderer, FallbackRenderer>, taskOptions?: Omit<ListrTask<InjectCtx, ListrGetRendererClassFromValue<Renderer>>, 'task'>): ListrTask<InjectCtx, ListrGetRendererClassFromValue<Renderer>>;
    run<InjectCtx = Ctx>(tasks: ListrTask<InjectCtx, ListrGetRendererClassFromValue<Renderer>>[], options?: ListrBaseClassOptions<InjectCtx, Renderer, FallbackRenderer>): Promise<InjectCtx>;
    getRuntime(pipetime: number): string;
}
