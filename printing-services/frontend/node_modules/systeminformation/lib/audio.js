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
// 16. audio
// ----------------------------------------------------------------------------------

const exec = require('child_process').exec;
const execSync = require('child_process').execSync;
const util = require('./util');

let _platform = process.platform;

const _linux = (_platform === 'linux' || _platform === 'android');
const _darwin = (_platform === 'darwin');
const _windows = (_platform === 'win32');
const _freebsd = (_platform === 'freebsd');
const _openbsd = (_platform === 'openbsd');
const _netbsd = (_platform === 'netbsd');
const _sunos = (_platform === 'sunos');

function parseAudioType(str, input, output) {
  str = str.toLowerCase();
  let result = '';

  if (str.indexOf('input') >= 0) { result = 'Microphone'; }
  if (str.indexOf('display audio') >= 0) { result = 'Speaker'; }
  if (str.indexOf('speak') >= 0) { result = 'Speaker'; }
  if (str.indexOf('laut') >= 0) { result = 'Speaker'; }
  if (str.indexOf('loud') >= 0) { result = 'Speaker'; }
  if (str.indexOf('head') >= 0) { result = 'Headset'; }
  if (str.indexOf('mic') >= 0) { result = 'Microphone'; }
  if (str.indexOf('mikr') >= 0) { result = 'Microphone'; }
  if (str.indexOf('phone') >= 0) { result = 'Phone'; }
  if (str.indexOf('controll') >= 0) { result = 'Controller'; }
  if (str.indexOf('line o') >= 0) { result = 'Line Out'; }
  if (str.indexOf('digital o') >= 0) { result = 'Digital Out'; }
  if (str.indexOf('smart sound technology') >= 0) { result = 'Digital Signal Processor'; }
  if (str.indexOf('high definition audio') >= 0) { result = 'Sound Driver'; }

  if (!result && output) {
    result = 'Speaker';
  } else if (!result && input) {
    result = 'Microphone';
  }
  return result;
}


function getLinuxAudioPci() {
  let cmd = 'lspci -v 2>/dev/null';
  let result = [];
  try {
    const parts = execSync(cmd, util.execOptsLinux).toString().split('\n\n');
    parts.forEach(element => {
      const lines = element.split('\n');
      if (lines && lines.length && lines[0].toLowerCase().indexOf('audio') >= 0) {
        const audio = {};
        audio.slotId = lines[0].split(' ')[0];
        audio.driver = util.getValue(lines, 'Kernel driver in use', ':', true) || util.getValue(lines, 'Kernel modules', ':', true);
        result.push(audio);
      }
    });
    return result;
  } catch (e) {
    return result;
  }
}

function parseLinuxAudioPciMM(lines, audioPCI) {
  const result = {};
  const slotId = util.getValue(lines, 'Slot');

  const pciMatch = audioPCI.filter(function (item) { return item.slotId === slotId; });

  result.id = slotId;
  result.name = util.getValue(lines, 'SDevice');
  result.manufacturer = util.getValue(lines, 'SVendor');
  result.revision = util.getValue(lines, 'Rev');
  result.driver = pciMatch && pciMatch.length === 1 && pciMatch[0].driver ? pciMatch[0].driver : '';
  result.default = null;
  result.channel = 'PCIe';
  result.type = parseAudioType(result.name, null, null);
  result.in = null;
  result.out = null;
  result.status = 'online';

  return result;
}

function parseDarwinChannel(str) {
  let result = '';

  if (str.indexOf('builtin') >= 0) { result = 'Built-In'; }
  if (str.indexOf('extern') >= 0) { result = 'Audio-Jack'; }
  if (str.indexOf('hdmi') >= 0) { result = 'HDMI'; }
  if (str.indexOf('displayport') >= 0) { result = 'Display-Port'; }
  if (str.indexOf('usb') >= 0) { result = 'USB'; }
  if (str.indexOf('pci') >= 0) { result = 'PCIe'; }

  return result;
}

function parseDarwinAudio(audioObject, id) {
  const result = {};
  const channelStr = ((audioObject.coreaudio_device_transport || '') + ' ' + (audioObject._name || '')).toLowerCase();

  result.id = id;
  result.name = audioObject._name;
  result.manufacturer = audioObject.coreaudio_device_manufacturer;
  result.revision = null;
  result.driver = null;
  result.default = !!(audioObject.coreaudio_default_audio_input_device || '') || !!(audioObject.coreaudio_default_audio_output_device || '');
  result.channel = parseDarwinChannel(channelStr);
  result.type = parseAudioType(result.name, !!(audioObject.coreaudio_device_input || ''), !!(audioObject.coreaudio_device_output || ''));
  result.in = !!(audioObject.coreaudio_device_input || '');
  result.out = !!(audioObject.coreaudio_device_output || '');
  result.status = 'online';

  return result;
}

function parseWindowsAudio(lines) {
  const result = {};
  const status = util.getValue(lines, 'StatusInfo', ':');

  result.id = util.getValue(lines, 'DeviceID', ':'); // PNPDeviceID??
  result.name = util.getValue(lines, 'name', ':');
  result.manufacturer = util.getValue(lines, 'manufacturer', ':');
  result.revision = null;
  result.driver = null;
  result.default = null;
  result.channel = null;
  result.type = parseAudioType(result.name, null, null);
  result.in = null;
  result.out = null;
  result.status = status;

  return result;
}

function audio(callback) {

  return new Promise((resolve) => {
    process.nextTick(() => {
      let result = [];
      if (_linux || _freebsd || _openbsd || _netbsd) {
        let cmd = 'lspci -vmm 2>/dev/null';
        exec(cmd, function (error, stdout) {
          // PCI
          if (!error) {
            const audioPCI = getLinuxAudioPci();
            const parts = stdout.toString().split('\n\n');
            parts.forEach(element => {
              const lines = element.split('\n');
              if (util.getValue(lines, 'class', ':', true).toLowerCase().indexOf('audio') >= 0) {
                const audio = parseLinuxAudioPciMM(lines, audioPCI);
                result.push(audio);
              }
            });
          }
          if (callback) {
            callback(result);
          }
          resolve(result);
        });
      }
      if (_darwin) {
        let cmd = 'system_profiler SPAudioDataType -json';
        exec(cmd, function (error, stdout) {
          if (!error) {
            try {
              const outObj = JSON.parse(stdout.toString());
              if (outObj.SPAudioDataType && outObj.SPAudioDataType.length && outObj.SPAudioDataType[0] && outObj.SPAudioDataType[0]['_items'] && outObj.SPAudioDataType[0]['_items'].length) {
                for (let i = 0; i < outObj.SPAudioDataType[0]['_items'].length; i++) {
                  const audio = parseDarwinAudio(outObj.SPAudioDataType[0]['_items'][i], i);
                  result.push(audio);
                }
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
        util.powerShell('Get-CimInstance Win32_SoundDevice | select DeviceID,StatusInfo,Name,Manufacturer | fl').then((stdout, error) => {
          if (!error) {
            const parts = stdout.toString().split(/\n\s*\n/);
            parts.forEach(element => {
              const lines = element.split('\n');
              if (util.getValue(lines, 'name', ':')) {
                result.push(parseWindowsAudio(lines));
              }
            });
          }
          if (callback) {
            callback(result);
          }
          resolve(result);
        });
      }
      if (_sunos) {
        resolve(null);
      }
    });
  });
}

exports.audio = audio;
