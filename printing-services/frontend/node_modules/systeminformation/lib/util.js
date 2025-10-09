'use strict';
// @ts-check
// ==================================================================================
// utils.js
// ----------------------------------------------------------------------------------
// Description:   System Information - library
//                for Node.js
// Copyright:     (c) 2014 - 2025
// Author:        Sebastian Hildebrandt
// ----------------------------------------------------------------------------------
// License:       MIT
// ==================================================================================
// 0. helper functions
// ----------------------------------------------------------------------------------

const os = require('os');
const fs = require('fs');
const path = require('path');
const spawn = require('child_process').spawn;
const exec = require('child_process').exec;
const execSync = require('child_process').execSync;
const util = require('util');

let _platform = process.platform;
const _linux = (_platform === 'linux' || _platform === 'android');
const _darwin = (_platform === 'darwin');
const _windows = (_platform === 'win32');
const _freebsd = (_platform === 'freebsd');
const _openbsd = (_platform === 'openbsd');
const _netbsd = (_platform === 'netbsd');

let _cores = 0;
let wmicPath = '';
let codepage = '';
let _smartMonToolsInstalled = null;
let _rpi_cpuinfo = null;

const WINDIR = process.env.WINDIR || 'C:\\Windows';

// powerShell
let _psChild;
let _psResult = '';
let _psCmds = [];
let _psPersistent = false;
let _powerShell = '';
const _psToUTF8 = '$OutputEncoding = [System.Console]::OutputEncoding = [System.Console]::InputEncoding = [System.Text.Encoding]::UTF8 ; ';
const _psCmdStart = '--###START###--';
const _psError = '--ERROR--';
const _psCmdSeperator = '--###ENDCMD###--';
const _psIdSeperator = '--##ID##--';

const execOptsWin = {
  windowsHide: true,
  maxBuffer: 1024 * 20000,
  encoding: 'UTF-8',
  env: Object.assign({}, process.env, { LANG: 'en_US.UTF-8' })
};

const execOptsLinux = {
  maxBuffer: 1024 * 20000,
  encoding: 'UTF-8',
  stdio: ['pipe', 'pipe', 'ignore']
};

function toInt(value) {
  let result = parseInt(value, 10);
  if (isNaN(result)) {
    result = 0;
  }
  return result;
}

function splitByNumber(str) {
  let numberStarted = false;
  let num = '';
  let cpart = '';
  for (const c of str) {
    if ((c >= '0' && c <= '9') || numberStarted) {
      numberStarted = true;
      num += c;
    } else {
      cpart += c;
    }
  }
  return [cpart, num];
}

const stringObj = new String();
const stringReplace = new String().replace;
const stringToLower = new String().toLowerCase;
const stringToString = new String().toString;
const stringSubstr = new String().substr;
const stringSubstring = new String().substring;
const stringTrim = new String().trim;
const stringStartWith = new String().startsWith;
const mathMin = Math.min;

function isFunction(functionToCheck) {
  let getType = {};
  return functionToCheck && getType.toString.call(functionToCheck) === '[object Function]';
}

function unique(obj) {
  let uniques = [];
  let stringify = {};
  for (let i = 0; i < obj.length; i++) {
    let keys = Object.keys(obj[i]);
    keys.sort(function (a, b) { return a - b; });
    let str = '';
    for (let j = 0; j < keys.length; j++) {
      str += JSON.stringify(keys[j]);
      str += JSON.stringify(obj[i][keys[j]]);
    }
    if (!{}.hasOwnProperty.call(stringify, str)) {
      uniques.push(obj[i]);
      stringify[str] = true;
    }
  }
  return uniques;
}

function sortByKey(array, keys) {
  return array.sort(function (a, b) {
    let x = '';
    let y = '';
    keys.forEach(function (key) {
      x = x + a[key]; y = y + b[key];
    });
    return ((x < y) ? -1 : ((x > y) ? 1 : 0));
  });
}

function cores() {
  if (_cores === 0) {
    _cores = os.cpus().length;
  }
  return _cores;
}

function getValue(lines, property, separator, trimmed, lineMatch) {
  separator = separator || ':';
  property = property.toLowerCase();
  trimmed = trimmed || false;
  lineMatch = lineMatch || false;
  let result = '';
  lines.some((line) => {
    let lineLower = line.toLowerCase().replace(/\t/g, '');
    if (trimmed) {
      lineLower = lineLower.trim();
    }
    if (lineLower.startsWith(property) && (lineMatch ? (lineLower.match(property + separator)) || (lineLower.match(property + ' ' + separator)) : true)) {
      const parts = trimmed ? line.trim().split(separator) : line.split(separator);
      if (parts.length >= 2) {
        parts.shift();
        result = parts.join(separator).trim();
        return true;
      }
    }
  });
  return result;
}

function decodeEscapeSequence(str, base) {
  base = base || 16;
  return str.replace(/\\x([0-9A-Fa-f]{2})/g, function () {
    return String.fromCharCode(parseInt(arguments[1], base));
  });
}

function detectSplit(str) {
  let seperator = '';
  let part = 0;
  str.split('').forEach(element => {
    if (element >= '0' && element <= '9') {
      if (part === 1) { part++; }
    } else {
      if (part === 0) { part++; }
      if (part === 1) {
        seperator += element;
      }
    }
  });
  return seperator;
}

function parseTime(t, pmDesignator) {
  pmDesignator = pmDesignator || '';
  t = t.toUpperCase();
  let hour = 0;
  let min = 0;
  let splitter = detectSplit(t);
  let parts = t.split(splitter);
  if (parts.length >= 2) {
    if (parts[2]) {
      parts[1] += parts[2];
    }
    let isPM = (parts[1] && (parts[1].toLowerCase().indexOf('pm') > -1) || (parts[1].toLowerCase().indexOf('p.m.') > -1) || (parts[1].toLowerCase().indexOf('p. m.') > -1) || (parts[1].toLowerCase().indexOf('n') > -1) || (parts[1].toLowerCase().indexOf('ch') > -1) || (parts[1].toLowerCase().indexOf('ös') > -1) || (pmDesignator && parts[1].toLowerCase().indexOf(pmDesignator) > -1));
    hour = parseInt(parts[0], 10);
    min = parseInt(parts[1], 10);
    hour = isPM && hour < 12 ? hour + 12 : hour;
    return ('0' + hour).substr(-2) + ':' + ('0' + min).substr(-2);
  }
}

function parseDateTime(dt, culture) {
  const result = {
    date: '',
    time: ''
  };
  culture = culture || {};
  let dateFormat = (culture.dateFormat || '').toLowerCase();
  let pmDesignator = (culture.pmDesignator || '');

  const parts = dt.split(' ');
  if (parts[0]) {
    if (parts[0].indexOf('/') >= 0) {
      // Dateformat: mm/dd/yyyy or dd/mm/yyyy or dd/mm/yy or yyyy/mm/dd
      const dtparts = parts[0].split('/');
      if (dtparts.length === 3) {
        if (dtparts[0].length === 4) {
          // Dateformat: yyyy/mm/dd
          result.date = dtparts[0] + '-' + ('0' + dtparts[1]).substr(-2) + '-' + ('0' + dtparts[2]).substr(-2);
        } else if (dtparts[2].length === 2) {
          if ((dateFormat.indexOf('/d/') > -1 || dateFormat.indexOf('/dd/') > -1)) {
            // Dateformat: mm/dd/yy
            result.date = '20' + dtparts[2] + '-' + ('0' + dtparts[1]).substr(-2) + '-' + ('0' + dtparts[0]).substr(-2);
          } else {
            // Dateformat: dd/mm/yy
            result.date = '20' + dtparts[2] + '-' + ('0' + dtparts[1]).substr(-2) + '-' + ('0' + dtparts[0]).substr(-2);
          }
        } else {
          // Dateformat: mm/dd/yyyy or dd/mm/yyyy
          const isEN = ((dt.toLowerCase().indexOf('pm') > -1) || (dt.toLowerCase().indexOf('p.m.') > -1) || (dt.toLowerCase().indexOf('p. m.') > -1) || (dt.toLowerCase().indexOf('am') > -1) || (dt.toLowerCase().indexOf('a.m.') > -1) || (dt.toLowerCase().indexOf('a. m.') > -1));
          if ((isEN || dateFormat.indexOf('/d/') > -1 || dateFormat.indexOf('/dd/') > -1) && dateFormat.indexOf('dd/') !== 0) {
            // Dateformat: mm/dd/yyyy
            result.date = dtparts[2] + '-' + ('0' + dtparts[0]).substr(-2) + '-' + ('0' + dtparts[1]).substr(-2);
          } else {
            // Dateformat: dd/mm/yyyy
            result.date = dtparts[2] + '-' + ('0' + dtparts[1]).substr(-2) + '-' + ('0' + dtparts[0]).substr(-2);
          }
        }
      }
    }
    if (parts[0].indexOf('.') >= 0) {
      const dtparts = parts[0].split('.');
      if (dtparts.length === 3) {
        if (dateFormat.indexOf('.d.') > -1 || dateFormat.indexOf('.dd.') > -1) {
          // Dateformat: mm.dd.yyyy
          result.date = dtparts[2] + '-' + ('0' + dtparts[0]).substr(-2) + '-' + ('0' + dtparts[1]).substr(-2);
        } else {
          // Dateformat: dd.mm.yyyy
          result.date = dtparts[2] + '-' + ('0' + dtparts[1]).substr(-2) + '-' + ('0' + dtparts[0]).substr(-2);
        }
      }
    }
    if (parts[0].indexOf('-') >= 0) {
      // Dateformat: yyyy-mm-dd
      const dtparts = parts[0].split('-');
      if (dtparts.length === 3) {
        result.date = dtparts[0] + '-' + ('0' + dtparts[1]).substr(-2) + '-' + ('0' + dtparts[2]).substr(-2);
      }
    }
  }
  if (parts[1]) {
    parts.shift();
    let time = parts.join(' ');
    result.time = parseTime(time, pmDesignator);
  }
  return result;
}

