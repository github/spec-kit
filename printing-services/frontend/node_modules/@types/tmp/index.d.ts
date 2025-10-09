export interface TmpNameOptions {
    /**
     * The optional temporary directory that must be relative to the system's default
     * temporary directory. Absolute paths are fine as long as they point to a
     * location under the system's default temporary directory. Any directories along
     * the so specified path must exist, otherwise a `ENOENT` error will be thrown
     * upon access, as tmp will not check the availability of the path, nor will it
     * establish the requested path for you.
     */
    dir?: string | undefined;
    /**
     * A fixed name that overrides random name generation, the name must
     * be relative and must not contain path segments.
     */
    name?: string | undefined;
    /**
     * The optional prefix.
     * @default 'tmp'
     */
    prefix?: string | undefined;
    /**
     * The optional postfix.
     * @default ''
     */
    postfix?: string | undefined;
    /**
     * [`mkstemp`](http://www.kernel.org/doc/man-pages/online/pages/man3/mkstemp.3.html)
     * like filename template, no default, must include `XXXXXX` once for random name generation,
     * e.g. `'foo-bar-XXXXXX'`.
     */
    template?: string | undefined;
    /**
     * Allows you to override the system's root tmp directory.
     */
    tmpdir?: string | undefined;
    /**
     * How many times should the function try to get a unique filename before giving up.
     * @default 3
     */
    tries?: number | undefined;
}

export interface FileOptions extends TmpNameOptions {
    /**
     * Detaches the file descriptor, caller is responsible for closing the file, `tmp` will no
     * longer try closing the file during garbage collection.
     * @default false
     */
    detachDescriptor?: boolean | undefined;
    /**
     * Discards the file descriptor (closes file, fd is -1), `tmp` will no longer try closing
     * the file during garbage collection.
     * @default false
     */
    discardDescriptor?: boolean | undefined;
    /**
     * Signals that the temporary file or directory should not be deleted on exit
     *
     * - In order to clean up, you will have to call the provided `cleanupCallback` function manually.
     *
     * @default false
     */
    keep?: boolean | undefined;
    /**
     * The file mode to create with.
     * @default 0o600
     */
    mode?: number | undefined;
}

export interface FileOptionsDiscardFd extends FileOptions {
    discardDescriptor: true;
}

export interface DirOptions extends TmpNameOptions {
    /**
     * Signals that the temporary file or directory should not be deleted on exit
     *
     * - In order to clean up, you will have to call the provided `cleanupCallback` function manually.
     *
     * @default false
     */
    keep?: boolean | undefined;
    /**
     * The file mode to create with.
     * @default 0o700
     */
    mode?: number | undefined;
    /**
     * Recursively removes the created temporary directory, even when it's not empty.
     * @default false
     */
    unsafeCleanup?: boolean | undefined;
}

export interface FileResult {
    name: string;
    fd: number;
    removeCallback: () => void;
}

export type FileResultNoFd = Omit<FileResult, "fd">;

export interface DirResult {
    name: string;
    removeCallback: () => void;
}

export type FileCallback = (err: Error | null, name: string, fd: number, removeCallback: () => void) => void;
export type FileCallbackNoFd = (err: Error | null, name: string, fd: undefined, removeCallback: () => void) => void;

export type DirCallback = (err: Error | null, name: string, removeCallback: () => void) => void;

export type TmpNameCallback = (err: Error | null, name: string) => void;

export const tmpdir: string;

/**
 * Asynchronous file creation.
 *
 * Simple temporary file creation, the file will be closed and unlinked on process exit.
 *
 * @example
 * import * as tmp from 'tmp';
 *
 * tmp.file((err, path, fd, cleanupCallback) => {
 *   if (err) throw err;
 *
 *   console.log('File: ', path);
 *   console.log('Filedescriptor: ', fd);
 *
 *   // If we don't need the file anymore we could manually call the cleanupCallback
 *   // But that is not necessary if we didn't pass the keep option because the library
 *   // will clean after itself.
 *   cleanupCallback();
 * });
 */
export function file(options: FileOptionsDiscardFd, cb: FileCallbackNoFd): void;
export function file(options: FileOptions, cb: FileCallback): void;
export function file(cb: FileCallback): void;

/**
 * Synchronous file creation.
 *
 * Simple synchronous temporary file creation, the file will be closed and unlinked on process exit.
 *
 * @example
 * import * as tmp from 'tmp';
 *
 * const tmpobj = tmp.fileSync();
 * console.log('File: ', tmpobj.name);
 * console.log('Filedescriptor: ', tmpobj.fd);
 *
 * // If we don't need the file anymore we could manually call the removeCallback
 * // But that is not necessary if we didn't pass the keep option because the library
 * // will clean after itself.
 * tmpobj.removeCallback();
 */
export function fileSync(options: FileOptionsDiscardFd): FileResultNoFd;
export function fileSync(options?: FileOptions): FileResult;

/**
 * Asynchronous directory creation.
 *
 * Simple temporary directory creation, it will be removed on process exit.
 *
 * If the directory still contains items on process exit, then it won't be removed.
 *
 * @example
 * import * as tmp from 'tmp';
 *
 * tmp.dir((err, path, cleanupCallback) => {
 *   if (err) throw err;
 *
 *   console.log('Dir: ', path);
 *
 *   // Manual cleanup
 *   cleanupCallback();
 * });
 */
export function dir(options: DirOptions, cb: DirCallback): void;
export function dir(cb: DirCallback): void;

/**
 * Synchronous directory creation.
 *
 * Simple synchronous temporary directory creation, it will be removed on process exit.
 *
 * If the directory still contains items on process exit, then it won't be removed.
 *
 * @example
 * import * as tmp from 'tmp';
 *
 * const tmpobj = tmp.dirSync();
 * console.log('Dir: ', tmpobj.name);
 * // Manual cleanup
 * tmpobj.removeCallback();
 */
export function dirSync(options?: DirOptions): DirResult;

/**
 * Asynchronous filename generation.
 *
 * Generates a unique filename in the specified directory.
 *
 * @example
 * import * as tmp from 'tmp';
 *
 * tmp.tmpName((err, path) => {
 *     if (err) throw err;
 *
 *     console.log('Created temporary filename: ', path);
 * });
 */
export function tmpName(options: TmpNameOptions, cb: TmpNameCallback): void;
export function tmpName(cb: TmpNameCallback): void;

/**
 * Synchronous filename generation.
 *
 * Synchronously generates a unique filename in the specified directory.
 *
 * @example
 * import * as tmp from 'tmp';
 *
 * const name = tmp.tmpNameSync();
 * console.log('Created temporary filename: ', name);
 */
export function tmpNameSync(options?: TmpNameOptions): string;

/**
 * Graceful cleanup.
 *
 * If graceful cleanup is set, `tmp` will remove all controlled temporary objects on process exit,
 * otherwise the temporary objects will remain in place, waiting to be cleaned up on system
 * restart or otherwise scheduled temporary object removal.
 *
 * @example
 * import * as tmp from 'tmp';
 *
 * tmp.setGracefulCleanup();
 */
export function setGracefulCleanup(): void;
