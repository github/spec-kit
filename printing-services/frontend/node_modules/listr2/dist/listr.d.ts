import { ListrError } from './interfaces/listr-error.interface';
import { ListrBaseClassOptions, ListrContext, ListrTask } from './interfaces/listr.interface';
import { ListrDefaultRendererValue, ListrFallbackRendererValue, ListrGetRendererClassFromValue, ListrGetRendererOptions, ListrRendererFactory, ListrRendererValue } from './interfaces/renderer.interface';
import { Task } from './lib/task';
/**
 * Creates a new set of Listr2 task list.
 */
export declare class Listr<Ctx = ListrContext, Renderer extends ListrRendererValue = ListrDefaultRendererValue, FallbackRenderer extends ListrRendererValue = ListrFallbackRendererValue> {
    task: ListrTask<Ctx, ListrGetRendererClassFromValue<Renderer>> | ListrTask<Ctx, ListrGetRendererClassFromValue<Renderer>>[];
    options?: ListrBaseClassOptions<Ctx, Renderer, FallbackRenderer>;
    tasks: Task<Ctx, ListrGetRendererClassFromValue<Renderer>>[];
    err: ListrError<Ctx>[];
    ctx: Ctx;
    rendererClass: ListrRendererFactory;
    rendererClassOptions: ListrGetRendererOptions<ListrRendererFactory>;
    renderHook$: Task<any, any>['renderHook$'];
    private concurrency;
    private renderer;
    constructor(task: ListrTask<Ctx, ListrGetRendererClassFromValue<Renderer>> | ListrTask<Ctx, ListrGetRendererClassFromValue<Renderer>>[], options?: ListrBaseClassOptions<Ctx, Renderer, FallbackRenderer>);
    add(task: ListrTask<Ctx, ListrGetRendererClassFromValue<Renderer>> | ListrTask<Ctx, ListrGetRendererClassFromValue<Renderer>>[]): void;
    run(context?: Ctx): Promise<Ctx>;
    private checkAll;
    private runTask;
}
