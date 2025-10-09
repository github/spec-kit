'use strict';
// @ts-check
// ==================================================================================
// audio.js
// ----------------------------------------------------------------------------------
// Description:   System Information - library
//                for Node.js
// Copyright:     (c) 2014 - 2025
// Author:        Sebastian Hildebrandt
// ----------------------------------------------------------------------------------
// License:       MIT
// ==================================================================================
// 17. bluetooth
// ----------------------------------------------------------------------------------

const exec = require('child_process').exec;
const execSync = require('child_process').execSync;
const path = require('path');
const util = require('./util');
const bluetoothVendors = require('./bluetoothVendors');
const fs = require('fs');

let _platform = process.platform;

const _linux = (_platform === 'linux' || _platform === 'android');
const _darwin = (_platform === 'darwin');
const _windows = (_platform === 'win32');
const _freebsd = (_platform === 'freebsd');
const _openbsd = (_platform === 'openbsd');
const _netbsd = (_platform === 'netbsd');
const _sunos = (_platform === 'sunos');

function parseBluetoothType(str) {
  let result = '';

  if (str.indexOf('keyboard') >= 0) { result = 'Keyboard'; }
  if (str.indexOf('mouse') >= 0) { result = 'Mouse'; }
  if (str.indexOf('trackpad') >= 0) { result = 'Trackpad'; }
  if (str.indexOf('speaker') >= 0) { result = 'Speaker'; }
  if (str.indexOf('headset') >= 0) { result = 'Headset'; }
  if (str.indexOf('phone') >= 0) { result = 'Phone'; }
  if (str.indexOf('macbook') >= 0) { result = 'Computer'; }
  if (str.indexOf('imac') >= 0) { result = 'Computer'; }
  if (str.indexOf('ipad') >= 0) { result = 'Tablet'; }
  if (str.indexOf('watch') >= 0) { result = 'Watch'; }
  if (str.indexOf('headphone') >= 0) { result = 'Headset'; }
  // to be continued ...

  return result;
}

function parseBluetoothManufacturer(str) {
  let result = str.split(' ')[0];
  str = str.toLowerCase();
  if (str.indexOf('apple') >= 0) { result = 'Apple'; }
  if (str.indexOf('ipad') >= 0) { result = 'Apple'; }
  if (str.indexOf('imac') >= 0) { result = 'Apple'; }
  if (str.indexOf('iphone') >= 0) { result = 'Apple'; }
  if (str.indexOf('magic mouse') >= 0) { result = 'Apple'; }
  if (str.indexOf('magic track') >= 0) { result = 'Apple'; }
  if (str.indexOf('macbook') >= 0) { result = 'Apple'; }
  // to be continued ...

  return result;
}

function parseBluetoothVendor(str) {
  const id = parseInt(str);
  if (!isNaN(id)) return bluetoothVendors[id];
}

function parseLinuxBluetoothInfo(lines, macAddr1, macAddr2) {
  const result = {};

  result.device = null;
  result.name = util.getValue(lines, 'name', '=');
  result.manufacturer = null;
  result.macDevice = macAddr1;
  result.macHost = macAddr2;
  result.batteryPercent = null;
  result.type = parseBluetoothType(result.name.toLowerCase());
  result.connected = false;

  return result;
}

function parseDarwinBluetoothDevices(bluetoothObject, macAddr2) {
  const result = {};
  const typeStr = ((bluetoothObject.device_minorClassOfDevice_string || bluetoothObject.device_majorClassOfDevice_string || bluetoothObject.device_minorType || '') + (bluetoothObject.device_name || '')).toLowerCase();

  result.device = bluetoothObject.device_services || '';
  result.name = bluetoothObject.device_name || '';
  result.manufacturer = bluetoothObject.device_manufacturer || parseBluetoothVendor(bluetoothObject.device_vendorID) || parseBluetoothManufacturer(bluetoothObject.device_name || '') || '';
  result.macDevice = (bluetoothObject.device_addr || bluetoothObject.device_address || '').toLowerCase().replace(/-/g, ':');
  result.macHost = macAddr2;
  result.batteryPercent = bluetoothObject.device_batteryPercent || null;
  result.type = parseBluetoothType(typeStr);
  result.connected = bluetoothObject.device_isconnected === 'attrib_Yes' || false;

  return result;
}

function parseWindowsBluetooth(lines) {
  const result = {};

  result.device = null;
  result.name = util.getValue(lines, 'name', ':');
  result.manufacturer = util.getValue(lines, 'manufacturer', ':');
  result.macDevice = null;
  result.macHost = null;
  result.batteryPercent = null;
  result.type = parseBluetoothType(result.name.toLowerCase());
  result.connected = null;

  return result;
}

