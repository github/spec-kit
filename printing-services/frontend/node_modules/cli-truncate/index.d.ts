declare namespace cliTruncate {
	interface Options {
		/**
		Position to truncate the string.

		@default 'end'
		*/
		readonly position?: 'start' | 'middle' | 'end';

		/**
		Add a space between the text and the ellipsis.

		@default false

		@example
		```
		cliTruncate('unicorns', 5, {position: 'end', space: true});
		//=> 'uni …'

		cliTruncate('unicorns', 5, {position: 'end', space: false});
		//=> 'unic…'

		cliTruncate('unicorns', 6, {position: 'start', space: true});
		//=> '… orns'

		cliTruncate('unicorns', 7, {position: 'middle', space: true});
		//=> 'uni … s'
		```
		*/
		readonly space?: boolean;

		/**
		Truncate the string from a whitespace if it is within 3 characters from the actual breaking point.

		@default false

		@example
		```
		cliTruncate('unicorns rainbow dragons', 20, {position: 'start', preferTruncationOnSpace: true});
		//=> '…rainbow dragons'

		cliTruncate('unicorns rainbow dragons', 20, {position: 'middle', preferTruncationOnSpace: true});
		//=> 'unicorns…dragons'

		cliTruncate('unicorns rainbow dragons', 6, {position: 'end', preferTruncationOnSpace: true});
		//=> 'unico…'
		````
		*/
		readonly preferTruncationOnSpace?: boolean;
	}
}

/**
Truncate a string to a specific width in the terminal.

@param text - Text to truncate.
@param columns - Columns to occupy in the terminal.

@example
```
import cliTruncate = require('cli-truncate');

cliTruncate('unicorn', 4);
//=> 'uni…'

// Truncate at different positions
cliTruncate('unicorn', 4, {position: 'start'});
//=> '…orn'

cliTruncate('unicorn', 4, {position: 'middle'});
//=> 'un…n'

cliTruncate('\u001B[31municorn\u001B[39m', 4);
//=> '\u001B[31muni\u001B[39m…'

// Truncate Unicode surrogate pairs
cliTruncate('uni\uD83C\uDE00corn', 5);
//=> 'uni\uD83C\uDE00…'

// Truncate fullwidth characters
cliTruncate('안녕하세요', 3);
//=> '안…'

// Truncate the paragraph to the terminal width
const paragraph = 'Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa.';
cliTruncate(paragraph, process.stdout.columns));
//=> 'Lorem ipsum dolor sit amet, consectetuer adipiscing…'
```
*/
declare function cliTruncate(
	text: string,
	columns: number,
	options?: cliTruncate.Options
): string;

export = cliTruncate;
