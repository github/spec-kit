class AlreadyHasPlaceholderDataProperty extends Error {
  /**
   * @param {import('jscodeshift').CallExpression} callExpression
   * @param {string} filePath
   */
  constructor(callExpression, filePath) {
    super('')
    this.message = this.buildMessage(callExpression, filePath)
    this.name = 'AlreadyHasPlaceholderDataProperty'
  }

  /**
   * @param {import('jscodeshift').CallExpression} callExpression
   * @param {string} filePath
   * @returns {string}
   */
  buildMessage(callExpression, filePath) {
    const location = callExpression.callee.loc
    const start = location.start.line
    const end = location.end.line

    return `The usage in file "${filePath}" at line ${start}:${end} already contains a a "placeholderData" property. Please migrate this usage manually.`
  }
}

module.exports = AlreadyHasPlaceholderDataProperty
