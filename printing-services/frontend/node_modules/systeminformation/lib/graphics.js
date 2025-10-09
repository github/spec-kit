'use strict';
// @ts-check
// ==================================================================================
// graphics.js
// ----------------------------------------------------------------------------------
// Description:   System Information - library
//                for Node.js
// Copyright:     (c) 2014 - 2025
// Author:        Sebastian Hildebrandt
// ----------------------------------------------------------------------------------
// License:       MIT
// ==================================================================================
// 7. Graphics (controller, display)
// ----------------------------------------------------------------------------------

const fs = require('fs');
const exec = require('child_process').exec;
const execSync = require('child_process').execSync;
const util = require('./util');

let _platform = process.platform;
let _nvidiaSmiPath = '';

const _linux = (_platform === 'linux' || _platform === 'android');
const _darwin = (_platform === 'darwin');
const _windows = (_platform === 'win32');
const _freebsd = (_platform === 'freebsd');
const _openbsd = (_platform === 'openbsd');
const _netbsd = (_platform === 'netbsd');
const _sunos = (_platform === 'sunos');

let _resolutionX = 0;
let _resolutionY = 0;
let _pixelDepth = 0;
let _refreshRate = 0;

const videoTypes = {
  '-2': 'UNINITIALIZED',
  '-1': 'OTHER',
  '0': 'HD15',
  '1': 'SVIDEO',
  '2': 'Composite video',
  '3': 'Component video',
  '4': 'DVI',
  '5': 'HDMI',
  '6': 'LVDS',
  '8': 'D_JPN',
  '9': 'SDI',
  '10': 'DP',
  '11': 'DP embedded',
  '12': 'UDI',
  '13': 'UDI embedded',
  '14': 'SDTVDONGLE',
  '15': 'MIRACAST',
  '2147483648': 'INTERNAL'
};

function getVendorFromModel(model) {
  const manufacturers = [
    { pattern: '^LG.+', manufacturer: 'LG' },
    { pattern: '^BENQ.+', manufacturer: 'BenQ' },
    { pattern: '^ASUS.+', manufacturer: 'Asus' },
    { pattern: '^DELL.+', manufacturer: 'Dell' },
    { pattern: '^SAMSUNG.+', manufacturer: 'Samsung' },
    { pattern: '^VIEWSON.+', manufacturer: 'ViewSonic' },
    { pattern: '^SONY.+', manufacturer: 'Sony' },
    { pattern: '^ACER.+', manufacturer: 'Acer' },
    { pattern: '^AOC.+', manufacturer: 'AOC Monitors' },
    { pattern: '^HP.+', manufacturer: 'HP' },
    { pattern: '^EIZO.?', manufacturer: 'Eizo' },
    { pattern: '^PHILIPS.?', manufacturer: 'Philips' },
    { pattern: '^IIYAMA.?', manufacturer: 'Iiyama' },
    { pattern: '^SHARP.?', manufacturer: 'Sharp' },
    { pattern: '^NEC.?', manufacturer: 'NEC' },
    { pattern: '^LENOVO.?', manufacturer: 'Lenovo' },
    { pattern: 'COMPAQ.?', manufacturer: 'Compaq' },
    { pattern: 'APPLE.?', manufacturer: 'Apple' },
    { pattern: 'INTEL.?', manufacturer: 'Intel' },
    { pattern: 'AMD.?', manufacturer: 'AMD' },
    { pattern: 'NVIDIA.?', manufacturer: 'NVDIA' },
  ];

  let result = '';
  if (model) {
    model = model.toUpperCase();
    manufacturers.forEach((manufacturer) => {
      const re = RegExp(manufacturer.pattern);
      if (re.test(model)) { result = manufacturer.manufacturer; }
    });
  }
  return result;
}

function getVendorFromId(id) {
  const vendors = {
    '610': 'Apple',
    '1e6d': 'LG',
    '10ac': 'DELL',
    '4dd9': 'Sony',
    '38a3': 'NEC',
  };
  return vendors[id] || '';
}

function vendorToId(str) {
  let result = '';
  str = (str || '').toLowerCase();
  if (str.indexOf('apple') >= 0) { result = '0x05ac'; }
  else if (str.indexOf('nvidia') >= 0) { result = '0x10de'; }
  else if (str.indexOf('intel') >= 0) { result = '0x8086'; }
  else if (str.indexOf('ati') >= 0 || str.indexOf('amd') >= 0) { result = '0x1002'; }

  return result;
}

function getMetalVersion(id) {
  const families = {
    'spdisplays_mtlgpufamilymac1': 'mac1',
    'spdisplays_mtlgpufamilymac2': 'mac2',
    'spdisplays_mtlgpufamilyapple1': 'apple1',
    'spdisplays_mtlgpufamilyapple2': 'apple2',
    'spdisplays_mtlgpufamilyapple3': 'apple3',
    'spdisplays_mtlgpufamilyapple4': 'apple4',
    'spdisplays_mtlgpufamilyapple5': 'apple5',
    'spdisplays_mtlgpufamilyapple6': 'apple6',
    'spdisplays_mtlgpufamilyapple7': 'apple7',
    'spdisplays_metalfeaturesetfamily11': 'family1_v1',
    'spdisplays_metalfeaturesetfamily12': 'family1_v2',
    'spdisplays_metalfeaturesetfamily13': 'family1_v3',
    'spdisplays_metalfeaturesetfamily14': 'family1_v4',
    'spdisplays_metalfeaturesetfamily21': 'family2_v1'
  };
  return families[id] || '';
}