function bluetoothDevices(callback) {

  return new Promise((resolve) => {
    process.nextTick(() => {
      let result = [];
      if (_linux) {
        // get files in /var/lib/bluetooth/ recursive
        const btFiles = util.getFilesInPath('/var/lib/bluetooth/');
        btFiles.forEach((element) => {
          const filename = path.basename(element);
          const pathParts = element.split('/');
          const macAddr1 = pathParts.length >= 6 ? pathParts[pathParts.length - 2] : null;
          const macAddr2 = pathParts.length >= 7 ? pathParts[pathParts.length - 3] : null;
          if (filename === 'info') {
            const infoFile = fs.readFileSync(element, { encoding: 'utf8' }).split('\n');
            result.push(parseLinuxBluetoothInfo(infoFile, macAddr1, macAddr2));
          }
        });
        // determine "connected" with hcitool con
        try {
          const hdicon = execSync('hcitool con', util.execOptsLinux).toString().toLowerCase();
          for (let i = 0; i < result.length; i++) {
            if (result[i].macDevice && result[i].macDevice.length > 10 && hdicon.indexOf(result[i].macDevice.toLowerCase()) >= 0) {
              result[i].connected = true;
            }
          }
        } catch (e) {
          util.noop();
        }

        if (callback) {
          callback(result);
        }
        resolve(result);
      }
      if (_darwin) {
        let cmd = 'system_profiler SPBluetoothDataType -json';
        exec(cmd, function (error, stdout) {
          if (!error) {
            try {
              const outObj = JSON.parse(stdout.toString());
              if (outObj.SPBluetoothDataType && outObj.SPBluetoothDataType.length && outObj.SPBluetoothDataType[0] && outObj.SPBluetoothDataType[0]['device_title'] && outObj.SPBluetoothDataType[0]['device_title'].length) {
                // missing: host BT Adapter macAddr ()
                let macAddr2 = null;
                if (outObj.SPBluetoothDataType[0]['local_device_title'] && outObj.SPBluetoothDataType[0].local_device_title.general_address) {
                  macAddr2 = outObj.SPBluetoothDataType[0].local_device_title.general_address.toLowerCase().replace(/-/g, ':');
                }
                outObj.SPBluetoothDataType[0]['device_title'].forEach((element) => {
                  const obj = element;
                  const objKey = Object.keys(obj);
                  if (objKey && objKey.length === 1) {
                    const innerObject = obj[objKey[0]];
                    innerObject.device_name = objKey[0];
                    const bluetoothDevice = parseDarwinBluetoothDevices(innerObject, macAddr2);
                    result.push(bluetoothDevice);
                  }
                });
              }
              if (outObj.SPBluetoothDataType && outObj.SPBluetoothDataType.length && outObj.SPBluetoothDataType[0] && outObj.SPBluetoothDataType[0]['device_connected'] && outObj.SPBluetoothDataType[0]['device_connected'].length) {
                const macAddr2 = outObj.SPBluetoothDataType[0].controller_properties && outObj.SPBluetoothDataType[0].controller_properties.controller_address ? outObj.SPBluetoothDataType[0].controller_properties.controller_address.toLowerCase().replace(/-/g, ':') : null;
                outObj.SPBluetoothDataType[0]['device_connected'].forEach((element) => {
                  const obj = element;
                  const objKey = Object.keys(obj);
                  if (objKey && objKey.length === 1) {
                    const innerObject = obj[objKey[0]];
                    innerObject.device_name = objKey[0];
                    innerObject.device_isconnected = 'attrib_Yes';
                    const bluetoothDevice = parseDarwinBluetoothDevices(innerObject, macAddr2);
                    result.push(bluetoothDevice);
                  }
                });
              }
              if (outObj.SPBluetoothDataType && outObj.SPBluetoothDataType.length && outObj.SPBluetoothDataType[0] && outObj.SPBluetoothDataType[0]['device_not_connected'] && outObj.SPBluetoothDataType[0]['device_not_connected'].length) {
                const macAddr2 = outObj.SPBluetoothDataType[0].controller_properties && outObj.SPBluetoothDataType[0].controller_properties.controller_address ? outObj.SPBluetoothDataType[0].controller_properties.controller_address.toLowerCase().replace(/-/g, ':') : null;
                outObj.SPBluetoothDataType[0]['device_not_connected'].forEach((element) => {
                  const obj = element;
                  const objKey = Object.keys(obj);
                  if (objKey && objKey.length === 1) {
                    const innerObject = obj[objKey[0]];
                    innerObject.device_name = objKey[0];
                    innerObject.device_isconnected = 'attrib_No';
                    const bluetoothDevice = parseDarwinBluetoothDevices(innerObject, macAddr2);
                    result.push(bluetoothDevice);
                  }
                });
              }
            } catch (e) {
              util.noop();
            }
          }
          if (callback) {
            callback(result);
          }
          resolve(result);
        });
      }
      if (_windows) {
        util.powerShell('Get-CimInstance Win32_PNPEntity | select PNPClass, Name, Manufacturer | fl').then((stdout, error) => {
          if (!error) {
            const parts = stdout.toString().split(/\n\s*\n/);
            parts.forEach((part) => {
              if (util.getValue(part.split('\n'), 'PNPClass', ':') === 'Bluetooth') {
                result.push(parseWindowsBluetooth(part.split('\n')));
              }
            });
          }
          if (callback) {
            callback(result);
          }
          resolve(result);
        });
      }
      if (_freebsd || _netbsd || _openbsd || _sunos) {
        resolve(null);
      }
    });
  });
}

exports.bluetoothDevices = bluetoothDevices;
