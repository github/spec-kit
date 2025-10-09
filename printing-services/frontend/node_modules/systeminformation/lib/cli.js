#!/usr/bin/env node

'use strict';
// @ts-check
// ==================================================================================
// cli.js
// ----------------------------------------------------------------------------------
// Description:   System Information - library
//                for Node.js
// Copyright:     (c) 2014 - 2025
// Author:        Sebastian Hildebrandt
// ----------------------------------------------------------------------------------
// License:       MIT
// ==================================================================================

// ----------------------------------------------------------------------------------
// Dependencies
// ----------------------------------------------------------------------------------
const si = require('./index');
const lib_version = require('../package.json').version;

function capFirst(string) {
  return string[0].toUpperCase() + string.slice(1);
}

function printLines(obj) {
  for (const property in obj) {
    console.log(capFirst(property) + '                    '.substring(0, 17 - property.length) + ': ' + (obj[property] || ''));
  }
  console.log();
}

function info() {
  console.log('┌─────────────────────────────────────────────────────────────────────────────────────────┐');
  console.log('│  SYSTEMINFORMATION                                                                                                  '.substring(0, 80 - lib_version.length) + 'Version: ' + lib_version + ' │');
  console.log('└─────────────────────────────────────────────────────────────────────────────────────────┘');

  si.osInfo().then(res => {
    console.log();
    console.log('Operating System:');
    console.log('──────────────────────────────────────────────────────────────────────────────────────────');
    delete res.serial;
    delete res.servicepack;
    delete res.logofile;
    delete res.fqdn;
    delete res.uefi;
    printLines(res);
    si.system().then(res => {
      console.log('System:');
      console.log('──────────────────────────────────────────────────────────────────────────────────────────');
      delete res.serial;
      delete res.uuid;
      delete res.sku;
      delete res.uuid;
      printLines(res);
      si.cpu().then(res => {
        console.log('CPU:');
        console.log('──────────────────────────────────────────────────────────────────────────────────────────');
        delete res.cache;
        delete res.governor;
        delete res.flags;
        delete res.virtualization;
        delete res.revision;
        delete res.voltage;
        delete res.vendor;
        delete res.speedMin;
        delete res.speedMax;
        printLines(res);
      });
    });
  });
}

// ----------------------------------------------------------------------------------
// Main
// ----------------------------------------------------------------------------------
(function () {
  const args = process.argv.slice(2);

  if (args[0] === 'info') {
    info();
  } else {
    si.getStaticData().then(
      ((data) => {
        data.time = si.time();
        console.log(JSON.stringify(data, null, 2));
      }
      ));
  }

})();
