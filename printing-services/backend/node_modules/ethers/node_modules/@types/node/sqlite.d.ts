/**
 * The `node:sqlite` module facilitates working with SQLite databases.
 * To access it:
 *
 * ```js
 * import sqlite from 'node:sqlite';
 * ```
 *
 * This module is only available under the `node:` scheme. The following will not
 * work:
 *
 * ```js
 * import sqlite from 'node:sqlite';
 * ```
 *
 * The following example shows the basic usage of the `node:sqlite` module to open
 * an in-memory database, write data to the database, and then read the data back.
 *
 * ```js
 * import { DatabaseSync } from 'node:sqlite';
 * const database = new DatabaseSync(':memory:');
 *
 * // Execute SQL statements from strings.
 * database.exec(`
 *   CREATE TABLE data(
 *     key INTEGER PRIMARY KEY,
 *     value TEXT
 *   ) STRICT
 * `);
 * // Create a prepared statement to insert data into the database.
 * const insert = database.prepare('INSERT INTO data (key, value) VALUES (?, ?)');
 * // Execute the prepared statement with bound values.
 * insert.run(1, 'hello');
 * insert.run(2, 'world');
 * // Create a prepared statement to read data from the database.
 * const query = database.prepare('SELECT * FROM data ORDER BY key');
 * // Execute the prepared statement and log the result set.
 * console.log(query.all());
 * // Prints: [ { key: 1, value: 'hello' }, { key: 2, value: 'world' } ]
 * ```
 * @since v22.5.0
 * @experimental
 * @see [source](https://github.com/nodejs/node/blob/v22.x/lib/sqlite.js)
 */