function parseHead(head, rights) {
  let space = (rights > 0);
  let count = 1;
  let from = 0;
  let to = 0;
  let result = [];
  for (let i = 0; i < head.length; i++) {
    if (count <= rights) {
      if (/\s/.test(head[i]) && !space) {
        to = i - 1;
        result.push({
          from: from,
          to: to + 1,
          cap: head.substring(from, to + 1)
        });
        from = to + 2;
        count++;
      }
      space = head[i] === ' ';
    } else {
      if (!/\s/.test(head[i]) && space) {
        to = i - 1;
        if (from < to) {
          result.push({
            from: from,
            to: to,
            cap: head.substring(from, to)
          });
        }
        from = to + 1;
        count++;
      }
      space = head[i] === ' ';
    }
  }
  to = 5000;
  result.push({
    from: from,
    to: to,
    cap: head.substring(from, to)
  });
  let len = result.length;
  for (let i = 0; i < len; i++) {
    if (result[i].cap.replace(/\s/g, '').length === 0) {
      if (i + 1 < len) {
        result[i].to = result[i + 1].to;
        result[i].cap = result[i].cap + result[i + 1].cap;
        result.splice(i + 1, 1);
        len = len - 1;
      }
    }
  }
  return result;
}

function findObjectByKey(array, key, value) {
  for (let i = 0; i < array.length; i++) {
    if (array[i][key] === value) {
      return i;
    }
  }
  return -1;
}

function getPowershell() {
  _powerShell = 'powershell.exe';
  if (_windows) {
    const defaultPath = `${WINDIR}\\system32\\WindowsPowerShell\\v1.0\\powershell.exe`;
    if (fs.existsSync(defaultPath)) {
      _powerShell = defaultPath;
    }
  }
}

function getWmic() {
  if (os.type() === 'Windows_NT' && !wmicPath) {
    wmicPath = WINDIR + '\\system32\\wbem\\wmic.exe';
    if (!fs.existsSync(wmicPath)) {
      try {
        const wmicPathArray = execSync('WHERE WMIC', execOptsWin).toString().split('\r\n');
        if (wmicPathArray && wmicPathArray.length) {
          wmicPath = wmicPathArray[0];
        } else {
          wmicPath = 'wmic';
        }
      } catch (e) {
        wmicPath = 'wmic';
      }
    }
  }
  return wmicPath;
}

function wmic(command) {
  return new Promise((resolve) => {
    process.nextTick(() => {
      try {
        powerShell(getWmic() + ' ' + command).then(stdout => {
          resolve(stdout, '');
        });
      } catch (e) {
        resolve('', e);
      }
    });
  });
}

function getVboxmanage() {
  return _windows ? `"${process.env.VBOX_INSTALL_PATH || process.env.VBOX_MSI_INSTALL_PATH}\\VBoxManage.exe"` : 'vboxmanage';
}

function powerShellProceedResults(data) {
  let id = '';
  let parts;
  let res = '';
  // startID
  if (data.indexOf(_psCmdStart) >= 0) {
    parts = data.split(_psCmdStart);
    const parts2 = parts[1].split(_psIdSeperator);
    id = parts2[0];
    if (parts2.length > 1) {
      data = parts2.slice(1).join(_psIdSeperator);
    }
  }
  // result;
  if (data.indexOf(_psCmdSeperator) >= 0) {
    parts = data.split(_psCmdSeperator);
    res = parts[0];
  }
  let remove = -1;
  for (let i = 0; i < _psCmds.length; i++) {
    if (_psCmds[i].id === id) {
      remove = i;
      _psCmds[i].callback(res);
    }
  }
  if (remove >= 0) {
    _psCmds.splice(remove, 1);
  }
}

function powerShellStart() {
  if (!_psChild) {
    _psChild = spawn(_powerShell, ['-NoProfile', '-NoLogo', '-InputFormat', 'Text', '-NoExit', '-Command', '-'], {
      stdio: 'pipe',
      windowsHide: true,
      maxBuffer: 1024 * 20000,
      encoding: 'UTF-8',
      env: Object.assign({}, process.env, { LANG: 'en_US.UTF-8' })
    });
    if (_psChild && _psChild.pid) {
      _psPersistent = true;
      _psChild.stdout.on('data', function (data) {
        _psResult = _psResult + data.toString('utf8');
        if (data.indexOf(_psCmdSeperator) >= 0) {
          powerShellProceedResults(_psResult);
          _psResult = '';
        }
      });
      _psChild.stderr.on('data', function () {
        powerShellProceedResults(_psResult + _psError);
      });
      _psChild.on('error', function () {
        powerShellProceedResults(_psResult + _psError);
      });
      _psChild.on('close', function () {
        if (_psChild) { _psChild.kill(); }
      });
    }
  }
}

function powerShellRelease() {
  try {
    if (_psChild) {
      _psChild.stdin.write('exit' + os.EOL);
      _psChild.stdin.end();
      _psPersistent = false;
    }
  } catch (e) {
    if (_psChild) { _psChild.kill(); }
  }
  _psChild = null;
}

function powerShell(cmd) {

  /// const pattern = [
  ///   '[\\u001B\\u009B][[\\]()#;?]*(?:(?:(?:(?:;[-a-zA-Z\\d\\/#&.:=?%@~_]+)*|[a-zA-Z\\d]+(?:;[-a-zA-Z\\d\\/#&.:=?%@~_]*)*)?\\u0007)',
  ///   '(?:(?:\\d{1,4}(?:;\\d{0,4})*)?[\\dA-PR-TZcf-nq-uy=><~]))'
  /// ].join('|');

  if (_psPersistent) {
    const id = Math.random().toString(36).substring(2, 12);
    return new Promise((resolve) => {
      process.nextTick(() => {
        function callback(data) {
          resolve(data);
        }
        _psCmds.push({
          id,
          cmd,
          callback,
          start: new Date()
        });
        try {
          if (_psChild && _psChild.pid) {
            _psChild.stdin.write(_psToUTF8 + 'echo ' + _psCmdStart + id + _psIdSeperator + '; ' + os.EOL + cmd + os.EOL + 'echo ' + _psCmdSeperator + os.EOL);
          }
        } catch (e) {
          resolve('');
        }
      });
    });

  } else {
    let result = '';

    return new Promise((resolve) => {
      process.nextTick(() => {
        try {
          const child = spawn(_powerShell, ['-NoProfile', '-NoLogo', '-InputFormat', 'Text', '-NoExit', '-ExecutionPolicy', 'Unrestricted', '-Command', '-'], {
            stdio: 'pipe',
            windowsHide: true,
            maxBuffer: 1024 * 20000,
            encoding: 'UTF-8',
            env: Object.assign({}, process.env, { LANG: 'en_US.UTF-8' })
          });

          if (child && !child.pid) {
            child.on('error', function () {
              resolve(result);
            });
          }
          if (child && child.pid) {
            child.stdout.on('data', function (data) {
              result = result + data.toString('utf8');
            });
            child.stderr.on('data', function () {
              child.kill();
              resolve(result);
            });
            child.on('close', function () {
              child.kill();

              resolve(result);
            });
            child.on('error', function () {
              child.kill();
              resolve(result);
            });
            try {
              child.stdin.write(_psToUTF8 + cmd + os.EOL);
              child.stdin.write('exit' + os.EOL);
              child.stdin.end();
            } catch (e) {
              child.kill();
              resolve(result);
            }
          } else {
            resolve(result);
          }
        } catch (e) {
          resolve(result);
        }
      });
    });
  }
}

