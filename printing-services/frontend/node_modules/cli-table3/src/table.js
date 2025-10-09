const utils = require('./utils');
const tableLayout = require('./layout-manager');

class Table extends Array {
  constructor(options) {
    super();

    this.options = utils.mergeOptions(options);
  }

  toString() {
    let array = this;
    let headersPresent = this.options.head && this.options.head.length;
    if (headersPresent) {
      array = [this.options.head];
      if (this.length) {
        array.push.apply(array, this);
      }
    } else {
      this.options.style.head = [];
    }

    let cells = tableLayout.makeTableLayout(array);

    cells.forEach(function (row) {
      row.forEach(function (cell) {
        cell.mergeTableOptions(this.options, cells);
      }, this);
    }, this);

    tableLayout.computeWidths(this.options.colWidths, cells);
    tableLayout.computeHeights(this.options.rowHeights, cells);

    cells.forEach(function (row) {
      row.forEach(function (cell) {
        cell.init(this.options);
      }, this);
    }, this);

    let result = [];

    for (let rowIndex = 0; rowIndex < cells.length; rowIndex++) {
      let row = cells[rowIndex];
      let heightOfRow = this.options.rowHeights[rowIndex];

      if (rowIndex === 0 || !this.options.style.compact || (rowIndex == 1 && headersPresent)) {
        doDraw(row, 'top', result);
      }

      for (let lineNum = 0; lineNum < heightOfRow; lineNum++) {
        doDraw(row, lineNum, result);
      }

      if (rowIndex + 1 == cells.length) {
        doDraw(row, 'bottom', result);
      }
    }

    return result.join('\n');
  }

  get width() {
    let str = this.toString().split('\n');
    return str[0].length;
  }
}

function doDraw(row, lineNum, result) {
  let line = [];
  row.forEach(function (cell) {
    line.push(cell.draw(lineNum));
  });
  let str = line.join('');
  if (str.length) result.push(str);
}

module.exports = Table;
