/// <reference types="node"/>

declare namespace logUpdate {
	interface LogUpdate {
		/**
		Log to `stdout` by overwriting the previous output in the terminal.

		@param text - The text to log to `stdout`.

		@example
		```
		import logUpdate = require('log-update');

		const frames = ['-', '\\', '|', '/'];
		let i = 0;

		setInterval(() => {
			const frame = frames[i = ++i % frames.length];

			logUpdate(
		`
				♥♥
		${frame} unicorns ${frame}
				♥♥
		`
			);
		}, 80);
		```
		*/
		(...text: string[]): void;

		/**
		Clear the logged output.
		*/
		clear(): void;

		/**
		Persist the logged output. Useful if you want to start a new log session below the current one.
		*/
		done(): void;
	}

	interface Options {
		/**
		Show the cursor. This can be useful when a CLI accepts input from a user.

		@example
		```
		import logUpdate = require('log-update');

		// Write output but don't hide the cursor
		const log = logUpdate.create(process.stdout, {
			showCursor: true
		});
		```
		*/
		readonly showCursor?: boolean;
	}
}

declare const logUpdate: logUpdate.LogUpdate & {
	/**
	Log to `stderr` by overwriting the previous output in the terminal.

	@param text - The text to log to `stderr`.
	*/
	readonly stderr: logUpdate.LogUpdate;

	/**
	Get a `logUpdate` method that logs to the specified stream.

	@param stream - The stream to log to.
	*/
	readonly create: (
		stream: NodeJS.WritableStream,
		options?: logUpdate.Options
	) => logUpdate.LogUpdate;
};

export = logUpdate;