function execSafe(cmd, args, options) {
  let result = '';
  options = options || {};

  return new Promise((resolve) => {
    process.nextTick(() => {
      try {
        const child = spawn(cmd, args, options);

        if (child && !child.pid) {
          child.on('error', function () {
            resolve(result);
          });
        }
        if (child && child.pid) {
          child.stdout.on('data', function (data) {
            result += data.toString();
          });
          child.on('close', function () {
            child.kill();
            resolve(result);
          });
          child.on('error', function () {
            child.kill();
            resolve(result);
          });
        } else {
          resolve(result);
        }
      } catch (e) {
        resolve(result);
      }
    });
  });
}

function getCodepage() {
  if (_windows) {
    if (!codepage) {
      try {
        const stdout = execSync('chcp', execOptsWin);
        const lines = stdout.toString().split('\r\n');
        const parts = lines[0].split(':');
        codepage = parts.length > 1 ? parts[1].replace('.', '').trim() : '';
      } catch (err) {
        codepage = '437';
      }
    }
    return codepage;
  }
  if (_linux || _darwin || _freebsd || _openbsd || _netbsd) {
    if (!codepage) {
      try {
        const stdout = execSync('echo $LANG', execOptsLinux);
        const lines = stdout.toString().split('\r\n');
        const parts = lines[0].split('.');
        codepage = parts.length > 1 ? parts[1].trim() : '';
        if (!codepage) {
          codepage = 'UTF-8';
        }
      } catch (err) {
        codepage = 'UTF-8';
      }
    }
    return codepage;
  }
}

function smartMonToolsInstalled() {
  if (_smartMonToolsInstalled !== null) {
    return _smartMonToolsInstalled;
  }
  _smartMonToolsInstalled = false;
  if (_windows) {
    try {
      const pathArray = execSync('WHERE smartctl 2>nul', execOptsWin).toString().split('\r\n');
      if (pathArray && pathArray.length) {
        _smartMonToolsInstalled = pathArray[0].indexOf(':\\') >= 0;
      } else {
        _smartMonToolsInstalled = false;
      }
    } catch (e) {
      _smartMonToolsInstalled = false;
    }
  }
  if (_linux || _darwin || _freebsd || _openbsd || _netbsd) {
    try {
      const pathArray = execSync('which smartctl 2>/dev/null', execOptsLinux).toString().split('\r\n');
      _smartMonToolsInstalled = pathArray.length > 0;
    } catch (e) {
      util.noop();
    }
  }
  return _smartMonToolsInstalled;
}

// reference values: https://elinux.org/RPi_HardwareHistory
// https://www.raspberrypi.org/documentation/hardware/raspberrypi/revision-codes/README.md
// https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#hardware-revision-codes

function isRaspberry(cpuinfo) {
  const PI_MODEL_NO = [
    'BCM2708',
    'BCM2709',
    'BCM2710',
    'BCM2711',
    'BCM2712',
    'BCM2835',
    'BCM2836',
    'BCM2837',
    'BCM2837B0'
  ];
  if (_rpi_cpuinfo !== null) {
    cpuinfo = _rpi_cpuinfo;
  } else if (cpuinfo === undefined) {
    try {
      cpuinfo = fs.readFileSync('/proc/cpuinfo', { encoding: 'utf8' }).toString().split('\n');
      _rpi_cpuinfo = cpuinfo;
    } catch (e) {
      return false;
    }
  }

  const hardware = getValue(cpuinfo, 'hardware');
  const model = getValue(cpuinfo, 'model');
  return ((hardware && PI_MODEL_NO.indexOf(hardware) > -1) || (model && model.indexOf('Raspberry Pi') > -1));
}

function isRaspbian() {
  let osrelease = [];
  try {
    osrelease = fs.readFileSync('/etc/os-release', { encoding: 'utf8' }).toString().split('\n');
  } catch (e) {
    return false;
  }
  const id = getValue(osrelease, 'id', '=');
  return (id && id.indexOf('raspbian') > -1);
}

function execWin(cmd, opts, callback) {
  if (!callback) {
    callback = opts;
    opts = execOptsWin;
  }
  let newCmd = 'chcp 65001 > nul && cmd /C ' + cmd + ' && chcp ' + codepage + ' > nul';
  exec(newCmd, opts, function (error, stdout) {
    callback(error, stdout);
  });
}

function darwinXcodeExists() {
  const cmdLineToolsExists = fs.existsSync('/Library/Developer/CommandLineTools/usr/bin/');
  const xcodeAppExists = fs.existsSync('/Applications/Xcode.app/Contents/Developer/Tools');
  const xcodeExists = fs.existsSync('/Library/Developer/Xcode/');
  return (cmdLineToolsExists || xcodeExists || xcodeAppExists);
}

function nanoSeconds() {
  const time = process.hrtime();
  if (!Array.isArray(time) || time.length !== 2) {
    return 0;
  }
  return +time[0] * 1e9 + +time[1];
}

function countUniqueLines(lines, startingWith) {
  startingWith = startingWith || '';
  const uniqueLines = [];
  lines.forEach(line => {
    if (line.startsWith(startingWith)) {
      if (uniqueLines.indexOf(line) === -1) {
        uniqueLines.push(line);
      }
    }
  });
  return uniqueLines.length;
}

function countLines(lines, startingWith) {
  startingWith = startingWith || '';
  const uniqueLines = [];
  lines.forEach(line => {
    if (line.startsWith(startingWith)) {
      uniqueLines.push(line);
    }
  });
  return uniqueLines.length;
}

function sanitizeShellString(str, strict) {
  if (typeof strict === 'undefined') { strict = false; }
  const s = str || '';
  let result = '';
  const l = mathMin(s.length, 2000);
  for (let i = 0; i <= l; i++) {
    if (!(s[i] === undefined ||
      s[i] === '>' ||
      s[i] === '<' ||
      s[i] === '*' ||
      s[i] === '?' ||
      s[i] === '[' ||
      s[i] === ']' ||
      s[i] === '|' ||
      s[i] === '˚' ||
      s[i] === '$' ||
      s[i] === ';' ||
      s[i] === '&' ||
      s[i] === ']' ||
      s[i] === '#' ||
      s[i] === '\\' ||
      s[i] === '\t' ||
      s[i] === '\n' ||
      s[i] === '\r' ||
      s[i] === '\'' ||
      s[i] === '`' ||
      s[i] === '"' ||
      s[i].length > 1 ||
      (strict && s[i] === '(') ||
      (strict && s[i] === ')') ||
      (strict && s[i] === '@') ||
      (strict && s[i] === ' ') ||
      (strict && s[i] == '{') ||
      (strict && s[i] == ';') ||
      (strict && s[i] == '}'))) {
      result = result + s[i];
    }
  }
  return result;
}