declare module "node:sqlite" {
    interface DatabaseSyncOptions {
        /**
         * If `true`, the database is opened by the constructor.
         * When this value is `false`, the database must be opened via the `open()` method.
         */
        open?: boolean | undefined;
    }
    /**
     * This class represents a single [connection](https://www.sqlite.org/c3ref/sqlite3.html) to a SQLite database. All APIs
     * exposed by this class execute synchronously.
     * @since v22.5.0
     */
    class DatabaseSync {
        /**
         * Constructs a new `DatabaseSync` instance.
         * @param location The location of the database.
         * A SQLite database can be stored in a file or completely [in memory](https://www.sqlite.org/inmemorydb.html).
         * To use a file-backed database, the location should be a file path.
         * To use an in-memory database, the location should be the special name `':memory:'`.
         * @param options Configuration options for the database connection.
         */
        constructor(location: string, options?: DatabaseSyncOptions);
        /**
         * Closes the database connection. An exception is thrown if the database is not
         * open. This method is a wrapper around [`sqlite3_close_v2()`](https://www.sqlite.org/c3ref/close.html).
         * @since v22.5.0
         */
        close(): void;
        /**
         * This method allows one or more SQL statements to be executed without returning
         * any results. This method is useful when executing SQL statements read from a
         * file. This method is a wrapper around [`sqlite3_exec()`](https://www.sqlite.org/c3ref/exec.html).
         * @since v22.5.0
         * @param sql A SQL string to execute.
         */
        exec(sql: string): void;
        /**
         * Opens the database specified in the `location` argument of the `DatabaseSync`constructor. This method should only be used when the database is not opened via
         * the constructor. An exception is thrown if the database is already open.
         * @since v22.5.0
         */
        open(): void;
        /**
         * Compiles a SQL statement into a [prepared statement](https://www.sqlite.org/c3ref/stmt.html). This method is a wrapper
         * around [`sqlite3_prepare_v2()`](https://www.sqlite.org/c3ref/prepare.html).
         * @since v22.5.0
         * @param sql A SQL string to compile to a prepared statement.
         * @return The prepared statement.
         */
        prepare(sql: string): StatementSync;
    }
    type SupportedValueType = null | number | bigint | string | Uint8Array;
    interface StatementResultingChanges {
        /**
         * The number of rows modified, inserted, or deleted by the most recently completed `INSERT`, `UPDATE`, or `DELETE` statement.
         * This field is either a number or a `BigInt` depending on the prepared statement's configuration.
         * This property is the result of [`sqlite3_changes64()`](https://www.sqlite.org/c3ref/changes.html).
         */
        changes: number | bigint;
        /**
         * The most recently inserted rowid.
         * This field is either a number or a `BigInt` depending on the prepared statement's configuration.
         * This property is the result of [`sqlite3_last_insert_rowid()`](https://www.sqlite.org/c3ref/last_insert_rowid.html).
         */
        lastInsertRowid: number | bigint;
    }
    /**
     * This class represents a single [prepared statement](https://www.sqlite.org/c3ref/stmt.html). This class cannot be
     * instantiated via its constructor. Instead, instances are created via the`database.prepare()` method. All APIs exposed by this class execute
     * synchronously.
     *
     * A prepared statement is an efficient binary representation of the SQL used to
     * create it. Prepared statements are parameterizable, and can be invoked multiple
     * times with different bound values. Parameters also offer protection against [SQL injection](https://en.wikipedia.org/wiki/SQL_injection) attacks. For these reasons, prepared statements are
     * preferred
     * over hand-crafted SQL strings when handling user input.
     * @since v22.5.0
     */
    class StatementSync {
        private constructor();
        /**
         * This method executes a prepared statement and returns all results as an array of
         * objects. If the prepared statement does not return any results, this method
         * returns an empty array. The prepared statement [parameters are bound](https://www.sqlite.org/c3ref/bind_blob.html) using
         * the values in `namedParameters` and `anonymousParameters`.
         * @since v22.5.0
         * @param namedParameters An optional object used to bind named parameters. The keys of this object are used to configure the mapping.
         * @param anonymousParameters Zero or more values to bind to anonymous parameters.
         * @return An array of objects. Each object corresponds to a row returned by executing the prepared statement. The keys and values of each object correspond to the column names and values of
         * the row.
         */
        all(...anonymousParameters: SupportedValueType[]): unknown[];
        all(
            namedParameters: Record<string, SupportedValueType>,
            ...anonymousParameters: SupportedValueType[]
        ): unknown[];
        /**
         * This method returns the source SQL of the prepared statement with parameter
         * placeholders replaced by values. This method is a wrapper around [`sqlite3_expanded_sql()`](https://www.sqlite.org/c3ref/expanded_sql.html).
         * @since v22.5.0
         * @return The source SQL expanded to include parameter values.
         */
        expandedSQL(): string;
        /**
         * This method executes a prepared statement and returns the first result as an
         * object. If the prepared statement does not return any results, this method
         * returns `undefined`. The prepared statement [parameters are bound](https://www.sqlite.org/c3ref/bind_blob.html) using the
         * values in `namedParameters` and `anonymousParameters`.
         * @since v22.5.0
         * @param namedParameters An optional object used to bind named parameters. The keys of this object are used to configure the mapping.
         * @param anonymousParameters Zero or more values to bind to anonymous parameters.
         * @return An object corresponding to the first row returned by executing the prepared statement. The keys and values of the object correspond to the column names and values of the row. If no
         * rows were returned from the database then this method returns `undefined`.
         */
        get(...anonymousParameters: SupportedValueType[]): unknown;
        get(namedParameters: Record<string, SupportedValueType>, ...anonymousParameters: SupportedValueType[]): unknown;
        /**
         * This method executes a prepared statement and returns an object summarizing the
         * resulting changes. The prepared statement [parameters are bound](https://www.sqlite.org/c3ref/bind_blob.html) using the
         * values in `namedParameters` and `anonymousParameters`.
         * @since v22.5.0
         * @param namedParameters An optional object used to bind named parameters. The keys of this object are used to configure the mapping.
         * @param anonymousParameters Zero or more values to bind to anonymous parameters.
         */
        run(...anonymousParameters: SupportedValueType[]): StatementResultingChanges;
        run(
            namedParameters: Record<string, SupportedValueType>,
            ...anonymousParameters: SupportedValueType[]
        ): StatementResultingChanges;
        /**
         * The names of SQLite parameters begin with a prefix character. By default,`node:sqlite` requires that this prefix character is present when binding
         * parameters. However, with the exception of dollar sign character, these
         * prefix characters also require extra quoting when used in object keys.
         *
         * To improve ergonomics, this method can be used to also allow bare named
         * parameters, which do not require the prefix character in JavaScript code. There
         * are several caveats to be aware of when enabling bare named parameters:
         *
         * * The prefix character is still required in SQL.
         * * The prefix character is still allowed in JavaScript. In fact, prefixed names
         * will have slightly better binding performance.
         * * Using ambiguous named parameters, such as `$k` and `@k`, in the same prepared
         * statement will result in an exception as it cannot be determined how to bind
         * a bare name.
         * @since v22.5.0
         * @param enabled Enables or disables support for binding named parameters without the prefix character.
         */
        setAllowBareNamedParameters(enabled: boolean): void;
        /**
         * When reading from the database, SQLite `INTEGER`s are mapped to JavaScript
         * numbers by default. However, SQLite `INTEGER`s can store values larger than
         * JavaScript numbers are capable of representing. In such cases, this method can
         * be used to read `INTEGER` data using JavaScript `BigInt`s. This method has no
         * impact on database write operations where numbers and `BigInt`s are both
         * supported at all times.
         * @since v22.5.0
         * @param enabled Enables or disables the use of `BigInt`s when reading `INTEGER` fields from the database.
         */
        setReadBigInts(enabled: boolean): void;
        /**
         * This method returns the source SQL of the prepared statement. This method is a
         * wrapper around [`sqlite3_sql()`](https://www.sqlite.org/c3ref/expanded_sql.html).
         * @since v22.5.0
         * @return The source SQL used to create this prepared statement.
         */
        sourceSQL(): string;
    }
}
