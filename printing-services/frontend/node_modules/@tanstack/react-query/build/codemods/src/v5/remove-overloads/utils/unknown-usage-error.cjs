class UnknownUsageError extends Error {
  /**
   * @param {import('jscodeshift').CallExpression} callExpression
   * @param {string} filePath
   */
  constructor(callExpression, filePath) {
    super('')
    this.message = this.buildMessage(callExpression, filePath)
    this.name = 'UnknownUsageError'
  }

  /**
   *
   * @param {import('jscodeshift').CallExpression} callExpression
   * @param {string} filePath
   * @returns {string}
   */
  buildMessage(callExpression, filePath) {
    const location = callExpression.callee.loc
    const start = location.start.line
    const end = location.end.line

    return `The usage in file "${filePath}" at line ${start}:${end} could not be transformed into the new syntax. Please do this manually.`
  }
}

module.exports = UnknownUsageError