function isPrototypePolluted() {
  const s = '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
  let notPolluted = true;
  let st = '';

  try {
    st.__proto__.replace = stringReplace;
    st.__proto__.toLowerCase = stringToLower;
    st.__proto__.toString = stringToString;
    st.__proto__.substr = stringSubstr;
    st.__proto__.substring = stringSubstring;
    st.__proto__.trim = stringTrim;
    st.__proto__.startsWith = stringStartWith;
  } catch (e) {
    Object.setPrototypeOf(st, stringObj);
  }
  notPolluted = notPolluted || (s.length !== 62);
  const ms = Date.now();
  if (typeof ms === 'number' && ms > 1600000000000) {
    const l = ms % 100 + 15;
    for (let i = 0; i < l; i++) {
      const r = Math.random() * 61.99999999 + 1;
      const rs = parseInt(Math.floor(r).toString(), 10);
      const rs2 = parseInt(r.toString().split('.')[0], 10);
      const q = Math.random() * 61.99999999 + 1;
      const qs = parseInt(Math.floor(q).toString(), 10);
      const qs2 = parseInt(q.toString().split('.')[0], 10);
      notPolluted = notPolluted && (r !== q);
      notPolluted = notPolluted && rs === rs2 && qs === qs2;
      st += s[rs - 1];
    }
    notPolluted = notPolluted && st.length === l;
    // string manipulation
    let p = Math.random() * l * 0.9999999999;
    let stm = st.substr(0, p) + ' ' + st.substr(p, 2000);
    try {
      stm.__proto__.replace = stringReplace;
    } catch (e) {
      Object.setPrototypeOf(stm, stringObj);
    }
    let sto = stm.replace(/ /g, '');
    notPolluted = notPolluted && st === sto;
    p = Math.random() * l * 0.9999999999;
    stm = st.substr(0, p) + '{' + st.substr(p, 2000);
    sto = stm.replace(/{/g, '');
    notPolluted = notPolluted && st === sto;
    p = Math.random() * l * 0.9999999999;
    stm = st.substr(0, p) + '*' + st.substr(p, 2000);
    sto = stm.replace(/\*/g, '');
    notPolluted = notPolluted && st === sto;
    p = Math.random() * l * 0.9999999999;
    stm = st.substr(0, p) + '$' + st.substr(p, 2000);
    sto = stm.replace(/\$/g, '');
    notPolluted = notPolluted && st === sto;

    // lower
    const stl = st.toLowerCase();
    notPolluted = notPolluted && (stl.length === l) && stl[l - 1] && !(stl[l]);
    for (let i = 0; i < l; i++) {
      const s1 = st[i];
      try {
        s1.__proto__.toLowerCase = stringToLower;
      } catch (e) {
        Object.setPrototypeOf(st, stringObj);
      }
      const s2 = stl ? stl[i] : '';
      const s1l = s1.toLowerCase();
      notPolluted = notPolluted && s1l[0] === s2 && s1l[0] && !(s1l[1]);
    }
  }
  return !notPolluted;
}

function hex2bin(hex) {
  return ('00000000' + (parseInt(hex, 16)).toString(2)).substr(-8);
}

function getFilesInPath(source) {
  const lstatSync = fs.lstatSync;
  const readdirSync = fs.readdirSync;
  const join = path.join;

  function isDirectory(source) {
    return lstatSync(source).isDirectory();
  }
  function isFile(source) { return lstatSync(source).isFile(); }

  function getDirectories(source) {
    return readdirSync(source).map(function (name) { return join(source, name); }).filter(isDirectory);
  }
  function getFiles(source) {
    return readdirSync(source).map(function (name) { return join(source, name); }).filter(isFile);
  }

  function getFilesRecursively(source) {
    try {
      let dirs = getDirectories(source);
      let files = dirs
        .map(function (dir) { return getFilesRecursively(dir); })
        .reduce(function (a, b) { return a.concat(b); }, []);
      return files.concat(getFiles(source));
    } catch (e) {
      return [];
    }
  }

  if (fs.existsSync(source)) {
    return getFilesRecursively(source);
  } else {
    return [];
  }
}

function decodePiCpuinfo(lines) {

  if (_rpi_cpuinfo === null) {
    _rpi_cpuinfo = lines;
  } else if (lines === undefined) {
    lines = _rpi_cpuinfo;
  }

  // https://www.raspberrypi.org/documentation/hardware/raspberrypi/revision-codes/README.md

  const oldRevisionCodes = {
    '0002': {
      type: 'B',
      revision: '1.0',
      memory: 256,
      manufacturer: 'Egoman',
      processor: 'BCM2835'
    },
    '0003': {
      type: 'B',
      revision: '1.0',
      memory: 256,
      manufacturer: 'Egoman',
      processor: 'BCM2835'
    },
    '0004': {
      type: 'B',
      revision: '2.0',
      memory: 256,
      manufacturer: 'Sony UK',
      processor: 'BCM2835'
    },
    '0005': {
      type: 'B',
      revision: '2.0',
      memory: 256,
      manufacturer: 'Qisda',
      processor: 'BCM2835'
    },
    '0006': {
      type: 'B',
      revision: '2.0',
      memory: 256,
      manufacturer: 'Egoman',
      processor: 'BCM2835'
    },
    '0007': {
      type: 'A',
      revision: '2.0',
      memory: 256,
      manufacturer: 'Egoman',
      processor: 'BCM2835'
    },
    '0008': {
      type: 'A',
      revision: '2.0',
      memory: 256,
      manufacturer: 'Sony UK',
      processor: 'BCM2835'
    },
    '0009': {
      type: 'A',
      revision: '2.0',
      memory: 256,
      manufacturer: 'Qisda',
      processor: 'BCM2835'
    },
    '000d': {
      type: 'B',
      revision: '2.0',
      memory: 512,
      manufacturer: 'Egoman',
      processor: 'BCM2835'
    },
    '000e': {
      type: 'B',
      revision: '2.0',
      memory: 512,
      manufacturer: 'Sony UK',
      processor: 'BCM2835'
    },
    '000f': {
      type: 'B',
      revision: '2.0',
      memory: 512,
      manufacturer: 'Egoman',
      processor: 'BCM2835'
    },
    '0010': {
      type: 'B+',
      revision: '1.2',
      memory: 512,
      manufacturer: 'Sony UK',
      processor: 'BCM2835'
    },
    '0011': {
      type: 'CM1',
      revision: '1.0',
      memory: 512,
      manufacturer: 'Sony UK',
      processor: 'BCM2835'
    },
    '0012': {
      type: 'A+',
      revision: '1.1',
      memory: 256,
      manufacturer: 'Sony UK',
      processor: 'BCM2835'
    },
    '0013': {
      type: 'B+',
      revision: '1.2',
      memory: 512,
      manufacturer: 'Embest',
      processor: 'BCM2835'
    },
    '0014': {
      type: 'CM1',
      revision: '1.0',
      memory: 512,
      manufacturer: 'Embest',
      processor: 'BCM2835'
    },
    '0015': {
      type: 'A+',
      revision: '1.1',
      memory: 256,
      manufacturer: '512MB	Embest',
      processor: 'BCM2835'
    }
  };

  const processorList = [
    'BCM2835',
    'BCM2836',
    'BCM2837',
    'BCM2711',
    'BCM2712',
  ];
  const manufacturerList = [
    'Sony UK',
    'Egoman',
    'Embest',
    'Sony Japan',
    'Embest',
    'Stadium'
  ];
  const typeList = {
    '00': 'A',
    '01': 'B',
    '02': 'A+',
    '03': 'B+',
    '04': '2B',
    '05': 'Alpha (early prototype)',
    '06': 'CM1',
    '08': '3B',
    '09': 'Zero',
    '0a': 'CM3',
    '0c': 'Zero W',
    '0d': '3B+',
    '0e': '3A+',
    '0f': 'Internal use only',
    '10': 'CM3+',
    '11': '4B',
    '12': 'Zero 2 W',
    '13': '400',
    '14': 'CM4',
    '15': 'CM4S',
    '16': 'Internal use only',
    '17': '5',
    '18': 'CM5',
    '19': '500',
    '1a': 'CM5 Lite',
  };

  const revisionCode = getValue(lines, 'revision', ':', true);
  const model = getValue(lines, 'model:', ':', true);
  const serial = getValue(lines, 'serial', ':', true);

  let result = {};
  if ({}.hasOwnProperty.call(oldRevisionCodes, revisionCode)) {
    // old revision codes
    result = {
      model,
      serial,
      revisionCode,
      memory: oldRevisionCodes[revisionCode].memory,
      manufacturer: oldRevisionCodes[revisionCode].manufacturer,
      processor: oldRevisionCodes[revisionCode].processor,
      type: oldRevisionCodes[revisionCode].type,
      revision: oldRevisionCodes[revisionCode].revision,
    };

  } else {
    // new revision code
    const revision = ('00000000' + getValue(lines, 'revision', ':', true).toLowerCase()).substr(-8);
    const memSizeCode = parseInt(hex2bin(revision.substr(2, 1)).substr(5, 3), 2) || 0;
    const manufacturer = manufacturerList[parseInt(revision.substr(3, 1), 10)];
    const processor = processorList[parseInt(revision.substr(4, 1), 10)];
    const typeCode = revision.substr(5, 2);


    result = {
      model,
      serial,
      revisionCode,
      memory: 256 * Math.pow(2, memSizeCode),
      manufacturer,
      processor,
      type: {}.hasOwnProperty.call(typeList, typeCode) ? typeList[typeCode] : '',
      revision: '1.' + revision.substr(7, 1),
    };
  }
  return result;
}

function getRpiGpu(cpuinfo) {

  if (_rpi_cpuinfo === null && cpuinfo !== undefined) {
    _rpi_cpuinfo = cpuinfo;
  } else if (cpuinfo === undefined && _rpi_cpuinfo !== null) {
    cpuinfo = _rpi_cpuinfo;
  } else {
    try {
      cpuinfo = fs.readFileSync('/proc/cpuinfo', { encoding: 'utf8' }).toString().split('\n');
      _rpi_cpuinfo = cpuinfo;
    } catch (e) {
      return false;
    }
  }

  const rpi = decodePiCpuinfo(cpuinfo);
  if (rpi.type === '4B' || rpi.type === 'CM4' || rpi.type === 'CM4S' || rpi.type === '400') { return 'VideoCore VI'; }
  if (rpi.type === '5' || rpi.type === '500') { return 'VideoCore VII'; }
  return 'VideoCore IV';
}

function promiseAll(promises) {
  const resolvingPromises = promises.map(function (promise) {
    return new Promise(function (resolve) {
      let payload = new Array(2);
      promise.then(function (result) {
        payload[0] = result;
      })
        .catch(function (error) {
          payload[1] = error;
        })
        .then(function () {
          // The wrapped Promise returns an array: 0 = result, 1 = error ... we resolve all
          resolve(payload);
        });
    });
  });
  const errors = [];
  const results = [];

  // Execute all wrapped Promises
  return Promise.all(resolvingPromises)
    .then(function (items) {
      items.forEach(function (payload) {
        if (payload[1]) {
          errors.push(payload[1]);
          results.push(null);
        } else {
          errors.push(null);
          results.push(payload[0]);
        }
      });

      return {
        errors: errors,
        results: results
      };
    });
}

function promisify(nodeStyleFunction) {
  return function () {
    const args = Array.prototype.slice.call(arguments);
    return new Promise(function (resolve, reject) {
      args.push(function (err, data) {
        if (err) {
          reject(err);
        } else {
          resolve(data);
        }
      });
      nodeStyleFunction.apply(null, args);
    });
  };
}

function promisifySave(nodeStyleFunction) {
  return function () {
    const args = Array.prototype.slice.call(arguments);
    return new Promise(function (resolve) {
      args.push(function (err, data) {
        resolve(data);
      });
      nodeStyleFunction.apply(null, args);
    });
  };
}

function linuxVersion() {
  let result = '';
  if (_linux) {
    try {
      result = execSync('uname -v', execOptsLinux).toString();
    } catch (e) {
      result = '';
    }
  }
  return result;
}

function plistParser(xmlStr) {
  const tags = ['array', 'dict', 'key', 'string', 'integer', 'date', 'real', 'data', 'boolean', 'arrayEmpty'];
  const startStr = '<plist version';

  let pos = xmlStr.indexOf(startStr);
  let len = xmlStr.length;
  while (xmlStr[pos] !== '>' && pos < len) {
    pos++;
  }

  let depth = 0;
  let inTagStart = false;
  let inTagContent = false;
  let inTagEnd = false;
  let metaData = [{ tagStart: '', tagEnd: '', tagContent: '', key: '', data: null }];
  let c = '';
  let cn = xmlStr[pos];

  while (pos < len) {
    c = cn;
    if (pos + 1 < len) { cn = xmlStr[pos + 1]; }
    if (c === '<') {
      inTagContent = false;
      if (cn === '/') { inTagEnd = true; }
      else if (metaData[depth].tagStart) {
        metaData[depth].tagContent = '';
        if (!metaData[depth].data) { metaData[depth].data = metaData[depth].tagStart === 'array' ? [] : {}; }
        depth++;
        metaData.push({ tagStart: '', tagEnd: '', tagContent: '', key: null, data: null });
        inTagStart = true;
        inTagContent = false;
      }
      else if (!inTagStart) { inTagStart = true; }
    } else if (c === '>') {
      if (metaData[depth].tagStart === 'true/') { inTagStart = false; inTagEnd = true; metaData[depth].tagStart = ''; metaData[depth].tagEnd = '/boolean'; metaData[depth].data = true; }
      if (metaData[depth].tagStart === 'false/') { inTagStart = false; inTagEnd = true; metaData[depth].tagStart = ''; metaData[depth].tagEnd = '/boolean'; metaData[depth].data = false; }
      if (metaData[depth].tagStart === 'array/') { inTagStart = false; inTagEnd = true; metaData[depth].tagStart = ''; metaData[depth].tagEnd = '/arrayEmpty'; metaData[depth].data = []; }
      if (inTagContent) { inTagContent = false; }
      if (inTagStart) {
        inTagStart = false;
        inTagContent = true;
        if (metaData[depth].tagStart === 'array') {
          metaData[depth].data = [];
        }
        if (metaData[depth].tagStart === 'dict') {
          metaData[depth].data = {};
        }
      }
      if (inTagEnd) {
        inTagEnd = false;
        if (metaData[depth].tagEnd && tags.indexOf(metaData[depth].tagEnd.substr(1)) >= 0) {
          if (metaData[depth].tagEnd === '/dict' || metaData[depth].tagEnd === '/array') {
            if (depth > 1 && metaData[depth - 2].tagStart === 'array') {
              metaData[depth - 2].data.push(metaData[depth - 1].data);
            }
            if (depth > 1 && metaData[depth - 2].tagStart === 'dict') {
              metaData[depth - 2].data[metaData[depth - 1].key] = metaData[depth - 1].data;
            }
            depth--;
            metaData.pop();
            metaData[depth].tagContent = '';
            metaData[depth].tagStart = '';
            metaData[depth].tagEnd = '';
          }
          else {
            if (metaData[depth].tagEnd === '/key' && metaData[depth].tagContent) {
              metaData[depth].key = metaData[depth].tagContent;
            } else {
              if (metaData[depth].tagEnd === '/real' && metaData[depth].tagContent) { metaData[depth].data = parseFloat(metaData[depth].tagContent) || 0; }
              if (metaData[depth].tagEnd === '/integer' && metaData[depth].tagContent) { metaData[depth].data = parseInt(metaData[depth].tagContent) || 0; }
              if (metaData[depth].tagEnd === '/string' && metaData[depth].tagContent) { metaData[depth].data = metaData[depth].tagContent || ''; }
              if (metaData[depth].tagEnd === '/boolean') { metaData[depth].data = metaData[depth].tagContent || false; }
              if (metaData[depth].tagEnd === '/arrayEmpty') { metaData[depth].data = metaData[depth].tagContent || []; }
              if (depth > 0 && metaData[depth - 1].tagStart === 'array') { metaData[depth - 1].data.push(metaData[depth].data); }
              if (depth > 0 && metaData[depth - 1].tagStart === 'dict') { metaData[depth - 1].data[metaData[depth].key] = metaData[depth].data; }
            }
            metaData[depth].tagContent = '';
            metaData[depth].tagStart = '';
            metaData[depth].tagEnd = '';
          }
        }
        metaData[depth].tagEnd = '';
        inTagStart = false;
        inTagContent = false;
      }
    } else {
      if (inTagStart) { metaData[depth].tagStart += c; }
      if (inTagEnd) { metaData[depth].tagEnd += c; }
      if (inTagContent) { metaData[depth].tagContent += c; }
    }
    pos++;
  }
  return metaData[0].data;
}

function strIsNumeric(str) {
  return typeof str === 'string' && !isNaN(str) && !isNaN(parseFloat(str));
}

function plistReader(output) {
  const lines = output.split('\n');
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].indexOf(' = ') >= 0) {
      const lineParts = lines[i].split(' = ');
      lineParts[0] = lineParts[0].trim();
      if (!lineParts[0].startsWith('"')) {
        lineParts[0] = '"' + lineParts[0] + '"';
      }
      lineParts[1] = lineParts[1].trim();
      if (lineParts[1].indexOf('"') === -1 && lineParts[1].endsWith(';')) {
        const valueString = lineParts[1].substring(0, lineParts[1].length - 1);
        if (!strIsNumeric(valueString)) {
          lineParts[1] = `"${valueString}";`;
        }
      }
      if (lineParts[1].indexOf('"') >= 0 && lineParts[1].endsWith(';')) {
        const valueString = lineParts[1].substring(0, lineParts[1].length - 1).replace(/"/g, '');
        if (strIsNumeric(valueString)) {
          lineParts[1] = `${valueString};`;
        }
      }
      lines[i] = lineParts.join(' : ');
    }
    lines[i] = lines[i].replace(/\(/g, '[').replace(/\)/g, ']').replace(/;/g, ',').trim();
    if (lines[i].startsWith('}') && lines[i - 1] && lines[i - 1].endsWith(',')) {
      lines[i - 1] = lines[i - 1].substring(0, lines[i - 1].length - 1);
    }
  }
  output = lines.join('');
  let obj = {};
  try {
    obj = JSON.parse(output);
  } catch (e) {
    noop();
  }
  return obj;
}