function graphics(callback) {

  function parseLinesDarwin(graphicsArr) {
    const res = {
      controllers: [],
      displays: []
    };
    try {
      graphicsArr.forEach(function (item) {
        // controllers
        const bus = ((item.sppci_bus || '').indexOf('builtin') > -1 ? 'Built-In' : ((item.sppci_bus || '').indexOf('pcie') > -1 ? 'PCIe' : ''));
        const vram = (parseInt((item.spdisplays_vram || ''), 10) || 0) * (((item.spdisplays_vram || '').indexOf('GB') > -1) ? 1024 : 1);
        const vramDyn = (parseInt((item.spdisplays_vram_shared || ''), 10) || 0) * (((item.spdisplays_vram_shared || '').indexOf('GB') > -1) ? 1024 : 1);
        let metalVersion = getMetalVersion(item.spdisplays_metal || item.spdisplays_metalfamily || '');
        res.controllers.push({
          vendor: getVendorFromModel(item.spdisplays_vendor || '') || item.spdisplays_vendor || '',
          model: item.sppci_model || '',
          bus,
          vramDynamic: bus === 'Built-In',
          vram: vram || vramDyn || null,
          deviceId: item['spdisplays_device-id'] || '',
          vendorId: item['spdisplays_vendor-id'] || vendorToId((item['spdisplays_vendor'] || '') + (item.sppci_model || '')),
          external: (item.sppci_device_type === 'spdisplays_egpu'),
          cores: item['sppci_cores'] || null,
          metalVersion
        });

        // displays
        if (item.spdisplays_ndrvs && item.spdisplays_ndrvs.length) {
          item.spdisplays_ndrvs.forEach(function (displayItem) {
            const connectionType = displayItem['spdisplays_connection_type'] || '';
            const currentResolutionParts = (displayItem['_spdisplays_resolution'] || '').split('@');
            const currentResolution = currentResolutionParts[0].split('x');
            const pixelParts = (displayItem['_spdisplays_pixels'] || '').split('x');
            const pixelDepthString = displayItem['spdisplays_depth'] || '';
            const serial = displayItem['_spdisplays_display-serial-number'] || displayItem['_spdisplays_display-serial-number2'] || null;
            res.displays.push({
              vendor: getVendorFromId(displayItem['_spdisplays_display-vendor-id'] || '') || getVendorFromModel(displayItem['_name'] || ''),
              vendorId: displayItem['_spdisplays_display-vendor-id'] || '',
              model: displayItem['_name'] || '',
              productionYear: displayItem['_spdisplays_display-year'] || null,
              serial: serial !== '0' ? serial : null,
              displayId: displayItem['_spdisplays_displayID'] || null,
              main: displayItem['spdisplays_main'] ? displayItem['spdisplays_main'] === 'spdisplays_yes' : false,
              builtin: (displayItem['spdisplays_display_type'] || '').indexOf('built-in') > -1,
              connection: ((connectionType.indexOf('_internal') > -1) ? 'Internal' : ((connectionType.indexOf('_displayport') > -1) ? 'Display Port' : ((connectionType.indexOf('_hdmi') > -1) ? 'HDMI' : null))),
              sizeX: null,
              sizeY: null,
              pixelDepth: (pixelDepthString === 'CGSThirtyBitColor' ? 30 : (pixelDepthString === 'CGSThirtytwoBitColor' ? 32 : (pixelDepthString === 'CGSTwentyfourBitColor' ? 24 : null))),
              resolutionX: pixelParts.length > 1 ? parseInt(pixelParts[0], 10) : null,
              resolutionY: pixelParts.length > 1 ? parseInt(pixelParts[1], 10) : null,
              currentResX: currentResolution.length > 1 ? parseInt(currentResolution[0], 10) : null,
              currentResY: currentResolution.length > 1 ? parseInt(currentResolution[1], 10) : null,
              positionX: 0,
              positionY: 0,
              currentRefreshRate: currentResolutionParts.length > 1 ? parseInt(currentResolutionParts[1], 10) : null,

            });
          });
        }
      });
      return res;
    } catch (e) {
      return res;
    }
  }

  function parseLinesLinuxControllers(lines) {
    let controllers = [];
    let currentController = {
      vendor: '',
      subVendor: '',
      model: '',
      bus: '',
      busAddress: '',
      vram: null,
      vramDynamic: false,
      pciID: ''
    };
    let isGraphicsController = false;
    // PCI bus IDs
    let pciIDs = [];
    try {
      pciIDs = execSync('export LC_ALL=C; dmidecode -t 9 2>/dev/null; unset LC_ALL | grep "Bus Address: "', util.execOptsLinux).toString().split('\n');
      for (let i = 0; i < pciIDs.length; i++) {
        pciIDs[i] = pciIDs[i].replace('Bus Address:', '').replace('0000:', '').trim();
      }
      pciIDs = pciIDs.filter(function (el) {
        return el != null && el;
      });
    } catch (e) {
      util.noop();
    }
    let i = 1;
    lines.forEach((line) => {
      let subsystem = '';
      if (i < lines.length && lines[i]) {   // get next line;
        subsystem = lines[i];
        if (subsystem.indexOf(':') > 0) {
          subsystem = subsystem.split(':')[1];
        }
      }
      if ('' !== line.trim()) {
        if (' ' !== line[0] && '\t' !== line[0]) {        // first line of new entry
          let isExternal = (pciIDs.indexOf(line.split(' ')[0]) >= 0);
          let vgapos = line.toLowerCase().indexOf(' vga ');
          let _3dcontrollerpos = line.toLowerCase().indexOf('3d controller');
          if (vgapos !== -1 || _3dcontrollerpos !== -1) {         // VGA
            if (_3dcontrollerpos !== -1 && vgapos === -1) {
              vgapos = _3dcontrollerpos;
            }
            if (currentController.vendor || currentController.model || currentController.bus || currentController.vram !== null || currentController.vramDynamic) { // already a controller found
              controllers.push(currentController);
              currentController = {
                vendor: '',
                model: '',
                bus: '',
                busAddress: '',
                vram: null,
                vramDynamic: false,
              };
            }

            const pciIDCandidate = line.split(' ')[0];
            if (/[\da-fA-F]{2}:[\da-fA-F]{2}\.[\da-fA-F]/.test(pciIDCandidate)) {
              currentController.busAddress = pciIDCandidate;
            }
            isGraphicsController = true;
            let endpos = line.search(/\[[0-9a-f]{4}:[0-9a-f]{4}]|$/);
            let parts = line.substr(vgapos, endpos - vgapos).split(':');
            currentController.busAddress = line.substr(0, vgapos).trim();
            if (parts.length > 1) {
              parts[1] = parts[1].trim();
              if (parts[1].toLowerCase().indexOf('corporation') >= 0) {
                currentController.vendor = parts[1].substr(0, parts[1].toLowerCase().indexOf('corporation') + 11).trim();
                currentController.model = parts[1].substr(parts[1].toLowerCase().indexOf('corporation') + 11, 200).split('(')[0].trim();
                currentController.bus = (pciIDs.length > 0 && isExternal) ? 'PCIe' : 'Onboard';
                currentController.vram = null;
                currentController.vramDynamic = false;
              } else if (parts[1].toLowerCase().indexOf(' inc.') >= 0) {
                if ((parts[1].match(/]/g) || []).length > 1) {
                  currentController.vendor = parts[1].substr(0, parts[1].toLowerCase().indexOf(']') + 1).trim();
                  currentController.model = parts[1].substr(parts[1].toLowerCase().indexOf(']') + 1, 200).trim().split('(')[0].trim();
                } else {
                  currentController.vendor = parts[1].substr(0, parts[1].toLowerCase().indexOf(' inc.') + 5).trim();
                  currentController.model = parts[1].substr(parts[1].toLowerCase().indexOf(' inc.') + 5, 200).trim().split('(')[0].trim();
                }
                currentController.bus = (pciIDs.length > 0 && isExternal) ? 'PCIe' : 'Onboard';
                currentController.vram = null;
                currentController.vramDynamic = false;
              } else if (parts[1].toLowerCase().indexOf(' ltd.') >= 0) {
                if ((parts[1].match(/]/g) || []).length > 1) {
                  currentController.vendor = parts[1].substr(0, parts[1].toLowerCase().indexOf(']') + 1).trim();
                  currentController.model = parts[1].substr(parts[1].toLowerCase().indexOf(']') + 1, 200).trim().split('(')[0].trim();
                } else {
                  currentController.vendor = parts[1].substr(0, parts[1].toLowerCase().indexOf(' ltd.') + 5).trim();
                  currentController.model = parts[1].substr(parts[1].toLowerCase().indexOf(' ltd.') + 5, 200).trim().split('(')[0].trim();
                }
              }
              if (currentController.model && subsystem.indexOf(currentController.model) !== -1) {
                const subVendor = subsystem.split(currentController.model)[0].trim();
                if (subVendor) {
                  currentController.subVendor = subVendor;
                }
              }
            }

          } else {
            isGraphicsController = false;
          }
        }
        if (isGraphicsController) { // within VGA details
          let parts = line.split(':');
          if (parts.length > 1 && parts[0].replace(/ +/g, '').toLowerCase().indexOf('devicename') !== -1 && parts[1].toLowerCase().indexOf('onboard') !== -1) { currentController.bus = 'Onboard'; }
          if (parts.length > 1 && parts[0].replace(/ +/g, '').toLowerCase().indexOf('region') !== -1 && parts[1].toLowerCase().indexOf('memory') !== -1) {
            let memparts = parts[1].split('=');
            if (memparts.length > 1) {
              currentController.vram = parseInt(memparts[1]);
            }
          }
        }
      }
      i++;
    });

    if (currentController.vendor || currentController.model || currentController.bus || currentController.busAddress || currentController.vram !== null || currentController.vramDynamic) { // already a controller found
      controllers.push(currentController);
    }
    return (controllers);
  }

  function parseLinesLinuxClinfo(controllers, lines) {
    const fieldPattern = /\[([^\]]+)\]\s+(\w+)\s+(.*)/;
    const devices = lines.reduce((devices, line) => {
      const field = fieldPattern.exec(line.trim());
      if (field) {
        if (!devices[field[1]]) {
          devices[field[1]] = {};
        }
        devices[field[1]][field[2]] = field[3];
      }
      return devices;
    }, {});
    for (let deviceId in devices) {
      const device = devices[deviceId];
      if (device['CL_DEVICE_TYPE'] === 'CL_DEVICE_TYPE_GPU') {
        let busAddress;
        if (device['CL_DEVICE_TOPOLOGY_AMD']) {
          const bdf = device['CL_DEVICE_TOPOLOGY_AMD'].match(/[a-zA-Z0-9]+:\d+\.\d+/);
          if (bdf) {
            busAddress = bdf[0];
          }
        } else if (device['CL_DEVICE_PCI_BUS_ID_NV'] && device['CL_DEVICE_PCI_SLOT_ID_NV']) {
          const bus = parseInt(device['CL_DEVICE_PCI_BUS_ID_NV']);
          const slot = parseInt(device['CL_DEVICE_PCI_SLOT_ID_NV']);
          if (!isNaN(bus) && !isNaN(slot)) {
            const b = bus & 0xff;
            const d = (slot >> 3) & 0xff;
            const f = slot & 0x07;
            busAddress = `${b.toString().padStart(2, '0')}:${d.toString().padStart(2, '0')}.${f}`;
          }
        }
        if (busAddress) {
          let controller = controllers.find(controller => controller.busAddress === busAddress);
          if (!controller) {
            controller = {
              vendor: '',
              model: '',
              bus: '',
              busAddress,
              vram: null,
              vramDynamic: false
            };
            controllers.push(controller);
          }
          controller.vendor = device['CL_DEVICE_VENDOR'];
          if (device['CL_DEVICE_BOARD_NAME_AMD']) {
            controller.model = device['CL_DEVICE_BOARD_NAME_AMD'];
          } else {
            controller.model = device['CL_DEVICE_NAME'];
          }
          const memory = parseInt(device['CL_DEVICE_GLOBAL_MEM_SIZE']);
          if (!isNaN(memory)) {
            controller.vram = Math.round(memory / 1024 / 1024);
          }
        }
      }
    }
    return controllers;
  }

  function getNvidiaSmi() {
    if (_nvidiaSmiPath) {
      return _nvidiaSmiPath;
    }

    if (_windows) {
      try {
        const basePath = util.WINDIR + '\\System32\\DriverStore\\FileRepository';
        // find all directories that have an nvidia-smi.exe file
        const candidateDirs = fs.readdirSync(basePath).filter(dir => {
          return fs.readdirSync([basePath, dir].join('/')).includes('nvidia-smi.exe');
        });
        // use the directory with the most recently created nvidia-smi.exe file
        const targetDir = candidateDirs.reduce((prevDir, currentDir) => {
          const previousNvidiaSmi = fs.statSync([basePath, prevDir, 'nvidia-smi.exe'].join('/'));
          const currentNvidiaSmi = fs.statSync([basePath, currentDir, 'nvidia-smi.exe'].join('/'));
          return (previousNvidiaSmi.ctimeMs > currentNvidiaSmi.ctimeMs) ? prevDir : currentDir;
        });

        if (targetDir) {
          _nvidiaSmiPath = [basePath, targetDir, 'nvidia-smi.exe'].join('/');
        }
      } catch (e) {
        util.noop();
      }
    } else if (_linux) {
      _nvidiaSmiPath = 'nvidia-smi';
    }
    return _nvidiaSmiPath;
  }

  function nvidiaSmi(options) {
    const nvidiaSmiExe = getNvidiaSmi();
    options = options || util.execOptsWin;
    if (nvidiaSmiExe) {
      const nvidiaSmiOpts = '--query-gpu=driver_version,pci.sub_device_id,name,pci.bus_id,fan.speed,memory.total,memory.used,memory.free,utilization.gpu,utilization.memory,temperature.gpu,temperature.memory,power.draw,power.limit,clocks.gr,clocks.mem --format=csv,noheader,nounits';
      const cmd = nvidiaSmiExe + ' ' + nvidiaSmiOpts + (_linux ? '  2>/dev/null' : '');
      if (_linux) {
        options.stdio = ['pipe', 'pipe', 'ignore'];
      }
      try {
        const sanitized = util.sanitizeShellString(cmd);
        const res = execSync(sanitized, options).toString();
        return res;
      } catch (e) {
        util.noop();
      }
    }
    return '';
  }

  function nvidiaDevices() {

    function safeParseNumber(value) {
      if ([null, undefined].includes(value)) {
        return value;
      }
      return parseFloat(value);
    }

    const stdout = nvidiaSmi();
    if (!stdout) {
      return [];
    }

    const gpus = stdout.split('\n').filter(Boolean);
    let results = gpus.map(gpu => {
      const splittedData = gpu.split(', ').map(value => value.includes('N/A') ? undefined : value);
      if (splittedData.length === 16) {
        return {
          driverVersion: splittedData[0],
          subDeviceId: splittedData[1],
          name: splittedData[2],
          pciBus: splittedData[3],
          fanSpeed: safeParseNumber(splittedData[4]),
          memoryTotal: safeParseNumber(splittedData[5]),
          memoryUsed: safeParseNumber(splittedData[6]),
          memoryFree: safeParseNumber(splittedData[7]),
          utilizationGpu: safeParseNumber(splittedData[8]),
          utilizationMemory: safeParseNumber(splittedData[9]),
          temperatureGpu: safeParseNumber(splittedData[10]),
          temperatureMemory: safeParseNumber(splittedData[11]),
          powerDraw: safeParseNumber(splittedData[12]),
          powerLimit: safeParseNumber(splittedData[13]),
          clockCore: safeParseNumber(splittedData[14]),
          clockMemory: safeParseNumber(splittedData[15]),
        };
      } else {
        return {};
      }
    });
    results = results.filter((item) => {
      return ('pciBus' in item);
    });
    return results;
  }

  function mergeControllerNvidia(controller, nvidia) {
    if (nvidia.driverVersion) { controller.driverVersion = nvidia.driverVersion; }
    if (nvidia.subDeviceId) { controller.subDeviceId = nvidia.subDeviceId; }
    if (nvidia.name) { controller.name = nvidia.name; }
    if (nvidia.pciBus) { controller.pciBus = nvidia.pciBus; }
    if (nvidia.fanSpeed) { controller.fanSpeed = nvidia.fanSpeed; }
    if (nvidia.memoryTotal) {
      controller.memoryTotal = nvidia.memoryTotal;
      controller.vram = nvidia.memoryTotal;
      controller.vramDynamic = false;
    }
    if (nvidia.memoryUsed) { controller.memoryUsed = nvidia.memoryUsed; }
    if (nvidia.memoryFree) { controller.memoryFree = nvidia.memoryFree; }
    if (nvidia.utilizationGpu) { controller.utilizationGpu = nvidia.utilizationGpu; }
    if (nvidia.utilizationMemory) { controller.utilizationMemory = nvidia.utilizationMemory; }
    if (nvidia.temperatureGpu) { controller.temperatureGpu = nvidia.temperatureGpu; }
    if (nvidia.temperatureMemory) { controller.temperatureMemory = nvidia.temperatureMemory; }
    if (nvidia.powerDraw) { controller.powerDraw = nvidia.powerDraw; }
    if (nvidia.powerLimit) { controller.powerLimit = nvidia.powerLimit; }
    if (nvidia.clockCore) { controller.clockCore = nvidia.clockCore; }
    if (nvidia.clockMemory) { controller.clockMemory = nvidia.clockMemory; }
    return controller;
  }

  function parseLinesLinuxEdid(edid) {
    // parsen EDID
    // --> model
    // --> resolutionx
    // --> resolutiony
    // --> builtin = false
    // --> pixeldepth (?)
    // --> sizex
    // --> sizey
    let result = {
      vendor: '',
      model: '',
      deviceName: '',
      main: false,
      builtin: false,
      connection: '',
      sizeX: null,
      sizeY: null,
      pixelDepth: null,
      resolutionX: null,
      resolutionY: null,
      currentResX: null,
      currentResY: null,
      positionX: 0,
      positionY: 0,
      currentRefreshRate: null
    };
    // find first "Detailed Timing Description"
    let start = 108;
    if (edid.substr(start, 6) === '000000') {
      start += 36;
    }
    if (edid.substr(start, 6) === '000000') {
      start += 36;
    }
    if (edid.substr(start, 6) === '000000') {
      start += 36;
    }
    if (edid.substr(start, 6) === '000000') {
      start += 36;
    }
    result.resolutionX = parseInt('0x0' + edid.substr(start + 8, 1) + edid.substr(start + 4, 2));
    result.resolutionY = parseInt('0x0' + edid.substr(start + 14, 1) + edid.substr(start + 10, 2));
    result.sizeX = parseInt('0x0' + edid.substr(start + 28, 1) + edid.substr(start + 24, 2));
    result.sizeY = parseInt('0x0' + edid.substr(start + 29, 1) + edid.substr(start + 26, 2));
    // monitor name
    start = edid.indexOf('000000fc00'); // find first "Monitor Description Data"
    if (start >= 0) {
      let model_raw = edid.substr(start + 10, 26);
      if (model_raw.indexOf('0a') !== -1) {
        model_raw = model_raw.substr(0, model_raw.indexOf('0a'));
      }
      try {
        if (model_raw.length > 2) {
          result.model = model_raw.match(/.{1,2}/g).map(function (v) {
            return String.fromCharCode(parseInt(v, 16));
          }).join('');
        }
      } catch (e) {
        util.noop();
      }
    } else {
      result.model = '';
    }
    return result;
  }

  function parseLinesLinuxDisplays(lines, depth) {
    let displays = [];
    let currentDisplay = {
      vendor: '',
      model: '',
      deviceName: '',
      main: false,
      builtin: false,
      connection: '',
      sizeX: null,
      sizeY: null,
      pixelDepth: null,
      resolutionX: null,
      resolutionY: null,
      currentResX: null,
      currentResY: null,
      positionX: 0,
      positionY: 0,
      currentRefreshRate: null
    };
    let is_edid = false;
    let is_current = false;
    let edid_raw = '';
    let start = 0;
    for (let i = 1; i < lines.length; i++) {        // start with second line
      if ('' !== lines[i].trim()) {
        if (' ' !== lines[i][0] && '\t' !== lines[i][0] && lines[i].toLowerCase().indexOf(' connected ') !== -1) {        // first line of new entry
          if (currentDisplay.model || currentDisplay.main || currentDisplay.builtin || currentDisplay.connection || currentDisplay.sizeX !== null || currentDisplay.pixelDepth !== null || currentDisplay.resolutionX !== null) {         // push last display to array
            displays.push(currentDisplay);
            currentDisplay = {
              vendor: '',
              model: '',
              main: false,
              builtin: false,
              connection: '',
              sizeX: null,
              sizeY: null,
              pixelDepth: null,
              resolutionX: null,
              resolutionY: null,
              currentResX: null,
              currentResY: null,
              positionX: 0,
              positionY: 0,
              currentRefreshRate: null
            };
          }
          let parts = lines[i].split(' ');
          currentDisplay.connection = parts[0];
          currentDisplay.main = lines[i].toLowerCase().indexOf(' primary ') >= 0;
          currentDisplay.builtin = (parts[0].toLowerCase().indexOf('edp') >= 0);
        }

        // try to read EDID information
        if (is_edid) {
          if (lines[i].search(/\S|$/) > start) {
            edid_raw += lines[i].toLowerCase().trim();
          } else {
            // parsen EDID
            let edid_decoded = parseLinesLinuxEdid(edid_raw);
            currentDisplay.vendor = edid_decoded.vendor;
            currentDisplay.model = edid_decoded.model;
            currentDisplay.resolutionX = edid_decoded.resolutionX;
            currentDisplay.resolutionY = edid_decoded.resolutionY;
            currentDisplay.sizeX = edid_decoded.sizeX;
            currentDisplay.sizeY = edid_decoded.sizeY;
            currentDisplay.pixelDepth = depth;
            is_edid = false;
          }
        }
        if (lines[i].toLowerCase().indexOf('edid:') >= 0) {
          is_edid = true;
          start = lines[i].search(/\S|$/);
        }
        if (lines[i].toLowerCase().indexOf('*current') >= 0) {
          const parts1 = lines[i].split('(');
          if (parts1 && parts1.length > 1 && parts1[0].indexOf('x') >= 0) {
            const resParts = parts1[0].trim().split('x');
            currentDisplay.currentResX = util.toInt(resParts[0]);
            currentDisplay.currentResY = util.toInt(resParts[1]);
          }
          is_current = true;
        }
        if (is_current && lines[i].toLowerCase().indexOf('clock') >= 0 && lines[i].toLowerCase().indexOf('hz') >= 0 && lines[i].toLowerCase().indexOf('v: height') >= 0) {
          const parts1 = lines[i].split('clock');
          if (parts1 && parts1.length > 1 && parts1[1].toLowerCase().indexOf('hz') >= 0) {
            currentDisplay.currentRefreshRate = util.toInt(parts1[1]);
          }
          is_current = false;
        }
      }
    }

    // pushen displays
    if (currentDisplay.model || currentDisplay.main || currentDisplay.builtin || currentDisplay.connection || currentDisplay.sizeX !== null || currentDisplay.pixelDepth !== null || currentDisplay.resolutionX !== null) {  // still information there
      displays.push(currentDisplay);
    }
    return displays;
  }

  // function starts here
  return new Promise((resolve) => {
    process.nextTick(() => {
      let result = {
        controllers: [],
        displays: []
      };
      if (_darwin) {
        let cmd = 'system_profiler -xml -detailLevel full SPDisplaysDataType';
        exec(cmd, function (error, stdout) {
          if (!error) {
            try {
              const output = stdout.toString();
              result = parseLinesDarwin(util.plistParser(output)[0]._items);
            } catch (e) {
              util.noop();
            }
            try {
              stdout = execSync('defaults read /Library/Preferences/com.apple.windowserver.plist 2>/dev/null;defaults read /Library/Preferences/com.apple.windowserver.displays.plist 2>/dev/null; echo ""', { maxBuffer: 1024 * 20000 });
              const output = (stdout || '').toString();
              const obj = util.plistReader(output);
              if (obj['DisplayAnyUserSets'] && obj['DisplayAnyUserSets']['Configs'] && obj['DisplayAnyUserSets']['Configs'][0] && obj['DisplayAnyUserSets']['Configs'][0]['DisplayConfig']) {
                const current = obj['DisplayAnyUserSets']['Configs'][0]['DisplayConfig'];
                let i = 0;
                current.forEach((o) => {
                  if (o['CurrentInfo'] && o['CurrentInfo']['OriginX'] !== undefined && result.displays && result.displays[i]) {
                    result.displays[i].positionX = o['CurrentInfo']['OriginX'];
                  }
                  if (o['CurrentInfo'] && o['CurrentInfo']['OriginY'] !== undefined && result.displays && result.displays[i]) {
                    result.displays[i].positionY = o['CurrentInfo']['OriginY'];
                  }
                  i++;
                });
              }
              if (obj['DisplayAnyUserSets'] && obj['DisplayAnyUserSets'].length > 0 && obj['DisplayAnyUserSets'][0].length > 0 && obj['DisplayAnyUserSets'][0][0]['DisplayID']) {
                const current = obj['DisplayAnyUserSets'][0];
                let i = 0;
                current.forEach((o) => {
                  if ('OriginX' in o && result.displays && result.displays[i]) {
                    result.displays[i].positionX = o['OriginX'];
                  }
                  if ('OriginY' in o && result.displays && result.displays[i]) {
                    result.displays[i].positionY = o['OriginY'];
                  }
                  if (o['Mode'] && o['Mode']['BitsPerPixel'] !== undefined && result.displays && result.displays[i]) {
                    result.displays[i].pixelDepth = o['Mode']['BitsPerPixel'];
                  }
                  i++;
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
      if (_linux) {
        // Raspberry: https://elinux.org/RPI_vcgencmd_usage
        if (util.isRaspberry()) {
          let cmd = 'fbset -s 2> /dev/null | grep \'mode "\' ; vcgencmd get_mem gpu 2> /dev/null; tvservice -s 2> /dev/null; tvservice -n 2> /dev/null;';
          exec(cmd, function (error, stdout) {
            let lines = stdout.toString().split('\n');
            if (lines.length > 3 && lines[0].indexOf('mode "') >= -1 && lines[2].indexOf('0x12000a') > -1) {
              const parts = lines[0].replace('mode', '').replace(/"/g, '').trim().split('x');
              if (parts.length === 2) {
                result.displays.push({
                  vendor: '',
                  model: util.getValue(lines, 'device_name', '='),
                  main: true,
                  builtin: false,
                  connection: 'HDMI',
                  sizeX: null,
                  sizeY: null,
                  pixelDepth: null,
                  resolutionX: parseInt(parts[0], 10),
                  resolutionY: parseInt(parts[1], 10),
                  currentResX: null,
                  currentResY: null,
                  positionX: 0,
                  positionY: 0,
                  currentRefreshRate: null
                });
              }
            }
            if (lines.length >= 1 && stdout.toString().indexOf('gpu=') >= -1) {
              result.controllers.push({
                vendor: 'Broadcom',
                model: util.getRpiGpu(),
                bus: '',
                vram: util.getValue(lines, 'gpu', '=').replace('M', ''),
                vramDynamic: true
              });
            }
            // if (callback) {
            //   callback(result);
            // }
            // resolve(result);
          });
        }
        // } else {
        let cmd = 'lspci -vvv  2>/dev/null';
        exec(cmd, function (error, stdout) {
          if (!error) {
            let lines = stdout.toString().split('\n');
            if (result.controllers.length === 0) {
              result.controllers = parseLinesLinuxControllers(lines);

              const nvidiaData = nvidiaDevices();
              // needs to be rewritten ... using no spread operators
              result.controllers = result.controllers.map((controller) => { // match by busAddress
                return mergeControllerNvidia(controller, nvidiaData.find((contr) => contr.pciBus.toLowerCase().endsWith(controller.busAddress.toLowerCase())) || {});
              });
            }
          }
          let cmd = 'clinfo --raw';
          exec(cmd, function (error, stdout) {
            if (!error) {
              let lines = stdout.toString().split('\n');
              result.controllers = parseLinesLinuxClinfo(result.controllers, lines);
            }
            let cmd = 'xdpyinfo 2>/dev/null | grep \'depth of root window\' | awk \'{ print $5 }\'';
            exec(cmd, function (error, stdout) {
              let depth = 0;
              if (!error) {
                let lines = stdout.toString().split('\n');
                depth = parseInt(lines[0]) || 0;
              }
              let cmd = 'xrandr --verbose 2>/dev/null';
              exec(cmd, function (error, stdout) {
                if (!error) {
                  let lines = stdout.toString().split('\n');
                  result.displays = parseLinesLinuxDisplays(lines, depth);
                }
                if (callback) {
                  callback(result);
                }
                resolve(result);
              });
            });
          });
        });
        // }
      }
      if (_freebsd || _openbsd || _netbsd) {
        if (callback) { callback(null); }
        resolve(null);
      }
      if (_sunos) {
        if (callback) { callback(null); }
        resolve(null);
      }
      if (_windows) {

        // https://blogs.technet.microsoft.com/heyscriptingguy/2013/10/03/use-powershell-to-discover-multi-monitor-information/
        // https://devblogs.microsoft.com/scripting/use-powershell-to-discover-multi-monitor-information/
        try {
          const workload = [];
          workload.push(util.powerShell('Get-CimInstance win32_VideoController | fl *'));
          workload.push(util.powerShell('gp "HKLM:\\SYSTEM\\ControlSet001\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}\\*" -ErrorAction SilentlyContinue | where MatchingDeviceId $null -NE | select MatchingDeviceId,HardwareInformation.qwMemorySize | fl'));
          workload.push(util.powerShell('Get-CimInstance win32_desktopmonitor | fl *'));
          workload.push(util.powerShell('Get-CimInstance -Namespace root\\wmi -ClassName WmiMonitorBasicDisplayParams | fl'));
          workload.push(util.powerShell('Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::AllScreens'));
          workload.push(util.powerShell('Get-CimInstance -Namespace root\\wmi -ClassName WmiMonitorConnectionParams | fl'));
          workload.push(util.powerShell('gwmi WmiMonitorID -Namespace root\\wmi | ForEach-Object {(($_.ManufacturerName -notmatch 0 | foreach {[char]$_}) -join "") + "|" + (($_.ProductCodeID -notmatch 0 | foreach {[char]$_}) -join "") + "|" + (($_.UserFriendlyName -notmatch 0 | foreach {[char]$_}) -join "") + "|" + (($_.SerialNumberID -notmatch 0 | foreach {[char]$_}) -join "") + "|" + $_.InstanceName}'));

          const nvidiaData = nvidiaDevices();

          Promise.all(
            workload
          ).then((data) => {
            // controller + vram
            let csections = data[0].replace(/\r/g, '').split(/\n\s*\n/);
            let vsections = data[1].replace(/\r/g, '').split(/\n\s*\n/);
            result.controllers = parseLinesWindowsControllers(csections, vsections);
            result.controllers = result.controllers.map((controller) => { // match by subDeviceId
              if (controller.vendor.toLowerCase() === 'nvidia') {
                return mergeControllerNvidia(controller, nvidiaData.find(device => {
                  let windowsSubDeviceId = (controller.subDeviceId || '').toLowerCase();
                  const nvidiaSubDeviceIdParts = device.subDeviceId.split('x');
                  let nvidiaSubDeviceId = nvidiaSubDeviceIdParts.length > 1 ? nvidiaSubDeviceIdParts[1].toLowerCase() : nvidiaSubDeviceIdParts[0].toLowerCase();
                  const lengthDifference = Math.abs(windowsSubDeviceId.length - nvidiaSubDeviceId.length);
                  if (windowsSubDeviceId.length > nvidiaSubDeviceId.length) {
                    for (let i = 0; i < lengthDifference; i++) {
                      nvidiaSubDeviceId = '0' + nvidiaSubDeviceId;
                    }
                  } else if (windowsSubDeviceId.length < nvidiaSubDeviceId.length) {
                    for (let i = 0; i < lengthDifference; i++) {
                      windowsSubDeviceId = '0' + windowsSubDeviceId;
                    }
                  }
                  return windowsSubDeviceId === nvidiaSubDeviceId;
                }) || {});
              } else {
                return controller;
              }
            });

            // displays
            let dsections = data[2].replace(/\r/g, '').split(/\n\s*\n/);
            // result.displays = parseLinesWindowsDisplays(dsections);
            if (dsections[0].trim() === '') { dsections.shift(); }
            if (dsections.length && dsections[dsections.length - 1].trim() === '') { dsections.pop(); }

            // monitor (powershell)
            let msections = data[3].replace(/\r/g, '').split('Active ');
            msections.shift();

            // forms.screens (powershell)
            let ssections = data[4].replace(/\r/g, '').split('BitsPerPixel ');
            ssections.shift();

            // connection params (powershell) - video type
            let tsections = data[5].replace(/\r/g, '').split(/\n\s*\n/);
            tsections.shift();

            // monitor ID (powershell) - model / vendor
            const res = data[6].replace(/\r/g, '').split(/\n/);
            let isections = [];
            res.forEach(element => {
              const parts = element.split('|');
              if (parts.length === 5) {
                isections.push({
                  vendor: parts[0],
                  code: parts[1],
                  model: parts[2],
                  serial: parts[3],
                  instanceId: parts[4]
                });
              }
            });

            result.displays = parseLinesWindowsDisplaysPowershell(ssections, msections, dsections, tsections, isections);

            if (result.displays.length === 1) {
              if (_resolutionX) {
                result.displays[0].resolutionX = _resolutionX;
                if (!result.displays[0].currentResX) {
                  result.displays[0].currentResX = _resolutionX;
                }
              }
              if (_resolutionY) {
                result.displays[0].resolutionY = _resolutionY;
                if (result.displays[0].currentResY === 0) {
                  result.displays[0].currentResY = _resolutionY;
                }
              }
              if (_pixelDepth) {
                result.displays[0].pixelDepth = _pixelDepth;
              }
            }
            result.displays = result.displays.map(element => {
              if (_refreshRate && !element.currentRefreshRate) {
                element.currentRefreshRate = _refreshRate;
              }
              return element;
            });

            if (callback) {
              callback(result);
            }
            resolve(result);
          })
            .catch(() => {
              if (callback) {
                callback(result);
              }
              resolve(result);
            });
        } catch (e) {
          if (callback) { callback(result); }
          resolve(result);
        }
      }
    });
  });

  function parseLinesWindowsControllers(sections, vections) {
    const memorySizes = {};
    for (const i in vections) {
      if ({}.hasOwnProperty.call(vections, i)) {
        if (vections[i].trim() !== '') {
          const lines = vections[i].trim().split('\n');
          const matchingDeviceId = util.getValue(lines, 'MatchingDeviceId').match(/PCI\\(VEN_[0-9A-F]{4})&(DEV_[0-9A-F]{4})(?:&(SUBSYS_[0-9A-F]{8}))?(?:&(REV_[0-9A-F]{2}))?/i);
          if (matchingDeviceId) {
            const quadWordmemorySize = parseInt(util.getValue(lines, 'HardwareInformation.qwMemorySize'));
            if (!isNaN(quadWordmemorySize)) {
              let deviceId = matchingDeviceId[1].toUpperCase() + '&' + matchingDeviceId[2].toUpperCase();
              if (matchingDeviceId[3]) {
                deviceId += '&' + matchingDeviceId[3].toUpperCase();
              }
              if (matchingDeviceId[4]) {
                deviceId += '&' + matchingDeviceId[4].toUpperCase();
              }
              memorySizes[deviceId] = quadWordmemorySize;
            }
          }
        }
      }
    }

    let controllers = [];
    for (let i in sections) {
      if ({}.hasOwnProperty.call(sections, i)) {
        if (sections[i].trim() !== '') {
          let lines = sections[i].trim().split('\n');
          let pnpDeviceId = util.getValue(lines, 'PNPDeviceID', ':').match(/PCI\\(VEN_[0-9A-F]{4})&(DEV_[0-9A-F]{4})(?:&(SUBSYS_[0-9A-F]{8}))?(?:&(REV_[0-9A-F]{2}))?/i);
          let subDeviceId = null;
          let memorySize = null;
          if (pnpDeviceId) {
            subDeviceId = pnpDeviceId[3] || '';
            if (subDeviceId) {
              subDeviceId = subDeviceId.split('_')[1];
            }

            // Match PCI device identifier (there's an order of increasing generality):
            // https://docs.microsoft.com/en-us/windows-hardware/drivers/install/identifiers-for-pci-devices

            // PCI\VEN_v(4)&DEV_d(4)&SUBSYS_s(4)n(4)&REV_r(2)
            if (memorySize == null && pnpDeviceId[3] && pnpDeviceId[4]) {
              const deviceId = pnpDeviceId[1].toUpperCase() + '&' + pnpDeviceId[2].toUpperCase() + '&' + pnpDeviceId[3].toUpperCase() + '&' + pnpDeviceId[4].toUpperCase();
              if ({}.hasOwnProperty.call(memorySizes, deviceId)) {
                memorySize = memorySizes[deviceId];
              }
            }

            // PCI\VEN_v(4)&DEV_d(4)&SUBSYS_s(4)n(4)
            if (memorySize == null && pnpDeviceId[3]) {
              const deviceId = pnpDeviceId[1].toUpperCase() + '&' + pnpDeviceId[2].toUpperCase() + '&' + pnpDeviceId[3].toUpperCase();
              if ({}.hasOwnProperty.call(memorySizes, deviceId)) {
                memorySize = memorySizes[deviceId];
              }
            }

            // PCI\VEN_v(4)&DEV_d(4)&REV_r(2)
            if (memorySize == null && pnpDeviceId[4]) {
              const deviceId = pnpDeviceId[1].toUpperCase() + '&' + pnpDeviceId[2].toUpperCase() + '&' + pnpDeviceId[4].toUpperCase();
              if ({}.hasOwnProperty.call(memorySizes, deviceId)) {
                memorySize = memorySizes[deviceId];
              }
            }

            // PCI\VEN_v(4)&DEV_d(4)
            if (memorySize == null) {
              const deviceId = pnpDeviceId[1].toUpperCase() + '&' + pnpDeviceId[2].toUpperCase();
              if ({}.hasOwnProperty.call(memorySizes, deviceId)) {
                memorySize = memorySizes[deviceId];
              }
            }
          }

          controllers.push({
            vendor: util.getValue(lines, 'AdapterCompatibility', ':'),
            model: util.getValue(lines, 'name', ':'),
            bus: util.getValue(lines, 'PNPDeviceID', ':').startsWith('PCI') ? 'PCI' : '',
            vram: (memorySize == null ? util.toInt(util.getValue(lines, 'AdapterRAM', ':')) : memorySize) / 1024 / 1024,
            vramDynamic: (util.getValue(lines, 'VideoMemoryType', ':') === '2'),
            subDeviceId
          });
          _resolutionX = util.toInt(util.getValue(lines, 'CurrentHorizontalResolution', ':')) || _resolutionX;
          _resolutionY = util.toInt(util.getValue(lines, 'CurrentVerticalResolution', ':')) || _resolutionY;
          _refreshRate = util.toInt(util.getValue(lines, 'CurrentRefreshRate', ':')) || _refreshRate;
          _pixelDepth = util.toInt(util.getValue(lines, 'CurrentBitsPerPixel', ':')) || _pixelDepth;
        }
      }
    }
    return controllers;
  }

  function parseLinesWindowsDisplaysPowershell(ssections, msections, dsections, tsections, isections) {
    let displays = [];
    let vendor = '';
    let model = '';
    let deviceID = '';
    let resolutionX = 0;
    let resolutionY = 0;
    if (dsections && dsections.length) {
      let linesDisplay = dsections[0].split('\n');
      vendor = util.getValue(linesDisplay, 'MonitorManufacturer', ':');
      model = util.getValue(linesDisplay, 'Name', ':');
      deviceID = util.getValue(linesDisplay, 'PNPDeviceID', ':').replace(/&amp;/g, '&').toLowerCase();
      resolutionX = util.toInt(util.getValue(linesDisplay, 'ScreenWidth', ':'));
      resolutionY = util.toInt(util.getValue(linesDisplay, 'ScreenHeight', ':'));
    }
    for (let i = 0; i < ssections.length; i++) {
      if (ssections[i].trim() !== '') {
        ssections[i] = 'BitsPerPixel ' + ssections[i];
        msections[i] = 'Active ' + msections[i];
        // tsections can be empty OR undefined on earlier versions of powershell (<=2.0)
        // Tag connection type as UNKNOWN by default if this information is missing
        if (tsections.length === 0 || tsections[i] === undefined) {
          tsections[i] = 'Unknown';
        }
        let linesScreen = ssections[i].split('\n');
        let linesMonitor = msections[i].split('\n');

        let linesConnection = tsections[i].split('\n');
        const bitsPerPixel = util.getValue(linesScreen, 'BitsPerPixel');
        const bounds = util.getValue(linesScreen, 'Bounds').replace('{', '').replace('}', '').replace(/=/g, ':').split(',');
        const primary = util.getValue(linesScreen, 'Primary');
        const sizeX = util.getValue(linesMonitor, 'MaxHorizontalImageSize');
        const sizeY = util.getValue(linesMonitor, 'MaxVerticalImageSize');
        const instanceName = util.getValue(linesMonitor, 'InstanceName').toLowerCase();
        const videoOutputTechnology = util.getValue(linesConnection, 'VideoOutputTechnology');
        const deviceName = util.getValue(linesScreen, 'DeviceName');
        let displayVendor = '';
        let displayModel = '';
        isections.forEach(element => {
          if (element.instanceId.toLowerCase().startsWith(instanceName) && vendor.startsWith('(') && model.startsWith('PnP')) {
            displayVendor = element.vendor;
            displayModel = element.model;
          }
        });
        displays.push({
          vendor: instanceName.startsWith(deviceID) && displayVendor === '' ? vendor : displayVendor,
          model: instanceName.startsWith(deviceID) && displayModel === '' ? model : displayModel,
          deviceName,
          main: primary.toLowerCase() === 'true',
          builtin: videoOutputTechnology === '2147483648',
          connection: videoOutputTechnology && videoTypes[videoOutputTechnology] ? videoTypes[videoOutputTechnology] : '',
          resolutionX: util.toInt(util.getValue(bounds, 'Width', ':')),
          resolutionY: util.toInt(util.getValue(bounds, 'Height', ':')),
          sizeX: sizeX ? parseInt(sizeX, 10) : null,
          sizeY: sizeY ? parseInt(sizeY, 10) : null,
          pixelDepth: bitsPerPixel,
          currentResX: util.toInt(util.getValue(bounds, 'Width', ':')),
          currentResY: util.toInt(util.getValue(bounds, 'Height', ':')),
          positionX: util.toInt(util.getValue(bounds, 'X', ':')),
          positionY: util.toInt(util.getValue(bounds, 'Y', ':')),
        });
      }
    }
    if (ssections.length === 0) {
      displays.push({
        vendor,
        model,
        main: true,
        sizeX: null,
        sizeY: null,
        resolutionX,
        resolutionY,
        pixelDepth: null,
        currentResX: resolutionX,
        currentResY: resolutionY,
        positionX: 0,
        positionY: 0
      });
    }
    return displays;
  }
}

exports.graphics = graphics;