function semverCompare(v1, v2) {
  let res = 0;
  const parts1 = v1.split('.');
  const parts2 = v2.split('.');
  if (parts1[0] < parts2[0]) { res = 1; }
  else if (parts1[0] > parts2[0]) { res = -1; }
  else if (parts1[0] === parts2[0] && parts1.length >= 2 && parts2.length >= 2) {
    if (parts1[1] < parts2[1]) { res = 1; }
    else if (parts1[1] > parts2[1]) { res = -1; }
    else if (parts1[1] === parts2[1]) {
      if (parts1.length >= 3 && parts2.length >= 3) {
        if (parts1[2] < parts2[2]) { res = 1; }
        else if (parts1[2] > parts2[2]) { res = -1; }
      } else if (parts2.length >= 3) {
        res = 1;
      }
    }
  }
  return res;
}

function getAppleModel(key) {
  const appleModelIds = [
    {
      key: 'Mac15,12',
      name: 'MacBook Air',
      size: '13-inch',
      processor: 'M3',
      year: '2024',
      additional: ''
    },
    {
      key: 'Mac14,15',
      name: 'MacBook Air',
      size: '15-inch',
      processor: 'M2',
      year: '2024',
      additional: ''
    },
    {
      key: 'Mac14,2',
      name: 'MacBook Air',
      size: '13-inch',
      processor: 'M2',
      year: '2022',
      additional: ''
    },
    {
      key: 'MacBookAir10,1',
      name: 'MacBook Air',
      size: '13-inch',
      processor: 'M1',
      year: '2020',
      additional: ''
    },
    {
      key: 'MacBookAir9,1',
      name: 'MacBook Air',
      size: '13-inch',
      processor: '',
      year: '2020',
      additional: ''
    },
    {
      key: 'MacBookAir8,2',
      name: 'MacBook Air',
      size: '13-inch',
      processor: '',
      year: '2019',
      additional: ''
    },
    {
      key: 'MacBookAir8,1',
      name: 'MacBook Air',
      size: '13-inch',
      processor: '',
      year: '2018',
      additional: ''
    },
    {
      key: 'MacBookAir7,2',
      name: 'MacBook Air',
      size: '13-inch',
      processor: '',
      year: '2017',
      additional: ''
    },
    {
      key: 'MacBookAir7,2',
      name: 'MacBook Air',
      size: '13-inch',
      processor: '',
      year: 'Early 2015',
      additional: ''
    },
    {
      key: 'MacBookAir7,1',
      name: 'MacBook Air',
      size: '11-inch',
      processor: '',
      year: 'Early 2015',
      additional: ''
    },
    {
      key: 'MacBookAir6,2',
      name: 'MacBook Air',
      size: '13-inch',
      processor: '',
      year: 'Early 2014',
      additional: ''
    },
    {
      key: 'MacBookAir6,1',
      name: 'MacBook Air',
      size: '11-inch',
      processor: '',
      year: 'Early 2014',
      additional: ''
    },
    {
      key: 'MacBookAir6,2',
      name: 'MacBook Air',
      size: '13-inch',
      processor: '',
      year: 'Mid 2013',
      additional: ''
    },
    {
      key: 'MacBookAir6,1',
      name: 'MacBook Air',
      size: '11-inch',
      processor: '',
      year: 'Mid 2013',
      additional: ''
    },
    {
      key: 'MacBookAir5,2',
      name: 'MacBook Air',
      size: '13-inch',
      processor: '',
      year: 'Mid 2012',
      additional: ''
    },
    {
      key: 'MacBookAir5,1',
      name: 'MacBook Air',
      size: '11-inch',
      processor: '',
      year: 'Mid 2012',
      additional: ''
    },
    {
      key: 'MacBookAir4,2',
      name: 'MacBook Air',
      size: '13-inch',
      processor: '',
      year: 'Mid 2011',
      additional: ''
    },
    {
      key: 'MacBookAir4,1',
      name: 'MacBook Air',
      size: '11-inch',
      processor: '',
      year: 'Mid 2011',
      additional: ''
    },
    {
      key: 'MacBookAir3,2',
      name: 'MacBook Air',
      size: '13-inch',
      processor: '',
      year: 'Late 2010',
      additional: ''
    },
    {
      key: 'MacBookAir3,1',
      name: 'MacBook Air',
      size: '11-inch',
      processor: '',
      year: 'Late 2010',
      additional: ''
    },
    {
      key: 'MacBookAir2,1',
      name: 'MacBook Air',
      size: '13-inch',
      processor: '',
      year: 'Mid 2009',
      additional: ''
    },
    {
      key: 'Mac16,1',
      name: 'MacBook Pro',
      size: '14-inch',
      processor: 'M4',
      year: '2024',
      additional: ''
    },
    {
      key: 'Mac16,6',
      name: 'MacBook Pro',
      size: '14-inch',
      processor: 'M4 Pro',
      year: '2024',
      additional: ''
    },
    {
      key: 'Mac16,8',
      name: 'MacBook Pro',
      size: '14-inch',
      processor: 'M4 Max',
      year: '2024',
      additional: ''
    },
    {
      key: 'Mac16,5',
      name: 'MacBook Pro',
      size: '16-inch',
      processor: 'M4 Pro',
      year: '2024',
      additional: ''
    },
    {
      key: 'Mac16,6',
      name: 'MacBook Pro',
      size: '16-inch',
      processor: 'M4 Max',
      year: '2024',
      additional: ''
    },
    {
      key: 'Mac15,3',
      name: 'MacBook Pro',
      size: '14-inch',
      processor: 'M3',
      year: 'Nov 2023',
      additional: ''
    },
    {
      key: 'Mac15,6',
      name: 'MacBook Pro',
      size: '14-inch',
      processor: 'M3 Pro',
      year: 'Nov 2023',
      additional: ''
    },
    {
      key: 'Mac15,8',
      name: 'MacBook Pro',
      size: '14-inch',
      processor: 'M3 Pro',
      year: 'Nov 2023',
      additional: ''
    },
    {
      key: 'Mac15,10',
      name: 'MacBook Pro',
      size: '14-inch',
      processor: 'M3 Max',
      year: 'Nov 2023',
      additional: ''
    },
    {
      key: 'Mac15,7',
      name: 'MacBook Pro',
      size: '16-inch',
      processor: 'M3 Pro',
      year: 'Nov 2023',
      additional: ''
    },
    {
      key: 'Mac15,9',
      name: 'MacBook Pro',
      size: '16-inch',
      processor: 'M3 Pro',
      year: 'Nov 2023',
      additional: ''
    },
    {
      key: 'Mac15,11',
      name: 'MacBook Pro',
      size: '16-inch',
      processor: 'M3 Max',
      year: 'Nov 2023',
      additional: ''
    },
    {
      key: 'Mac14,5',
      name: 'MacBook Pro',
      size: '14-inch',
      processor: 'M2 Max',
      year: '2023',
      additional: ''
    },
    {
      key: 'Mac14,9',
      name: 'MacBook Pro',
      size: '14-inch',
      processor: 'M2 Max',
      year: '2023',
      additional: ''
    },
    {
      key: 'Mac14,6',
      name: 'MacBook Pro',
      size: '16-inch',
      processor: 'M2 Max',
      year: '2023',
      additional: ''
    },
    {
      key: 'Mac14,10',
      name: 'MacBook Pro',
      size: '16-inch',
      processor: 'M2 Max',
      year: '2023',
      additional: ''
    },
    {
      key: 'Mac14,7',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: 'M2',
      year: '2022',
      additional: ''
    },
    {
      key: 'MacBookPro18,3',
      name: 'MacBook Pro',
      size: '14-inch',
      processor: 'M1 Pro',
      year: '2021',
      additional: ''
    },
    {
      key: 'MacBookPro18,4',
      name: 'MacBook Pro',
      size: '14-inch',
      processor: 'M1 Max',
      year: '2021',
      additional: ''
    },
    {
      key: 'MacBookPro18,1',
      name: 'MacBook Pro',
      size: '16-inch',
      processor: 'M1 Pro',
      year: '2021',
      additional: ''
    },
    {
      key: 'MacBookPro18,2',
      name: 'MacBook Pro',
      size: '16-inch',
      processor: 'M1 Max',
      year: '2021',
      additional: ''
    },
    {
      key: 'MacBookPro17,1',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: 'M1',
      year: '2020',
      additional: ''
    },
    {
      key: 'MacBookPro16,3',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: '2020',
      additional: 'Two Thunderbolt 3 ports'
    },
    {
      key: 'MacBookPro16,2',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: '2020',
      additional: 'Four Thunderbolt 3 ports'
    },
    {
      key: 'MacBookPro16,1',
      name: 'MacBook Pro',
      size: '16-inch',
      processor: '',
      year: '2019',
      additional: ''
    },
    {
      key: 'MacBookPro16,4',
      name: 'MacBook Pro',
      size: '16-inch',
      processor: '',
      year: '2019',
      additional: ''
    },
    {
      key: 'MacBookPro15,3',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: '2019',
      additional: ''
    },
    {
      key: 'MacBookPro15,2',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: '2019',
      additional: ''
    },
    {
      key: 'MacBookPro15,1',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: '2019',
      additional: ''
    },
    {
      key: 'MacBookPro15,4',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: '2019',
      additional: 'Two Thunderbolt 3 ports'
    },
    {
      key: 'MacBookPro15,1',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: '2018',
      additional: ''
    },
    {
      key: 'MacBookPro15,2',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: '2018',
      additional: 'Four Thunderbolt 3 ports'
    },
    {
      key: 'MacBookPro14,1',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: '2017',
      additional: 'Two Thunderbolt 3 ports'
    },
    {
      key: 'MacBookPro14,2',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: '2017',
      additional: 'Four Thunderbolt 3 ports'
    },
    {
      key: 'MacBookPro14,3',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: '2017',
      additional: ''
    },
    {
      key: 'MacBookPro13,1',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: '2016',
      additional: 'Two Thunderbolt 3 ports'
    },
    {
      key: 'MacBookPro13,2',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: '2016',
      additional: 'Four Thunderbolt 3 ports'
    },
    {
      key: 'MacBookPro13,3',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: '2016',
      additional: ''
    },
    {
      key: 'MacBookPro11,4',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: 'Mid 2015',
      additional: ''
    },
    {
      key: 'MacBookPro11,5',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: 'Mid 2015',
      additional: ''
    },
    {
      key: 'MacBookPro12,1',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: 'Early 2015',
      additional: ''
    },
    {
      key: 'MacBookPro11,2',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: 'Late 2013',
      additional: ''
    },
    {
      key: 'MacBookPro11,3',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: 'Late 2013',
      additional: ''
    },
    {
      key: 'MacBookPro11,1',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: 'Late 2013',
      additional: ''
    },
    {
      key: 'MacBookPro10,1',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: 'Mid 2012',
      additional: ''
    },
    {
      key: 'MacBookPro10,2',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: 'Late 2012',
      additional: ''
    },
    {
      key: 'MacBookPro9,1',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: 'Mid 2012',
      additional: ''
    },
    {
      key: 'MacBookPro9,2',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: 'Mid 2012',
      additional: ''
    },
    {
      key: 'MacBookPro8,3',
      name: 'MacBook Pro',
      size: '17-inch',
      processor: '',
      year: 'Early 2011',
      additional: ''
    },
    {
      key: 'MacBookPro8,2',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: 'Early 2011',
      additional: ''
    },
    {
      key: 'MacBookPro8,1',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: 'Early 2011',
      additional: ''
    },
    {
      key: 'MacBookPro6,1',
      name: 'MacBook Pro',
      size: '17-inch',
      processor: '',
      year: 'Mid 2010',
      additional: ''
    },
    {
      key: 'MacBookPro6,2',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: 'Mid 2010',
      additional: ''
    },
    {
      key: 'MacBookPro7,1',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: 'Mid 2010',
      additional: ''
    },
    {
      key: 'MacBookPro5,2',
      name: 'MacBook Pro',
      size: '17-inch',
      processor: '',
      year: 'Early 2009',
      additional: ''
    },
    {
      key: 'MacBookPro5,3',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: 'Mid 2009',
      additional: ''
    },
    {
      key: 'MacBookPro5,5',
      name: 'MacBook Pro',
      size: '13-inch',
      processor: '',
      year: 'Mid 2009',
      additional: ''
    },
    {
      key: 'MacBookPro5,1',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: 'Late 2008',
      additional: ''
    },
    {
      key: 'MacBookPro4,1',
      name: 'MacBook Pro',
      size: '15-inch',
      processor: '',
      year: 'Early 2008',
      additional: ''
    },
    {
      key: 'MacBook10,1',
      name: 'MacBook',
      size: '12-inch',
      processor: '',
      year: '2017',
      additional: ''
    },
    {
      key: 'MacBook9,1',
      name: 'MacBook',
      size: '12-inch',
      processor: '',
      year: 'Early 2016',
      additional: ''
    },
    {
      key: 'MacBook8,1',
      name: 'MacBook',
      size: '12-inch',
      processor: '',
      year: 'Early 2015',
      additional: ''
    },
    {
      key: 'MacBook7,1',
      name: 'MacBook',
      size: '13-inch',
      processor: '',
      year: 'Mid 2010',
      additional: ''
    },
    {
      key: 'MacBook6,1',
      name: 'MacBook',
      size: '13-inch',
      processor: '',
      year: 'Late 2009',
      additional: ''
    },
    {
      key: 'MacBook5,2',
      name: 'MacBook',
      size: '13-inch',
      processor: '',
      year: 'Early 2009',
      additional: ''
    },
    {
      key: 'Mac14,13',
      name: 'Mac Studio',
      size: '',
      processor: '',
      year: '2023',
      additional: ''
    },
    {
      key: 'Mac14,14',
      name: 'Mac Studio',
      size: '',
      processor: '',
      year: '2023',
      additional: ''
    },
    {
      key: 'Mac13,1',
      name: 'Mac Studio',
      size: '',
      processor: '',
      year: '2022',
      additional: ''
    },
    {
      key: 'Mac13,2',
      name: 'Mac Studio',
      size: '',
      processor: '',
      year: '2022',
      additional: ''
    },
    {
      key: 'Mac16,11',
      name: 'Mac mini',
      size: '',
      processor: 'M4 Pro',
      year: '2024',
      additional: ''
    },
    {
      key: 'Mac16,10',
      name: 'Mac mini',
      size: '',
      processor: 'M4',
      year: '2024',
      additional: ''
    },
    {
      key: 'Mac14,3',
      name: 'Mac mini',
      size: '',
      processor: 'M2',
      year: '2023',
      additional: ''
    },
    {
      key: 'Mac14,12',
      name: 'Mac mini',
      size: '',
      processor: 'M2 Pro',
      year: '2023',
      additional: ''
    },
    {
      key: 'Macmini9,1',
      name: 'Mac mini',
      size: '',
      processor: 'M1',
      year: '2020',
      additional: ''
    },
    {
      key: 'Macmini8,1',
      name: 'Mac mini',
      size: '',
      processor: '',
      year: 'Late 2018',
      additional: ''
    },
    {
      key: 'Macmini7,1',
      name: 'Mac mini',
      size: '',
      processor: '',
      year: 'Late 2014',
      additional: ''
    },
    {
      key: 'Macmini6,1',
      name: 'Mac mini',
      size: '',
      processor: '',
      year: 'Late 2012',
      additional: ''
    },
    {
      key: 'Macmini6,2',
      name: 'Mac mini',
      size: '',
      processor: '',
      year: 'Late 2012',
      additional: ''
    },
    {
      key: 'Macmini5,1',
      name: 'Mac mini',
      size: '',
      processor: '',
      year: 'Mid 2011',
      additional: ''
    },
    {
      key: 'Macmini5,2',
      name: 'Mac mini',
      size: '',
      processor: '',
      year: 'Mid 2011',
      additional: ''
    },
    {
      key: 'Macmini4,1',
      name: 'Mac mini',
      size: '',
      processor: '',
      year: 'Mid 2010',
      additional: ''
    },
    {
      key: 'Macmini3,1',
      name: 'Mac mini',
      size: '',
      processor: '',
      year: 'Early 2009',
      additional: ''
    },
    {
      key: 'Mac16,3',
      name: 'iMac',
      size: '24-inch',
      processor: 'M4',
      year: '2024',
      additional: 'Four ports'
    },
    {
      key: 'Mac16,2',
      name: 'iMac',
      size: '24-inch',
      processor: 'M4',
      year: '2024',
      additional: 'Two ports'
    },
    {
      key: 'Mac15,5',
      name: 'iMac',
      size: '24-inch',
      processor: 'M3',
      year: '2023',
      additional: 'Four ports'
    },
    {
      key: 'Mac15,4',
      name: 'iMac',
      size: '24-inch',
      processor: 'M3',
      year: '2023',
      additional: 'Two ports'
    },
    {
      key: 'iMac21,1',
      name: 'iMac',
      size: '24-inch',
      processor: 'M1',
      year: '2021',
      additional: ''
    },
    {
      key: 'iMac21,2',
      name: 'iMac',
      size: '24-inch',
      processor: 'M1',
      year: '2021',
      additional: ''
    },
    {
      key: 'iMac20,1',
      name: 'iMac',
      size: '27-inch',
      processor: '',
      year: '2020',
      additional: 'Retina 5K'
    },
    {
      key: 'iMac20,2',
      name: 'iMac',
      size: '27-inch',
      processor: '',
      year: '2020',
      additional: 'Retina 5K'
    },
    {
      key: 'iMac19,1',
      name: 'iMac',
      size: '27-inch',
      processor: '',
      year: '2019',
      additional: 'Retina 5K'
    },
    {
      key: 'iMac19,2',
      name: 'iMac',
      size: '21.5-inch',
      processor: '',
      year: '2019',
      additional: 'Retina 4K'
    },
    {
      key: 'iMacPro1,1',
      name: 'iMac Pro',
      size: '',
      processor: '',
      year: '2017',
      additional: ''
    },
    {
      key: 'iMac18,3',
      name: 'iMac',
      size: '27-inch',
      processor: '',
      year: '2017',
      additional: 'Retina 5K'
    },
    {
      key: 'iMac18,2',
      name: 'iMac',
      size: '21.5-inch',
      processor: '',
      year: '2017',
      additional: 'Retina 4K'
    },
    {
      key: 'iMac18,1',
      name: 'iMac',
      size: '21.5-inch',
      processor: '',
      year: '2017',
      additional: ''
    },
    {
      key: 'iMac17,1',
      name: 'iMac',
      size: '27-inch',
      processor: '',
      year: 'Late 2015',
      additional: 'Retina 5K'
    },
    {
      key: 'iMac16,2',
      name: 'iMac',
      size: '21.5-inch',
      processor: '',
      year: 'Late 2015',
      additional: 'Retina 4K'
    },
    {
      key: 'iMac16,1',
      name: 'iMac',
      size: '21.5-inch',
      processor: '',
      year: 'Late 2015',
      additional: ''
    },
    {
      key: 'iMac15,1',
      name: 'iMac',
      size: '27-inch',
      processor: '',
      year: 'Late 2014',
      additional: 'Retina 5K'
    },
    {
      key: 'iMac14,4',
      name: 'iMac',
      size: '21.5-inch',
      processor: '',
      year: 'Mid 2014',
      additional: ''
    },
    {
      key: 'iMac14,2',
      name: 'iMac',
      size: '27-inch',
      processor: '',
      year: 'Late 2013',
      additional: ''
    },
    {
      key: 'iMac14,1',
      name: 'iMac',
      size: '21.5-inch',
      processor: '',
      year: 'Late 2013',
      additional: ''
    },
    {
      key: 'iMac13,2',
      name: 'iMac',
      size: '27-inch',
      processor: '',
      year: 'Late 2012',
      additional: ''
    },
    {
      key: 'iMac13,1',
      name: 'iMac',
      size: '21.5-inch',
      processor: '',
      year: 'Late 2012',
      additional: ''
    },
    {
      key: 'iMac12,2',
      name: 'iMac',
      size: '27-inch',
      processor: '',
      year: 'Mid 2011',
      additional: ''
    },
    {
      key: 'iMac12,1',
      name: 'iMac',
      size: '21.5-inch',
      processor: '',
      year: 'Mid 2011',
      additional: ''
    },
    {
      key: 'iMac11,3',
      name: 'iMac',
      size: '27-inch',
      processor: '',
      year: 'Mid 2010',
      additional: ''
    },
    {
      key: 'iMac11,2',
      name: 'iMac',
      size: '21.5-inch',
      processor: '',
      year: 'Mid 2010',
      additional: ''
    },
    {
      key: 'iMac10,1',
      name: 'iMac',
      size: '21.5-inch',
      processor: '',
      year: 'Late 2009',
      additional: ''
    },
    {
      key: 'iMac9,1',
      name: 'iMac',
      size: '20-inch',
      processor: '',
      year: 'Early 2009',
      additional: ''
    },
    {
      key: 'Mac14,8',
      name: 'Mac Pro',
      size: '',
      processor: '',
      year: '2023',
      additional: ''
    },
    {
      key: 'Mac14,8',
      name: 'Mac Pro',
      size: '',
      processor: '',
      year: '2023',
      additional: 'Rack'
    },
    {
      key: 'MacPro7,1',
      name: 'Mac Pro',
      size: '',
      processor: '',
      year: '2019',
      additional: ''
    },
    {
      key: 'MacPro7,1',
      name: 'Mac Pro',
      size: '',
      processor: '',
      year: '2019',
      additional: 'Rack'
    },
    {
      key: 'MacPro6,1',
      name: 'Mac Pro',
      size: '',
      processor: '',
      year: 'Late 2013',
      additional: ''
    },
    {
      key: 'MacPro5,1',
      name: 'Mac Pro',
      size: '',
      processor: '',
      year: 'Mid 2012',
      additional: ''
    },
    {
      key: 'MacPro5,1',
      name: 'Mac Pro Server',
      size: '',
      processor: '',
      year: 'Mid 2012',
      additional: 'Server'
    },
    {
      key: 'MacPro5,1',
      name: 'Mac Pro',
      size: '',
      processor: '',
      year: 'Mid 2010',
      additional: ''
    },
    {
      key: 'MacPro5,1',
      name: 'Mac Pro Server',
      size: '',
      processor: '',
      year: 'Mid 2010',
      additional: 'Server'
    },
    {
      key: 'MacPro4,1',
      name: 'Mac Pro',
      size: '',
      processor: '',
      year: 'Early 2009',
      additional: ''
    }
  ];

  const list = appleModelIds.filter((model) => model.key === key);
  if (list.length === 0) {
    return {
      key: key,
      model: 'Apple',
      version: 'Unknown'
    };
  }
  const features = [];
  if (list[0].size) { features.push(list[0].size); }
  if (list[0].processor) { features.push(list[0].processor); }
  if (list[0].year) { features.push(list[0].year); }
  if (list[0].additional) { features.push(list[0].additional); }
  return {
    key: key,
    model: list[0].name,
    version: list[0].name + ' (' + features.join(', ') + ')'
  };
}

function checkWebsite(url, timeout = 5000) {
  const http = ((url.startsWith('https:') || url.indexOf(':443/') > 0 || url.indexOf(':8443/') > 0) ? require('https') : require('http'));
  const t = Date.now();
  return new Promise((resolve) => {
    const request = http
      .get(url, function (res) {
        res.on('data', () => { });
        res.on('end', () => {
          resolve({
            url,
            statusCode: res.statusCode,
            message: res.statusMessage,
            time: Date.now() - t
          });
        });
      })
      .on("error", function (e) {
        resolve({
          url,
          statusCode: 404,
          message: e.message,
          time: Date.now() - t
        });
      })
      .setTimeout(timeout, () => {
        request.destroy();
        resolve({
          url,
          statusCode: 408,
          message: 'Request Timeout',
          time: Date.now() - t
        });
      });
  });
};

function cleanString(str) {
  return str.replace(/To Be Filled By O.E.M./g, '');
}
function noop() { }

exports.toInt = toInt;
exports.splitByNumber = splitByNumber;
exports.execOptsWin = execOptsWin;
exports.execOptsLinux = execOptsLinux;
exports.getCodepage = getCodepage;
exports.execWin = execWin;
exports.isFunction = isFunction;
exports.unique = unique;
exports.sortByKey = sortByKey;
exports.cores = cores;
exports.getValue = getValue;
exports.decodeEscapeSequence = decodeEscapeSequence;
exports.parseDateTime = parseDateTime;
exports.parseHead = parseHead;
exports.findObjectByKey = findObjectByKey;
exports.getWmic = getWmic;
exports.wmic = wmic;
exports.darwinXcodeExists = darwinXcodeExists;
exports.getVboxmanage = getVboxmanage;
exports.powerShell = powerShell;
exports.powerShellStart = powerShellStart;
exports.powerShellRelease = powerShellRelease;
exports.execSafe = execSafe;
exports.nanoSeconds = nanoSeconds;
exports.countUniqueLines = countUniqueLines;
exports.countLines = countLines;
exports.noop = noop;
exports.isRaspberry = isRaspberry;
exports.isRaspbian = isRaspbian;
exports.sanitizeShellString = sanitizeShellString;
exports.isPrototypePolluted = isPrototypePolluted;
exports.decodePiCpuinfo = decodePiCpuinfo;
exports.getRpiGpu = getRpiGpu;
exports.promiseAll = promiseAll;
exports.promisify = promisify;
exports.promisifySave = promisifySave;
exports.smartMonToolsInstalled = smartMonToolsInstalled;
exports.linuxVersion = linuxVersion;
exports.plistParser = plistParser;
exports.plistReader = plistReader;
exports.stringObj = stringObj;
exports.stringReplace = stringReplace;
exports.stringToLower = stringToLower;
exports.stringToString = stringToString;
exports.stringSubstr = stringSubstr;
exports.stringSubstring = stringSubstring;
exports.stringTrim = stringTrim;
exports.stringStartWith = stringStartWith;
exports.mathMin = mathMin;
exports.WINDIR = WINDIR;
exports.getFilesInPath = getFilesInPath;
exports.semverCompare = semverCompare;
exports.getAppleModel = getAppleModel;
exports.checkWebsite = checkWebsite;
exports.cleanString = cleanString;
exports.getPowershell = getPowershell;
