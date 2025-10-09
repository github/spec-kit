'use strict';
// @ts-check
// ==================================================================================
// cpu.js
// ----------------------------------------------------------------------------------
// Description:   System Information - library
//                for Node.js
// Copyright:     (c) 2014 - 2025
// Author:        Sebastian Hildebrandt
// ----------------------------------------------------------------------------------
// License:       MIT
// ==================================================================================
// 4. CPU
// ----------------------------------------------------------------------------------

const os = require('os');
const exec = require('child_process').exec;
const execSync = require('child_process').execSync;
const fs = require('fs');
const util = require('./util');

let _platform = process.platform;

const _linux = (_platform === 'linux' || _platform === 'android');
const _darwin = (_platform === 'darwin');
const _windows = (_platform === 'win32');
const _freebsd = (_platform === 'freebsd');
const _openbsd = (_platform === 'openbsd');
const _netbsd = (_platform === 'netbsd');
const _sunos = (_platform === 'sunos');

let _cpu_speed = 0;
let _current_cpu = {
  user: 0,
  nice: 0,
  system: 0,
  idle: 0,
  irq: 0,
  steal: 0,
  guest: 0,
  load: 0,
  tick: 0,
  ms: 0,
  currentLoad: 0,
  currentLoadUser: 0,
  currentLoadSystem: 0,
  currentLoadNice: 0,
  currentLoadIdle: 0,
  currentLoadIrq: 0,
  currentLoadSteal: 0,
  currentLoadGuest: 0,
  rawCurrentLoad: 0,
  rawCurrentLoadUser: 0,
  rawCurrentLoadSystem: 0,
  rawCurrentLoadNice: 0,
  rawCurrentLoadIdle: 0,
  rawCurrentLoadIrq: 0,
  rawCurrentLoadSteal: 0,
  rawCurrentLoadGuest: 0
};
let _cpus = [];
let _corecount = 0;

const AMDBaseFrequencies = {
  '8346': '1.8',
  '8347': '1.9',
  '8350': '2.0',
  '8354': '2.2',
  '8356|SE': '2.4',
  '8356': '2.3',
  '8360': '2.5',
  '2372': '2.1',
  '2373': '2.1',
  '2374': '2.2',
  '2376': '2.3',
  '2377': '2.3',
  '2378': '2.4',
  '2379': '2.4',
  '2380': '2.5',
  '2381': '2.5',
  '2382': '2.6',
  '2384': '2.7',
  '2386': '2.8',
  '2387': '2.8',
  '2389': '2.9',
  '2393': '3.1',
  '8374': '2.2',
  '8376': '2.3',
  '8378': '2.4',
  '8379': '2.4',
  '8380': '2.5',
  '8381': '2.5',
  '8382': '2.6',
  '8384': '2.7',
  '8386': '2.8',
  '8387': '2.8',
  '8389': '2.9',
  '8393': '3.1',
  '2419EE': '1.8',
  '2423HE': '2.0',
  '2425HE': '2.1',
  '2427': '2.2',
  '2431': '2.4',
  '2435': '2.6',
  '2439SE': '2.8',
  '8425HE': '2.1',
  '8431': '2.4',
  '8435': '2.6',
  '8439SE': '2.8',
  '4122': '2.2',
  '4130': '2.6',
  '4162EE': '1.7',
  '4164EE': '1.8',
  '4170HE': '2.1',
  '4174HE': '2.3',
  '4176HE': '2.4',
  '4180': '2.6',
  '4184': '2.8',
  '6124HE': '1.8',
  '6128HE': '2.0',
  '6132HE': '2.2',
  '6128': '2.0',
  '6134': '2.3',
  '6136': '2.4',
  '6140': '2.6',
  '6164HE': '1.7',
  '6166HE': '1.8',
  '6168': '1.9',
  '6172': '2.1',
  '6174': '2.2',
  '6176': '2.3',
  '6176SE': '2.3',
  '6180SE': '2.5',
  '3250': '2.5',
  '3260': '2.7',
  '3280': '2.4',
  '4226': '2.7',
  '4228': '2.8',
  '4230': '2.9',
  '4234': '3.1',
  '4238': '3.3',
  '4240': '3.4',
  '4256': '1.6',
  '4274': '2.5',
  '4276': '2.6',
  '4280': '2.8',
  '4284': '3.0',
  '6204': '3.3',
  '6212': '2.6',
  '6220': '3.0',
  '6234': '2.4',
  '6238': '2.6',
  '6262HE': '1.6',
  '6272': '2.1',
  '6274': '2.2',
  '6276': '2.3',
  '6278': '2.4',
  '6282SE': '2.6',
  '6284SE': '2.7',
  '6308': '3.5',
  '6320': '2.8',
  '6328': '3.2',
  '6338P': '2.3',
  '6344': '2.6',
  '6348': '2.8',
  '6366': '1.8',
  '6370P': '2.0',
  '6376': '2.3',
  '6378': '2.4',
  '6380': '2.5',
  '6386': '2.8',
  'FX|4100': '3.6',
  'FX|4120': '3.9',
  'FX|4130': '3.8',
  'FX|4150': '3.8',
  'FX|4170': '4.2',
  'FX|6100': '3.3',
  'FX|6120': '3.6',
  'FX|6130': '3.6',
  'FX|6200': '3.8',
  'FX|8100': '2.8',
  'FX|8120': '3.1',
  'FX|8140': '3.2',
  'FX|8150': '3.6',
  'FX|8170': '3.9',
  'FX|4300': '3.8',
  'FX|4320': '4.0',
  'FX|4350': '4.2',
  'FX|6300': '3.5',
  'FX|6350': '3.9',
  'FX|8300': '3.3',
  'FX|8310': '3.4',
  'FX|8320': '3.5',
  'FX|8350': '4.0',
  'FX|8370': '4.0',
  'FX|9370': '4.4',
  'FX|9590': '4.7',
  'FX|8320E': '3.2',
  'FX|8370E': '3.3',

  // ZEN Desktop CPUs
  '1200': '3.1',
  'Pro 1200': '3.1',
  '1300X': '3.5',
  'Pro 1300': '3.5',
  '1400': '3.2',
  '1500X': '3.5',
  'Pro 1500': '3.5',
  '1600': '3.2',
  '1600X': '3.6',
  'Pro 1600': '3.2',
  '1700': '3.0',
  'Pro 1700': '3.0',
  '1700X': '3.4',
  'Pro 1700X': '3.4',
  '1800X': '3.6',
  '1900X': '3.8',
  '1920': '3.2',
  '1920X': '3.5',
  '1950X': '3.4',

  // ZEN Desktop APUs
  '200GE': '3.2',
  'Pro 200GE': '3.2',
  '220GE': '3.4',
  '240GE': '3.5',
  '3000G': '3.5',
  '300GE': '3.4',
  '3050GE': '3.4',
  '2200G': '3.5',
  'Pro 2200G': '3.5',
  '2200GE': '3.2',
  'Pro 2200GE': '3.2',
  '2400G': '3.6',
  'Pro 2400G': '3.6',
  '2400GE': '3.2',
  'Pro 2400GE': '3.2',

  // ZEN Mobile APUs
  'Pro 200U': '2.3',
  '300U': '2.4',
  '2200U': '2.5',
  '3200U': '2.6',
  '2300U': '2.0',
  'Pro 2300U': '2.0',
  '2500U': '2.0',
  'Pro 2500U': '2.2',
  '2600H': '3.2',
  '2700U': '2.0',
  'Pro 2700U': '2.2',
  '2800H': '3.3',

  // ZEN Server Processors
  '7351': '2.4',
  '7351P': '2.4',
  '7401': '2.0',
  '7401P': '2.0',
  '7551P': '2.0',
  '7551': '2.0',
  '7251': '2.1',
  '7261': '2.5',
  '7281': '2.1',
  '7301': '2.2',
  '7371': '3.1',
  '7451': '2.3',
  '7501': '2.0',
  '7571': '2.2',
  '7601': '2.2',

  // ZEN Embedded Processors
  'V1500B': '2.2',
  'V1780B': '3.35',
  'V1202B': '2.3',
  'V1404I': '2.0',
  'V1605B': '2.0',
  'V1756B': '3.25',
  'V1807B': '3.35',

  '3101': '2.1',
  '3151': '2.7',
  '3201': '1.5',
  '3251': '2.5',
  '3255': '2.5',
  '3301': '2.0',
  '3351': '1.9',
  '3401': '1.85',
  '3451': '2.15',

  // ZEN+ Desktop
  '1200|AF': '3.1',
  '2300X': '3.5',
  '2500X': '3.6',
  '2600': '3.4',
  '2600E': '3.1',
  '1600|AF': '3.2',
  '2600X': '3.6',
  '2700': '3.2',
  '2700E': '2.8',
  'Pro 2700': '3.2',
  '2700X': '3.7',
  'Pro 2700X': '3.6',
  '2920X': '3.5',
  '2950X': '3.5',
  '2970WX': '3.0',
  '2990WX': '3.0',

  // ZEN+ Desktop APU
  'Pro 300GE': '3.4',
  'Pro 3125GE': '3.4',
  '3150G': '3.5',
  'Pro 3150G': '3.5',
  '3150GE': '3.3',
  'Pro 3150GE': '3.3',
  '3200G': '3.6',
  'Pro 3200G': '3.6',
  '3200GE': '3.3',
  'Pro 3200GE': '3.3',
  '3350G': '3.6',
  'Pro 3350G': '3.6',
  '3350GE': '3.3',
  'Pro 3350GE': '3.3',
  '3400G': '3.7',
  'Pro 3400G': '3.7',
  '3400GE': '3.3',
  'Pro 3400GE': '3.3',

  // ZEN+ Mobile
  '3300U': '2.1',
  'PRO 3300U': '2.1',
  '3450U': '2.1',
  '3500U': '2.1',
  'PRO 3500U': '2.1',
  '3500C': '2.1',
  '3550H': '2.1',
  '3580U': '2.1',
  '3700U': '2.3',
  'PRO 3700U': '2.3',
  '3700C': '2.3',
  '3750H': '2.3',
  '3780U': '2.3',

  // ZEN2 Desktop CPUS
  '3100': '3.6',
  '3300X': '3.8',
  '3500': '3.6',
  '3500X': '3.6',
  '3600': '3.6',
  'Pro 3600': '3.6',
  '3600X': '3.8',
  '3600XT': '3.8',
  'Pro 3700': '3.6',
  '3700X': '3.6',
  '3800X': '3.9',
  '3800XT': '3.9',
  '3900': '3.1',
  'Pro 3900': '3.1',
  '3900X': '3.8',
  '3900XT': '3.8',
  '3950X': '3.5',
  '3960X': '3.8',
  '3970X': '3.7',
  '3990X': '2.9',
  '3945WX': '4.0',
  '3955WX': '3.9',
  '3975WX': '3.5',
  '3995WX': '2.7',

  // ZEN2 Desktop APUs
  '4300GE': '3.5',
  'Pro 4300GE': '3.5',
  '4300G': '3.8',
  'Pro 4300G': '3.8',
  '4600GE': '3.3',
  'Pro 4650GE': '3.3',
  '4600G': '3.7',
  'Pro 4650G': '3.7',
  '4700GE': '3.1',
  'Pro 4750GE': '3.1',
  '4700G': '3.6',
  'Pro 4750G': '3.6',
  '4300U': '2.7',
  '4450U': '2.5',
  'Pro 4450U': '2.5',
  '4500U': '2.3',
  '4600U': '2.1',
  'PRO 4650U': '2.1',
  '4680U': '2.1',
  '4600HS': '3.0',
  '4600H': '3.0',
  '4700U': '2.0',
  'PRO 4750U': '1.7',
  '4800U': '1.8',
  '4800HS': '2.9',
  '4800H': '2.9',
  '4900HS': '3.0',
  '4900H': '3.3',
  '5300U': '2.6',
  '5500U': '2.1',
  '5700U': '1.8',

  // ZEN2 - EPYC
  '7232P': '3.1',
  '7302P': '3.0',
  '7402P': '2.8',
  '7502P': '2.5',
  '7702P': '2.0',
  '7252': '3.1',
  '7262': '3.2',
  '7272': '2.9',
  '7282': '2.8',
  '7302': '3.0',
  '7352': '2.3',
  '7402': '2.8',
  '7452': '2.35',
  '7502': '2.5',
  '7532': '2.4',
  '7542': '2.9',
  '7552': '2.2',
  '7642': '2.3',
  '7662': '2.0',
  '7702': '2.0',
  '7742': '2.25',
  '7H12': '2.6',
  '7F32': '3.7',
  '7F52': '3.5',
  '7F72': '3.2',

  // Epyc (Milan)

  '7773X': '2.2',
  '7763': '2.45',
  '7713': '2.0',
  '7713P': '2.0',
  '7663': '2.0',
  '7643': '2.3',
  '7573X': '2.8',
  '75F3': '2.95',
  '7543': '2.8',
  '7543P': '2.8',
  '7513': '2.6',
  '7473X': '2.8',
  '7453': '2.75',
  '74F3': '3.2',
  '7443': '2.85',
  '7443P': '2.85',
  '7413': '2.65',
  '7373X': '3.05',
  '73F3': '3.5',
  '7343': '3.2',
  '7313': '3.0',
  '7313P': '3.0',
  '72F3': '3.7',

  // ZEN3
  '5600X': '3.7',
  '5800X': '3.8',
  '5900X': '3.7',
  '5950X': '3.4',
  '5945WX': '4.1',
  '5955WX': '4.0',
  '5965WX': '3.8',
  '5975WX': '3.6',
  '5995WX': '2.7',

  '7960X': '4.2',
  '7970X': '4.0',
  '7980X': '3.2',

  '7965WX': '4.2',
  '7975WX': '4.0',
  '7985WX': '3.2',
  '7995WX': '2.5',

  // ZEN4
  '9754': '2.25',
  '9754S': '2.25',
  '9734': '2.2',
  '9684X': '2.55',
  '9384X': '3.1',
  '9184X': '3.55',
  '9654P': '2.4',
  '9654': '2.4',
  '9634': '2.25',
  '9554P': '3.1',
  '9554': '3.1',
  '9534': '2.45',
  '9474F': '3.6',
  '9454P': '2.75',
  '9454': '2.75',
  '9374F': '3.85',
  '9354P': '3.25',
  '9354': '3.25',
  '9334': '2.7',
  '9274F': '4.05',
  '9254': '2.9',
  '9224': '2.5',
  '9174F': '4.1',
  '9124': '3.0'
};

const socketTypes = {
  1: 'Other',
  2: 'Unknown',
  3: 'Daughter Board',
  4: 'ZIF Socket',
  5: 'Replacement/Piggy Back',
  6: 'None',
  7: 'LIF Socket',
  8: 'Slot 1',
  9: 'Slot 2',
  10: '370 Pin Socket',
  11: 'Slot A',
  12: 'Slot M',
  13: '423',
  14: 'A (Socket 462)',
  15: '478',
  16: '754',
  17: '940',
  18: '939',
  19: 'mPGA604',
  20: 'LGA771',
  21: 'LGA775',
  22: 'S1',
  23: 'AM2',
  24: 'F (1207)',
  25: 'LGA1366',
  26: 'G34',
  27: 'AM3',
  28: 'C32',
  29: 'LGA1156',
  30: 'LGA1567',
  31: 'PGA988A',
  32: 'BGA1288',
  33: 'rPGA988B',
  34: 'BGA1023',
  35: 'BGA1224',
  36: 'LGA1155',
  37: 'LGA1356',
  38: 'LGA2011',
  39: 'FS1',
  40: 'FS2',
  41: 'FM1',
  42: 'FM2',
  43: 'LGA2011-3',
  44: 'LGA1356-3',
  45: 'LGA1150',
  46: 'BGA1168',
  47: 'BGA1234',
  48: 'BGA1364',
  49: 'AM4',
  50: 'LGA1151',
  51: 'BGA1356',
  52: 'BGA1440',
  53: 'BGA1515',
  54: 'LGA3647-1',
  55: 'SP3',
  56: 'SP3r2',
  57: 'LGA2066',
  58: 'BGA1392',
  59: 'BGA1510',
  60: 'BGA1528',
  61: 'LGA4189',
  62: 'LGA1200',
  63: 'LGA4677',
  64: 'LGA1700',
  65: 'BGA1744',
  66: 'BGA1781',
  67: 'BGA1211',
  68: 'BGA2422',
  69: 'LGA1211',
  70: 'LGA2422',
  71: 'LGA5773',
  72: 'BGA5773',
  73: 'AM5',
  74: 'SP5',
  75: 'SP6',
  76: 'BGA883',
  77: 'BGA1190',
  78: 'BGA4129',
  79: 'LGA4710',
  80: 'LGA7529',
  81: 'BGA1964',
  82: 'BGA1792',
  83: 'BGA2049',
  84: 'BGA2551',
  85: 'LGA1851',
  86: 'BGA2114',
  87: 'BGA2833'
};

const socketTypesByName = {
  'LGA1150': 'i7-5775C i3-4340 i3-4170 G3250 i3-4160T i3-4160 E3-1231 G3258 G3240 i7-4790S i7-4790K i7-4790 i5-4690K i5-4690 i5-4590T i5-4590S i5-4590 i5-4460 i3-4360 i3-4150 G1820 G3420 G3220 i7-4771 i5-4440 i3-4330 i3-4130T i3-4130 E3-1230 i7-4770S i7-4770K i7-4770 i5-4670K i5-4670 i5-4570T i5-4570S i5-4570 i5-4430',
  'LGA1151': 'i9-9900KS E-2288G E-2224 G5420 i9-9900T i9-9900 i7-9700T i7-9700F i7-9700E i7-9700 i5-9600 i5-9500T i5-9500F i5-9500 i5-9400T i3-9350K i3-9300 i3-9100T i3-9100F i3-9100 G4930 i9-9900KF i7-9700KF i5-9600KF i5-9400F i5-9400 i3-9350KF i9-9900K i7-9700K i5-9600K G5500 G5400 i7-8700T i7-8086K i5-8600 i5-8500T i5-8500 i5-8400T i3-8300 i3-8100T G4900 i7-8700K i7-8700 i5-8600K i5-8400 i3-8350K i3-8100 E3-1270 G4600 G4560 i7-7700T i7-7700K i7-7700 i5-7600K i5-7600 i5-7500T i5-7500 i5-7400 i3-7350K i3-7300 i3-7100T i3-7100 G3930 G3900 G4400 i7-6700T i7-6700K i7-6700 i5-6600K i5-6600 i5-6500T i5-6500 i5-6400T i5-6400 i3-6300 i3-6100T i3-6100 E3-1270 E3-1270 T4500 T4400',
  '1155': 'G440 G460 G465 G470 G530T G540T G550T G1610T G1620T G530 G540 G1610 G550 G1620 G555 G1630 i3-2100T i3-2120T i3-3220T i3-3240T i3-3250T i3-2100 i3-2105 i3-2102 i3-3210 i3-3220 i3-2125 i3-2120 i3-3225 i3-2130 i3-3245 i3-3240 i3-3250 i5-3570T i5-2500T i5-2400S i5-2405S i5-2390T i5-3330S i5-2500S i5-3335S i5-2300 i5-3450S i5-3340S i5-3470S i5-3475S i5-3470T i5-2310 i5-3550S i5-2320 i5-3330 i5-3350P i5-3450 i5-2400 i5-3340 i5-3570S i5-2380P i5-2450P i5-3470 i5-2500K i5-3550 i5-2500 i5-3570 i5-3570K i5-2550K i7-3770T i7-2600S i7-3770S i7-2600K i7-2600 i7-3770 i7-3770K i7-2700K G620T G630T G640T G2020T G645T G2100T G2030T G622 G860T G620 G632 G2120T G630 G640 G2010 G840 G2020 G850 G645 G2030 G860 G2120 G870 G2130 G2140 E3-1220L E3-1220L E3-1260L E3-1265L E3-1220 E3-1225 E3-1220 E3-1235 E3-1225 E3-1230 E3-1230 E3-1240 E3-1245 E3-1270 E3-1275 E3-1240 E3-1245 E3-1270 E3-1280 E3-1275 E3-1290 E3-1280 E3-1290'
};

function getSocketTypesByName(str) {
  let result = '';
  for (const key in socketTypesByName) {
    const names = socketTypesByName[key].split(' ');
    names.forEach(element => {
      if (str.indexOf(element) >= 0) {
        result = key;
      }
    });
  }
  return result;
}

function cpuManufacturer(str) {
  let result = str;
  str = str.toLowerCase();

  if (str.indexOf('intel') >= 0) { result = 'Intel'; }
  if (str.indexOf('amd') >= 0) { result = 'AMD'; }
  if (str.indexOf('qemu') >= 0) { result = 'QEMU'; }
  if (str.indexOf('hygon') >= 0) { result = 'Hygon'; }
  if (str.indexOf('centaur') >= 0) { result = 'WinChip/Via'; }
  if (str.indexOf('vmware') >= 0) { result = 'VMware'; }
  if (str.indexOf('Xen') >= 0) { result = 'Xen Hypervisor'; }
  if (str.indexOf('tcg') >= 0) { result = 'QEMU'; }
  if (str.indexOf('apple') >= 0) { result = 'Apple'; }
  if (str.indexOf('sifive') >= 0) { result = 'SiFive'; }
  if (str.indexOf('thead') >= 0) { result = 'T-Head'; }
  if (str.indexOf('andestech') >= 0) { result = 'Andes Technology'; }

  return result;
}

function cpuBrandManufacturer(res) {
  res.brand = res.brand.replace(/\(R\)+/g, '®').replace(/\s+/g, ' ').trim();
  res.brand = res.brand.replace(/\(TM\)+/g, '™').replace(/\s+/g, ' ').trim();
  res.brand = res.brand.replace(/\(C\)+/g, '©').replace(/\s+/g, ' ').trim();
  res.brand = res.brand.replace(/CPU+/g, '').replace(/\s+/g, ' ').trim();
  res.manufacturer = cpuManufacturer(res.brand);

  let parts = res.brand.split(' ');
  parts.shift();
  res.brand = parts.join(' ');
  return res;
}

function getAMDSpeed(brand) {
  let result = '0';
  for (let key in AMDBaseFrequencies) {
    if ({}.hasOwnProperty.call(AMDBaseFrequencies, key)) {
      let parts = key.split('|');
      let found = 0;
      parts.forEach(item => {
        if (brand.indexOf(item) > -1) {
          found++;
        }
      });
      if (found === parts.length) {
        result = AMDBaseFrequencies[key];
      }
    }
  }
  return parseFloat(result);
}

// --------------------------
// CPU - brand, speed

function getCpu() {

  return new Promise((resolve) => {
    process.nextTick(() => {
      const UNKNOWN = 'unknown';
      let result = {
        manufacturer: UNKNOWN,
        brand: UNKNOWN,
        vendor: '',
        family: '',
        model: '',
        stepping: '',
        revision: '',
        voltage: '',
        speed: 0,
        speedMin: 0,
        speedMax: 0,
        governor: '',
        cores: util.cores(),
        physicalCores: util.cores(),
        performanceCores: util.cores(),
        efficiencyCores: 0,
        processors: 1,
        socket: '',
        flags: '',
        virtualization: false,
        cache: {}
      };
      cpuFlags().then(flags => {
        result.flags = flags;
        result.virtualization = flags.indexOf('vmx') > -1 || flags.indexOf('svm') > -1;
        if (_darwin) {
          exec('sysctl machdep.cpu hw.cpufrequency_max hw.cpufrequency_min hw.packages hw.physicalcpu_max hw.ncpu hw.tbfrequency hw.cpufamily hw.cpusubfamily', function (error, stdout) {
            let lines = stdout.toString().split('\n');
            const modelline = util.getValue(lines, 'machdep.cpu.brand_string');
            const modellineParts = modelline.split('@');
            result.brand = modellineParts[0].trim();
            const speed = modellineParts[1] ? modellineParts[1].trim() : '0';
            result.speed = parseFloat(speed.replace(/GHz+/g, ''));
            let tbFrequency = util.getValue(lines, 'hw.tbfrequency') / 1000000000.0;
            tbFrequency = tbFrequency < 0.1 ? tbFrequency * 100 : tbFrequency;
            result.speed = result.speed === 0 ? tbFrequency : result.speed;

            _cpu_speed = result.speed;
            result = cpuBrandManufacturer(result);
            result.speedMin = util.getValue(lines, 'hw.cpufrequency_min') ? (util.getValue(lines, 'hw.cpufrequency_min') / 1000000000.0) : result.speed;
            result.speedMax = util.getValue(lines, 'hw.cpufrequency_max') ? (util.getValue(lines, 'hw.cpufrequency_max') / 1000000000.0) : result.speed;
            result.vendor = util.getValue(lines, 'machdep.cpu.vendor') || 'Apple';
            result.family = util.getValue(lines, 'machdep.cpu.family') || util.getValue(lines, 'hw.cpufamily');
            result.model = util.getValue(lines, 'machdep.cpu.model');
            result.stepping = util.getValue(lines, 'machdep.cpu.stepping') || util.getValue(lines, 'hw.cpusubfamily');
            result.virtualization = true;
            const countProcessors = util.getValue(lines, 'hw.packages');
            const countCores = util.getValue(lines, 'hw.physicalcpu_max');
            const countThreads = util.getValue(lines, 'hw.ncpu');
            if (os.arch() === 'arm64') {
              result.socket = 'SOC';
              try {
                const clusters = execSync('ioreg -c IOPlatformDevice -d 3 -r | grep cluster-type').toString().split('\n');
                const efficiencyCores = clusters.filter(line => line.indexOf('"E"') >= 0).length;
                const performanceCores = clusters.filter(line => line.indexOf('"P"') >= 0).length;
                result.efficiencyCores = efficiencyCores;
                result.performanceCores = performanceCores;
              } catch (e) {
                util.noop();
              }
            }
            if (countProcessors) {
              result.processors = parseInt(countProcessors) || 1;
            }
            if (countCores && countThreads) {
              result.cores = parseInt(countThreads) || util.cores();
              result.physicalCores = parseInt(countCores) || util.cores();
            }
            cpuCache().then((res) => {
              result.cache = res;
              resolve(result);
            });
          });
        }
        if (_linux) {
          let modelline = '';
          let lines = [];
          if (os.cpus()[0] && os.cpus()[0].model) { modelline = os.cpus()[0].model; }
          exec('export LC_ALL=C; lscpu; echo -n "Governor: "; cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null; echo; unset LC_ALL', function (error, stdout) {
            if (!error) {
              lines = stdout.toString().split('\n');
            }
            modelline = util.getValue(lines, 'model name') || modelline;
            modelline = util.getValue(lines, 'bios model name') || modelline;
            modelline = util.cleanString(modelline);
            const modellineParts = modelline.split('@');
            result.brand = modellineParts[0].trim();
            result.speed = modellineParts[1] ? parseFloat(modellineParts[1].trim()) : 0;
            if (result.speed === 0 && (result.brand.indexOf('AMD') > -1 || result.brand.toLowerCase().indexOf('ryzen') > -1)) {
              result.speed = getAMDSpeed(result.brand);
            }
            if (result.speed === 0) {
              const current = getCpuCurrentSpeedSync();
              if (current.avg !== 0) { result.speed = current.avg; }
            }
            _cpu_speed = result.speed;
            result.speedMin = Math.round(parseFloat(util.getValue(lines, 'cpu min mhz').replace(/,/g, '.')) / 10.0) / 100;
            result.speedMax = Math.round(parseFloat(util.getValue(lines, 'cpu max mhz').replace(/,/g, '.')) / 10.0) / 100;

            result = cpuBrandManufacturer(result);
            result.vendor = cpuManufacturer(util.getValue(lines, 'vendor id'));

            result.family = util.getValue(lines, 'cpu family');
            result.model = util.getValue(lines, 'model:');
            result.stepping = util.getValue(lines, 'stepping');
            result.revision = util.getValue(lines, 'cpu revision');
            result.cache.l1d = util.getValue(lines, 'l1d cache');
            if (result.cache.l1d) { result.cache.l1d = parseInt(result.cache.l1d) * (result.cache.l1d.indexOf('M') !== -1 ? 1024 * 1024 : (result.cache.l1d.indexOf('K') !== -1 ? 1024 : 1)); }
            result.cache.l1i = util.getValue(lines, 'l1i cache');
            if (result.cache.l1i) { result.cache.l1i = parseInt(result.cache.l1i) * (result.cache.l1i.indexOf('M') !== -1 ? 1024 * 1024 : (result.cache.l1i.indexOf('K') !== -1 ? 1024 : 1)); }
            result.cache.l2 = util.getValue(lines, 'l2 cache');
            if (result.cache.l2) { result.cache.l2 = parseInt(result.cache.l2) * (result.cache.l2.indexOf('M') !== -1 ? 1024 * 1024 : (result.cache.l2.indexOf('K') !== -1 ? 1024 : 1)); }
            result.cache.l3 = util.getValue(lines, 'l3 cache');
            if (result.cache.l3) { result.cache.l3 = parseInt(result.cache.l3) * (result.cache.l3.indexOf('M') !== -1 ? 1024 * 1024 : (result.cache.l3.indexOf('K') !== -1 ? 1024 : 1)); }

            const threadsPerCore = util.getValue(lines, 'thread(s) per core') || '1';
            const processors = util.getValue(lines, 'socket(s)') || '1';
            const threadsPerCoreInt = parseInt(threadsPerCore, 10); // threads per code (normally only for performance cores)
            const processorsInt = parseInt(processors, 10) || 1;  // number of sockets /  processor units in machine (normally 1)
            const coresPerSocket = parseInt(util.getValue(lines, 'core(s) per socket'), 10); // number of cores (e.g. 16 on i12900)
            result.physicalCores = coresPerSocket ? coresPerSocket * processorsInt : result.cores / threadsPerCoreInt;
            result.performanceCores = threadsPerCoreInt > 1 ? result.cores - result.physicalCores : result.cores;
            result.efficiencyCores = threadsPerCoreInt > 1 ? result.cores - (threadsPerCoreInt * result.performanceCores) : 0;
            result.processors = processorsInt;
            result.governor = util.getValue(lines, 'governor') || '';

            // Test Raspberry
            if (result.vendor === 'ARM' && util.isRaspberry()) {
              const rPIRevision = util.decodePiCpuinfo();
              result.family = result.manufacturer;
              result.manufacturer = rPIRevision.manufacturer;
              result.brand = rPIRevision.processor;
              result.revision = rPIRevision.revisionCode;
              result.socket = 'SOC';
            }

            // Test RISC-V
            if (util.getValue(lines, 'architecture') === 'riscv64') {
              const linesRiscV = fs.readFileSync('/proc/cpuinfo').toString().split('\n');
              const uarch = util.getValue(linesRiscV, 'uarch') || '';
              if (uarch.indexOf(',') > -1) {
                const split = uarch.split(',');
                result.manufacturer = cpuManufacturer(split[0]);
                result.brand = split[1];
              }
            }

            // socket type
            let lines2 = [];
            exec('export LC_ALL=C; dmidecode –t 4 2>/dev/null | grep "Upgrade: Socket"; unset LC_ALL', function (error2, stdout2) {
              lines2 = stdout2.toString().split('\n');
              if (lines2 && lines2.length) {
                result.socket = util.getValue(lines2, 'Upgrade').replace('Socket', '').trim() || result.socket;
              }
              resolve(result);
            });
          });
        }
        if (_freebsd || _openbsd || _netbsd) {
          let modelline = '';
          let lines = [];
          if (os.cpus()[0] && os.cpus()[0].model) { modelline = os.cpus()[0].model; }
          exec('export LC_ALL=C; dmidecode -t 4; dmidecode -t 7 unset LC_ALL', function (error, stdout) {
            let cache = [];
            if (!error) {
              const data = stdout.toString().split('# dmidecode');
              const processor = data.length > 1 ? data[1] : '';
              cache = data.length > 2 ? data[2].split('Cache Information') : [];

              lines = processor.split('\n');
            }
            result.brand = modelline.split('@')[0].trim();
            result.speed = modelline.split('@')[1] ? parseFloat(modelline.split('@')[1].trim()) : 0;
            if (result.speed === 0 && (result.brand.indexOf('AMD') > -1 || result.brand.toLowerCase().indexOf('ryzen') > -1)) {
              result.speed = getAMDSpeed(result.brand);
            }
            if (result.speed === 0) {
              const current = getCpuCurrentSpeedSync();
              if (current.avg !== 0) { result.speed = current.avg; }
            }
            _cpu_speed = result.speed;
            result.speedMin = result.speed;
            result.speedMax = Math.round(parseFloat(util.getValue(lines, 'max speed').replace(/Mhz/g, '')) / 10.0) / 100;

            result = cpuBrandManufacturer(result);
            result.vendor = cpuManufacturer(util.getValue(lines, 'manufacturer'));
            let sig = util.getValue(lines, 'signature');
            sig = sig.split(',');
            for (let i = 0; i < sig.length; i++) {
              sig[i] = sig[i].trim();
            }
            result.family = util.getValue(sig, 'Family', ' ', true);
            result.model = util.getValue(sig, 'Model', ' ', true);
            result.stepping = util.getValue(sig, 'Stepping', ' ', true);
            result.revision = '';
            const voltage = parseFloat(util.getValue(lines, 'voltage'));
            result.voltage = isNaN(voltage) ? '' : voltage.toFixed(2);
            for (let i = 0; i < cache.length; i++) {
              lines = cache[i].split('\n');
              let cacheType = util.getValue(lines, 'Socket Designation').toLowerCase().replace(' ', '-').split('-');
              cacheType = cacheType.length ? cacheType[0] : '';
              const sizeParts = util.getValue(lines, 'Installed Size').split(' ');
              let size = parseInt(sizeParts[0], 10);
              const unit = sizeParts.length > 1 ? sizeParts[1] : 'kb';
              size = size * (unit === 'kb' ? 1024 : (unit === 'mb' ? 1024 * 1024 : (unit === 'gb' ? 1024 * 1024 * 1024 : 1)));
              if (cacheType) {
                if (cacheType === 'l1') {
                  result.cache[cacheType + 'd'] = size / 2;
                  result.cache[cacheType + 'i'] = size / 2;
                } else {
                  result.cache[cacheType] = size;
                }
              }
            }
            // socket type
            result.socket = util.getValue(lines, 'Upgrade').replace('Socket', '').trim();
            // # threads / # cores
            const threadCount = util.getValue(lines, 'thread count').trim();
            const coreCount = util.getValue(lines, 'core count').trim();
            if (coreCount && threadCount) {
              result.cores = parseInt(threadCount, 10);
              result.physicalCores = parseInt(coreCount, 10);
            }
            resolve(result);
          });
        }
        if (_sunos) {
          resolve(result);
        }
        if (_windows) {
          try {
            const workload = [];
            workload.push(util.powerShell('Get-CimInstance Win32_processor | select Name, Revision, L2CacheSize, L3CacheSize, Manufacturer, MaxClockSpeed, Description, UpgradeMethod, Caption, NumberOfLogicalProcessors, NumberOfCores | fl'));
            workload.push(util.powerShell('Get-CimInstance Win32_CacheMemory | select CacheType,InstalledSize,Level | fl'));
            workload.push(util.powerShell('(Get-CimInstance Win32_ComputerSystem).HypervisorPresent'));

            Promise.all(
              workload
            ).then((data) => {
              let lines = data[0].split('\r\n');
              let name = util.getValue(lines, 'name', ':') || '';
              if (name.indexOf('@') >= 0) {
                result.brand = name.split('@')[0].trim();
                result.speed = name.split('@')[1] ? parseFloat(name.split('@')[1].trim()) : 0;
                _cpu_speed = result.speed;
              } else {
                result.brand = name.trim();
                result.speed = 0;
              }
              result = cpuBrandManufacturer(result);
              result.revision = util.getValue(lines, 'revision', ':');
              result.vendor = util.getValue(lines, 'manufacturer', ':');
              result.speedMax = Math.round(parseFloat(util.getValue(lines, 'maxclockspeed', ':').replace(/,/g, '.')) / 10.0) / 100;
              if (result.speed === 0 && (result.brand.indexOf('AMD') > -1 || result.brand.toLowerCase().indexOf('ryzen') > -1)) {
                result.speed = getAMDSpeed(result.brand);
              }
              if (result.speed === 0) {
                result.speed = result.speedMax;
              }
              result.speedMin = result.speed;

              let description = util.getValue(lines, 'description', ':').split(' ');
              for (let i = 0; i < description.length; i++) {
                if (description[i].toLowerCase().startsWith('family') && (i + 1) < description.length && description[i + 1]) {
                  result.family = description[i + 1];
                }
                if (description[i].toLowerCase().startsWith('model') && (i + 1) < description.length && description[i + 1]) {
                  result.model = description[i + 1];
                }
                if (description[i].toLowerCase().startsWith('stepping') && (i + 1) < description.length && description[i + 1]) {
                  result.stepping = description[i + 1];
                }
              }
              // socket type
              const socketId = util.getValue(lines, 'UpgradeMethod', ':');
              if (socketTypes[socketId]) {
                result.socket = socketTypes[socketId];
              }
              const socketByName = getSocketTypesByName(name);
              if (socketByName) {
                result.socket = socketByName;
              }
              // # threads / # cores
              const countProcessors = util.countLines(lines, 'Caption');
              const countThreads = util.getValue(lines, 'NumberOfLogicalProcessors', ':');
              const countCores = util.getValue(lines, 'NumberOfCores', ':');
              if (countProcessors) {
                result.processors = parseInt(countProcessors) || 1;
              }
              if (countCores && countThreads) {
                result.cores = parseInt(countThreads) || util.cores();
                result.physicalCores = parseInt(countCores) || util.cores();
              }
              if (countProcessors > 1) {
                result.cores = result.cores * countProcessors;
                result.physicalCores = result.physicalCores * countProcessors;
              }
              result.cache = parseWinCache(data[0], data[1]);
              const hyperv = data[2] ? data[2].toString().toLowerCase() : '';
              result.virtualization = hyperv.indexOf('true') !== -1;

              resolve(result);
            });
          } catch (e) {
            resolve(result);
          }
        }
      });
    });
  });
}

// --------------------------
// CPU - Processor Data

function cpu(callback) {

  return new Promise((resolve) => {
    process.nextTick(() => {
      getCpu().then(result => {
        if (callback) { callback(result); }
        resolve(result);
      });
    });
  });
}

exports.cpu = cpu;

// --------------------------
// CPU - current speed - in GHz

function getCpuCurrentSpeedSync() {

  let cpus = os.cpus();
  let minFreq = 999999999;
  let maxFreq = 0;
  let avgFreq = 0;
  let cores = [];
  let speeds = [];

  if (cpus && cpus.length && cpus[0].hasOwnProperty('speed')) {
    for (let i in cpus) {
      speeds.push(cpus[i].speed > 100 ? (cpus[i].speed + 1) / 1000 : cpus[i].speed / 10);
    }
  } else if (_linux) {
    try {
      const speedStrings = execSync('cat /proc/cpuinfo | grep "cpu MHz" | cut -d " " -f 3', util.execOptsLinux).toString().split('\n').filter((line) => line.length > 0);
      for (let i in speedStrings) {
        speeds.push(Math.floor(parseInt(speedStrings[i], 10) / 10) / 100);
      }
    } catch {
      util.noop();
    }
  }

  if (speeds && speeds.length) {
    try {
      for (let i in speeds) {
        avgFreq = avgFreq + speeds[i];
        if (speeds[i] > maxFreq) { maxFreq = speeds[i]; }
        if (speeds[i] < minFreq) { minFreq = speeds[i]; }
        cores.push(parseFloat(speeds[i].toFixed(2)));
      }
      avgFreq = avgFreq / speeds.length;
      return {
        min: parseFloat(minFreq.toFixed(2)),
        max: parseFloat(maxFreq.toFixed(2)),
        avg: parseFloat((avgFreq).toFixed(2)),
        cores: cores
      };
    } catch (e) {
      return {
        min: 0,
        max: 0,
        avg: 0,
        cores: cores
      };
    }
  } else {
    return {
      min: 0,
      max: 0,
      avg: 0,
      cores: cores
    };
  }
}

function cpuCurrentSpeed(callback) {

  return new Promise((resolve) => {
    process.nextTick(() => {
      let result = getCpuCurrentSpeedSync();
      if (result.avg === 0 && _cpu_speed !== 0) {
        const currCpuSpeed = parseFloat(_cpu_speed);
        result = {
          min: currCpuSpeed,
          max: currCpuSpeed,
          avg: currCpuSpeed,
          cores: []
        };
      }
      if (callback) { callback(result); }
      resolve(result);
    });
  });
}

exports.cpuCurrentSpeed = cpuCurrentSpeed;

// --------------------------
// CPU - temperature
// if sensors are installed

function cpuTemperature(callback) {

  return new Promise((resolve) => {
    process.nextTick(() => {
      let result = {
        main: null,
        cores: [],
        max: null,
        socket: [],
        chipset: null
      };
      if (_linux) {
        // CPU Chipset, Socket
        try {
          const cmd = 'cat /sys/class/thermal/thermal_zone*/type  2>/dev/null; echo "-----"; cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null;';
          const parts = execSync(cmd, util.execOptsLinux).toString().split('-----\n');
          if (parts.length === 2) {
            const lines = parts[0].split('\n');
            const lines2 = parts[1].split('\n');
            for (let i = 0; i < lines.length; i++) {
              const line = lines[i].trim();
              if (line.startsWith('acpi') && lines2[i]) {
                result.socket.push(Math.round(parseInt(lines2[i], 10) / 100) / 10);
              }
              if (line.startsWith('pch') && lines2[i]) {
                result.chipset = Math.round(parseInt(lines2[i], 10) / 100) / 10;
              }
            }
          }
        } catch (e) {
          util.noop();
        }

        const cmd = 'for mon in /sys/class/hwmon/hwmon*; do for label in "$mon"/temp*_label; do if [ -f $label ]; then value=${label%_*}_input; echo $(cat "$label")___$(cat "$value"); fi; done; done;';
        try {
          exec(cmd, function (error, stdout) {
            stdout = stdout.toString();
            const tdiePos = stdout.toLowerCase().indexOf('tdie');
            if (tdiePos !== -1) {
              stdout = stdout.substring(tdiePos);
            }
            let lines = stdout.split('\n');
            let tctl = 0;
            lines.forEach(line => {
              const parts = line.split('___');
              const label = parts[0];
              const value = parts.length > 1 && parts[1] ? parts[1] : '0';
              if (value && label && label.toLowerCase() === 'tctl') {
                tctl = result.main = Math.round(parseInt(value, 10) / 100) / 10;
              }
              if (value && (label === undefined || (label && label.toLowerCase().startsWith('core')))) {
                result.cores.push(Math.round(parseInt(value, 10) / 100) / 10);
              } else if (value && label && result.main === null && (label.toLowerCase().indexOf('package') >= 0 || label.toLowerCase().indexOf('physical') >= 0 || label.toLowerCase() === 'tccd1')) {
                result.main = Math.round(parseInt(value, 10) / 100) / 10;
              }
            });
            if (tctl && result.main === null) {
              result.main = tctl;
            }

            if (result.cores.length > 0) {
              if (result.main === null) {
                result.main = Math.round(result.cores.reduce((a, b) => a + b, 0) / result.cores.length);
              }
              let maxtmp = Math.max.apply(Math, result.cores);
              result.max = (maxtmp > result.main) ? maxtmp : result.main;
            }
            if (result.main !== null) {
              if (result.max === null) {
                result.max = result.main;
              }
              if (callback) { callback(result); }
              resolve(result);
              return;
            }
            exec('sensors', function (error, stdout) {
              if (!error) {
                let lines = stdout.toString().split('\n');
                let tdieTemp = null;
                let newSectionStarts = true;
                let section = '';
                lines.forEach(function (line) {
                  // determine section
                  if (line.trim() === '') {
                    newSectionStarts = true;
                  } else if (newSectionStarts) {
                    if (line.trim().toLowerCase().startsWith('acpi')) { section = 'acpi'; }
                    if (line.trim().toLowerCase().startsWith('pch')) { section = 'pch'; }
                    if (line.trim().toLowerCase().startsWith('core')) { section = 'core'; }
                    newSectionStarts = false;
                  }
                  let regex = /[+-]([^°]*)/g;
                  let temps = line.match(regex);
                  let firstPart = line.split(':')[0].toUpperCase();
                  if (section === 'acpi') {
                    // socket temp
                    if (firstPart.indexOf('TEMP') !== -1) {
                      result.socket.push(parseFloat(temps));
                    }
                  } else if (section === 'pch') {
                    // chipset temp
                    if (firstPart.indexOf('TEMP') !== -1 && !result.chipset) {
                      result.chipset = parseFloat(temps);
                    }
                  }
                  // cpu temp
                  if (firstPart.indexOf('PHYSICAL') !== -1 || firstPart.indexOf('PACKAGE') !== -1) {
                    result.main = parseFloat(temps);
                  }
                  if (firstPart.indexOf('CORE ') !== -1) {
                    result.cores.push(parseFloat(temps));
                  }
                  if (firstPart.indexOf('TDIE') !== -1 && tdieTemp === null) {
                    tdieTemp = parseFloat(temps);
                  }
                });
                if (result.cores.length > 0) {
                  result.main = Math.round(result.cores.reduce((a, b) => a + b, 0) / result.cores.length);
                  let maxtmp = Math.max.apply(Math, result.cores);
                  result.max = (maxtmp > result.main) ? maxtmp : result.main;
                } else {
                  if (result.main === null && tdieTemp !== null) {
                    result.main = tdieTemp;
                    result.max = tdieTemp;
                  }
                }
                if (result.main !== null || result.max !== null) {
                  if (callback) { callback(result); }
                  resolve(result);
                  return;
                }
              }
              fs.stat('/sys/class/thermal/thermal_zone0/temp', function (err) {
                if (err === null) {
                  fs.readFile('/sys/class/thermal/thermal_zone0/temp', function (error, stdout) {
                    if (!error) {
                      let lines = stdout.toString().split('\n');
                      if (lines.length > 0) {
                        result.main = parseFloat(lines[0]) / 1000.0;
                        result.max = result.main;
                      }
                    }
                    if (callback) { callback(result); }
                    resolve(result);
                  });
                } else {
                  exec('/opt/vc/bin/vcgencmd measure_temp', function (error, stdout) {
                    if (!error) {
                      let lines = stdout.toString().split('\n');
                      if (lines.length > 0 && lines[0].indexOf('=')) {
                        result.main = parseFloat(lines[0].split('=')[1]);
                        result.max = result.main;
                      }
                    }
                    if (callback) { callback(result); }
                    resolve(result);
                  });
                }
              });
            });
          });
        } catch (er) {
          if (callback) { callback(result); }
          resolve(result);
        }
      }
      if (_freebsd || _openbsd || _netbsd) {
        exec('sysctl dev.cpu | grep temp', function (error, stdout) {
          if (!error) {
            let lines = stdout.toString().split('\n');
            let sum = 0;
            lines.forEach(function (line) {
              const parts = line.split(':');
              if (parts.length > 1) {
                const temp = parseFloat(parts[1].replace(',', '.'));
                if (temp > result.max) { result.max = temp; }
                sum = sum + temp;
                result.cores.push(temp);
              }
            });
            if (result.cores.length) {
              result.main = Math.round(sum / result.cores.length * 100) / 100;
            }
          }
          if (callback) { callback(result); }
          resolve(result);
        });
      }
      if (_darwin) {
        let osxTemp = null;
        try {
          osxTemp = require('osx-temperature-sensor');
        } catch (er) {
          osxTemp = null;
        }
        if (osxTemp) {
          result = osxTemp.cpuTemperature();
          // round to 2 digits
          if (result.main) {
            result.main = Math.round(result.main * 100) / 100;
          }
          if (result.max) {
            result.max = Math.round(result.max * 100) / 100;
          }
          if (result.cores && result.cores.length) {
            for (let i = 0; i < result.cores.length; i++) {
              result.cores[i] = Math.round(result.cores[i] * 100) / 100;
            }
          }
        }

        if (callback) { callback(result); }
        resolve(result);
      }
      if (_sunos) {
        if (callback) { callback(result); }
        resolve(result);
      }
      if (_windows) {
        try {
          util.powerShell('Get-CimInstance MSAcpi_ThermalZoneTemperature -Namespace "root/wmi" | Select CurrentTemperature').then((stdout, error) => {
            if (!error) {
              let sum = 0;
              let lines = stdout.split('\r\n').filter(line => line.trim() !== '').filter((line, idx) => idx > 0);
              lines.forEach(function (line) {
                let value = (parseInt(line, 10) - 2732) / 10;
                if (!isNaN(value)) {
                  sum = sum + value;
                  if (value > result.max) { result.max = value; }
                  result.cores.push(value);
                }
              });
              if (result.cores.length) {
                result.main = sum / result.cores.length;
              }
            }
            if (callback) { callback(result); }
            resolve(result);
          });
        } catch (e) {
          if (callback) { callback(result); }
          resolve(result);
        }
      }
    });
  });
}

exports.cpuTemperature = cpuTemperature;

// --------------------------
// CPU Flags

function cpuFlags(callback) {

  return new Promise((resolve) => {
    process.nextTick(() => {
      let result = '';
      if (_windows) {
        try {
          exec('reg query "HKEY_LOCAL_MACHINE\\HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0" /v FeatureSet', util.execOptsWin, function (error, stdout) {
            if (!error) {
              let flag_hex = stdout.split('0x').pop().trim();
              let flag_bin_unpadded = parseInt(flag_hex, 16).toString(2);
              let flag_bin = '0'.repeat(32 - flag_bin_unpadded.length) + flag_bin_unpadded;
              // empty flags are the reserved fields in the CPUID feature bit list
              // as found on wikipedia:
              // https://en.wikipedia.org/wiki/CPUID
              let all_flags = [
                'fpu', 'vme', 'de', 'pse', 'tsc', 'msr', 'pae', 'mce', 'cx8', 'apic',
                '', 'sep', 'mtrr', 'pge', 'mca', 'cmov', 'pat', 'pse-36', 'psn', 'clfsh',
                '', 'ds', 'acpi', 'mmx', 'fxsr', 'sse', 'sse2', 'ss', 'htt', 'tm', 'ia64', 'pbe'
              ];
              for (let f = 0; f < all_flags.length; f++) {
                if (flag_bin[f] === '1' && all_flags[f] !== '') {
                  result += ' ' + all_flags[f];
                }
              }
              result = result.trim().toLowerCase();
            }
            if (callback) { callback(result); }
            resolve(result);
          });
        } catch (e) {
          if (callback) { callback(result); }
          resolve(result);
        }
      }
      if (_linux) {
        try {

          exec('export LC_ALL=C; lscpu; unset LC_ALL', function (error, stdout) {
            if (!error) {
              let lines = stdout.toString().split('\n');
              lines.forEach(function (line) {
                if (line.split(':')[0].toUpperCase().indexOf('FLAGS') !== -1) {
                  result = line.split(':')[1].trim().toLowerCase();
                }
              });
            }
            if (!result) {
              fs.readFile('/proc/cpuinfo', function (error, stdout) {
                if (!error) {
                  let lines = stdout.toString().split('\n');
                  result = util.getValue(lines, 'features', ':', true).toLowerCase();
                }
                if (callback) { callback(result); }
                resolve(result);
              });
            } else {
              if (callback) { callback(result); }
              resolve(result);
            }
          });
        } catch (e) {
          if (callback) { callback(result); }
          resolve(result);
        }
      }
      if (_freebsd || _openbsd || _netbsd) {
        exec('export LC_ALL=C; dmidecode -t 4 2>/dev/null; unset LC_ALL', function (error, stdout) {
          let flags = [];
          if (!error) {
            let parts = stdout.toString().split('\tFlags:');
            const lines = parts.length > 1 ? parts[1].split('\tVersion:')[0].split('\n') : [];
            lines.forEach(function (line) {
              let flag = (line.indexOf('(') ? line.split('(')[0].toLowerCase() : '').trim().replace(/\t/g, '');
              if (flag) {
                flags.push(flag);
              }
            });
          }
          result = flags.join(' ').trim().toLowerCase();
          if (callback) { callback(result); }
          resolve(result);
        });
      }
      if (_darwin) {
        exec('sysctl machdep.cpu.features', function (error, stdout) {
          if (!error) {
            let lines = stdout.toString().split('\n');
            if (lines.length > 0 && lines[0].indexOf('machdep.cpu.features:') !== -1) {
              result = lines[0].split(':')[1].trim().toLowerCase();
            }
          }
          if (callback) { callback(result); }
          resolve(result);
        });
      }
      if (_sunos) {
        if (callback) { callback(result); }
        resolve(result);
      }
    });
  });
}

exports.cpuFlags = cpuFlags;

// --------------------------
// CPU Cache

function cpuCache(callback) {

  return new Promise((resolve) => {
    process.nextTick(() => {

      let result = {
        l1d: null,
        l1i: null,
        l2: null,
        l3: null,
      };
      if (_linux) {
        try {
          exec('export LC_ALL=C; lscpu; unset LC_ALL', function (error, stdout) {
            if (!error) {
              let lines = stdout.toString().split('\n');
              lines.forEach(function (line) {
                let parts = line.split(':');
                if (parts[0].toUpperCase().indexOf('L1D CACHE') !== -1) {
                  result.l1d = parseInt(parts[1].trim()) * (parts[1].indexOf('M') !== -1 ? 1024 * 1024 : (parts[1].indexOf('K') !== -1 ? 1024 : 1));
                }
                if (parts[0].toUpperCase().indexOf('L1I CACHE') !== -1) {
                  result.l1i = parseInt(parts[1].trim()) * (parts[1].indexOf('M') !== -1 ? 1024 * 1024 : (parts[1].indexOf('K') !== -1 ? 1024 : 1));
                }
                if (parts[0].toUpperCase().indexOf('L2 CACHE') !== -1) {
                  result.l2 = parseInt(parts[1].trim()) * (parts[1].indexOf('M') !== -1 ? 1024 * 1024 : (parts[1].indexOf('K') !== -1 ? 1024 : 1));
                }
                if (parts[0].toUpperCase().indexOf('L3 CACHE') !== -1) {
                  result.l3 = parseInt(parts[1].trim()) * (parts[1].indexOf('M') !== -1 ? 1024 * 1024 : (parts[1].indexOf('K') !== -1 ? 1024 : 1));
                }
              });
            }
            if (callback) { callback(result); }
            resolve(result);
          });
        } catch (e) {
          if (callback) { callback(result); }
          resolve(result);
        }
      }
      if (_freebsd || _openbsd || _netbsd) {
        exec('export LC_ALL=C; dmidecode -t 7 2>/dev/null; unset LC_ALL', function (error, stdout) {
          let cache = [];
          if (!error) {
            const data = stdout.toString();
            cache = data.split('Cache Information');
            cache.shift();
          }
          for (let i = 0; i < cache.length; i++) {
            const lines = cache[i].split('\n');
            let cacheType = util.getValue(lines, 'Socket Designation').toLowerCase().replace(' ', '-').split('-');
            cacheType = cacheType.length ? cacheType[0] : '';
            const sizeParts = util.getValue(lines, 'Installed Size').split(' ');
            let size = parseInt(sizeParts[0], 10);
            const unit = sizeParts.length > 1 ? sizeParts[1] : 'kb';
            size = size * (unit === 'kb' ? 1024 : (unit === 'mb' ? 1024 * 1024 : (unit === 'gb' ? 1024 * 1024 * 1024 : 1)));
            if (cacheType) {
              if (cacheType === 'l1') {
                result.cache[cacheType + 'd'] = size / 2;
                result.cache[cacheType + 'i'] = size / 2;
              } else {
                result.cache[cacheType] = size;
              }
            }
          }
          if (callback) { callback(result); }
          resolve(result);
        });
      }
      if (_darwin) {
        exec('sysctl hw.l1icachesize hw.l1dcachesize hw.l2cachesize hw.l3cachesize', function (error, stdout) {
          if (!error) {
            let lines = stdout.toString().split('\n');
            lines.forEach(function (line) {
              let parts = line.split(':');
              if (parts[0].toLowerCase().indexOf('hw.l1icachesize') !== -1) {
                result.l1d = parseInt(parts[1].trim()) * (parts[1].indexOf('K') !== -1 ? 1024 : 1);
              }
              if (parts[0].toLowerCase().indexOf('hw.l1dcachesize') !== -1) {
                result.l1i = parseInt(parts[1].trim()) * (parts[1].indexOf('K') !== -1 ? 1024 : 1);
              }
              if (parts[0].toLowerCase().indexOf('hw.l2cachesize') !== -1) {
                result.l2 = parseInt(parts[1].trim()) * (parts[1].indexOf('K') !== -1 ? 1024 : 1);
              }
              if (parts[0].toLowerCase().indexOf('hw.l3cachesize') !== -1) {
                result.l3 = parseInt(parts[1].trim()) * (parts[1].indexOf('K') !== -1 ? 1024 : 1);
              }
            });
          }
          if (callback) { callback(result); }
          resolve(result);
        });
      }
      if (_sunos) {
        if (callback) { callback(result); }
        resolve(result);
      }
      if (_windows) {
        try {
          const workload = [];
          workload.push(util.powerShell('Get-CimInstance Win32_processor | select L2CacheSize, L3CacheSize | fl'));
          workload.push(util.powerShell('Get-CimInstance Win32_CacheMemory | select CacheType,InstalledSize,Level | fl'));

          Promise.all(
            workload
          ).then((data) => {
            result = parseWinCache(data[0], data[1]);

            if (callback) { callback(result); }
            resolve(result);
          });
        } catch (e) {
          if (callback) { callback(result); }
          resolve(result);
        }
      }
    });
  });
}

function parseWinCache(linesProc, linesCache) {
  let result = {
    l1d: null,
    l1i: null,
    l2: null,
    l3: null,
  };

  // Win32_processor
  let lines = linesProc.split('\r\n');
  result.l1d = 0;
  result.l1i = 0;
  result.l2 = util.getValue(lines, 'l2cachesize', ':');
  result.l3 = util.getValue(lines, 'l3cachesize', ':');
  if (result.l2) { result.l2 = parseInt(result.l2, 10) * 1024; } else { result.l2 = 0; }
  if (result.l3) { result.l3 = parseInt(result.l3, 10) * 1024; } else { result.l3 = 0; }

  // Win32_CacheMemory
  const parts = linesCache.split(/\n\s*\n/);
  let l1i = 0;
  let l1d = 0;
  let l2 = 0;
  parts.forEach(function (part) {
    const lines = part.split('\r\n');
    const cacheType = util.getValue(lines, 'CacheType');
    const level = util.getValue(lines, 'Level');
    const installedSize = util.getValue(lines, 'InstalledSize');
    // L1 Instructions
    if (level === '3' && cacheType === '3') {
      result.l1i = result.l1i + parseInt(installedSize, 10) * 1024;
    }
    // L1 Data
    if (level === '3' && cacheType === '4') {
      result.l1d = result.l1d + parseInt(installedSize, 10) * 1024;
    }
    // L1 all
    if (level === '3' && cacheType === '5') {
      l1i = parseInt(installedSize, 10) / 2;
      l1d = parseInt(installedSize, 10) / 2;
    }
    // L2
    if (level === '4' && cacheType === '5') {
      l2 = l2 + parseInt(installedSize, 10) * 1024;
    }
  });
  if (!result.l1i && !result.l1d) {
    result.l1i = l1i;
    result.l1d = l1d;
  }
  if (l2) {
    result.l2 = l2;
  }
  return result;
}

exports.cpuCache = cpuCache;

// --------------------------
// CPU - current load - in %

function getLoad() {

  return new Promise((resolve) => {
    process.nextTick(() => {
      let loads = os.loadavg().map(function (x) { return x / util.cores(); });
      let avgLoad = parseFloat((Math.max.apply(Math, loads)).toFixed(2));
      let result = {};

      let now = Date.now() - _current_cpu.ms;
      if (now >= 200) {
        _current_cpu.ms = Date.now();
        const cpus = os.cpus().map(function (cpu) {
          cpu.times.steal = 0;
          cpu.times.guest = 0;
          return cpu;
        });
        let totalUser = 0;
        let totalSystem = 0;
        let totalNice = 0;
        let totalIrq = 0;
        let totalIdle = 0;
        let totalSteal = 0;
        let totalGuest = 0;
        let cores = [];
        _corecount = (cpus && cpus.length) ? cpus.length : 0;

        // linux: try to get other cpu stats
        if (_linux) {
          try {
            const lines = execSync('cat /proc/stat 2>/dev/null | grep cpu', util.execOptsLinux).toString().split('\n');
            if (lines.length > 1) {
              lines.shift();
              if (lines.length === cpus.length) {
                for (let i = 0; i < lines.length; i++) {
                  let parts = lines[i].split(' ');
                  if (parts.length >= 10) {
                    const steal = parseFloat(parts[8]) || 0;
                    const guest = parseFloat(parts[9]) || 0;
                    cpus[i].times.steal = steal;
                    cpus[i].times.guest = guest;
                  }
                }
              }
            }
          } catch (e) {
            util.noop();
          }
        }

        for (let i = 0; i < _corecount; i++) {
          const cpu = cpus[i].times;
          totalUser += cpu.user;
          totalSystem += cpu.sys;
          totalNice += cpu.nice;
          totalIdle += cpu.idle;
          totalIrq += cpu.irq;
          totalSteal += cpu.steal || 0;
          totalGuest += cpu.guest || 0;
          let tmpTick = (_cpus && _cpus[i] && _cpus[i].totalTick ? _cpus[i].totalTick : 0);
          let tmpLoad = (_cpus && _cpus[i] && _cpus[i].totalLoad ? _cpus[i].totalLoad : 0);
          let tmpUser = (_cpus && _cpus[i] && _cpus[i].user ? _cpus[i].user : 0);
          let tmpSystem = (_cpus && _cpus[i] && _cpus[i].sys ? _cpus[i].sys : 0);
          let tmpNice = (_cpus && _cpus[i] && _cpus[i].nice ? _cpus[i].nice : 0);
          let tmpIdle = (_cpus && _cpus[i] && _cpus[i].idle ? _cpus[i].idle : 0);
          let tmpIrq = (_cpus && _cpus[i] && _cpus[i].irq ? _cpus[i].irq : 0);
          let tmpSteal = (_cpus && _cpus[i] && _cpus[i].steal ? _cpus[i].steal : 0);
          let tmpGuest = (_cpus && _cpus[i] && _cpus[i].guest ? _cpus[i].guest : 0);
          _cpus[i] = cpu;
          _cpus[i].totalTick = _cpus[i].user + _cpus[i].sys + _cpus[i].nice + _cpus[i].irq + _cpus[i].steal + _cpus[i].guest + _cpus[i].idle;
          _cpus[i].totalLoad = _cpus[i].user + _cpus[i].sys + _cpus[i].nice + _cpus[i].irq + _cpus[i].steal + _cpus[i].guest;
          _cpus[i].currentTick = _cpus[i].totalTick - tmpTick;
          _cpus[i].load = (_cpus[i].totalLoad - tmpLoad);
          _cpus[i].loadUser = (_cpus[i].user - tmpUser);
          _cpus[i].loadSystem = (_cpus[i].sys - tmpSystem);
          _cpus[i].loadNice = (_cpus[i].nice - tmpNice);
          _cpus[i].loadIdle = (_cpus[i].idle - tmpIdle);
          _cpus[i].loadIrq = (_cpus[i].irq - tmpIrq);
          _cpus[i].loadSteal = (_cpus[i].steal - tmpSteal);
          _cpus[i].loadGuest = (_cpus[i].guest - tmpGuest);
          cores[i] = {};
          cores[i].load = _cpus[i].load / _cpus[i].currentTick * 100;
          cores[i].loadUser = _cpus[i].loadUser / _cpus[i].currentTick * 100;
          cores[i].loadSystem = _cpus[i].loadSystem / _cpus[i].currentTick * 100;
          cores[i].loadNice = _cpus[i].loadNice / _cpus[i].currentTick * 100;
          cores[i].loadIdle = _cpus[i].loadIdle / _cpus[i].currentTick * 100;
          cores[i].loadIrq = _cpus[i].loadIrq / _cpus[i].currentTick * 100;
          cores[i].loadSteal = _cpus[i].loadSteal / _cpus[i].currentTick * 100;
          cores[i].loadGuest = _cpus[i].loadGuest / _cpus[i].currentTick * 100;
          cores[i].rawLoad = _cpus[i].load;
          cores[i].rawLoadUser = _cpus[i].loadUser;
          cores[i].rawLoadSystem = _cpus[i].loadSystem;
          cores[i].rawLoadNice = _cpus[i].loadNice;
          cores[i].rawLoadIdle = _cpus[i].loadIdle;
          cores[i].rawLoadIrq = _cpus[i].loadIrq;
          cores[i].rawLoadSteal = _cpus[i].loadSteal;
          cores[i].rawLoadGuest = _cpus[i].loadGuest;
        }
        let totalTick = totalUser + totalSystem + totalNice + totalIrq + totalSteal + totalGuest + totalIdle;
        let totalLoad = totalUser + totalSystem + totalNice + totalIrq + totalSteal + totalGuest;
        let currentTick = totalTick - _current_cpu.tick;
        result = {
          avgLoad: avgLoad,
          currentLoad: (totalLoad - _current_cpu.load) / currentTick * 100,
          currentLoadUser: (totalUser - _current_cpu.user) / currentTick * 100,
          currentLoadSystem: (totalSystem - _current_cpu.system) / currentTick * 100,
          currentLoadNice: (totalNice - _current_cpu.nice) / currentTick * 100,
          currentLoadIdle: (totalIdle - _current_cpu.idle) / currentTick * 100,
          currentLoadIrq: (totalIrq - _current_cpu.irq) / currentTick * 100,
          currentLoadSteal: (totalSteal - _current_cpu.steal) / currentTick * 100,
          currentLoadGuest: (totalGuest - _current_cpu.guest) / currentTick * 100,
          rawCurrentLoad: (totalLoad - _current_cpu.load),
          rawCurrentLoadUser: (totalUser - _current_cpu.user),
          rawCurrentLoadSystem: (totalSystem - _current_cpu.system),
          rawCurrentLoadNice: (totalNice - _current_cpu.nice),
          rawCurrentLoadIdle: (totalIdle - _current_cpu.idle),
          rawCurrentLoadIrq: (totalIrq - _current_cpu.irq),
          rawCurrentLoadSteal: (totalSteal - _current_cpu.steal),
          rawCurrentLoadGuest: (totalGuest - _current_cpu.guest),
          cpus: cores
        };
        _current_cpu = {
          user: totalUser,
          nice: totalNice,
          system: totalSystem,
          idle: totalIdle,
          irq: totalIrq,
          steal: totalSteal,
          guest: totalGuest,
          tick: totalTick,
          load: totalLoad,
          ms: _current_cpu.ms,
          currentLoad: result.currentLoad,
          currentLoadUser: result.currentLoadUser,
          currentLoadSystem: result.currentLoadSystem,
          currentLoadNice: result.currentLoadNice,
          currentLoadIdle: result.currentLoadIdle,
          currentLoadIrq: result.currentLoadIrq,
          currentLoadSteal: result.currentLoadSteal,
          currentLoadGuest: result.currentLoadGuest,
          rawCurrentLoad: result.rawCurrentLoad,
          rawCurrentLoadUser: result.rawCurrentLoadUser,
          rawCurrentLoadSystem: result.rawCurrentLoadSystem,
          rawCurrentLoadNice: result.rawCurrentLoadNice,
          rawCurrentLoadIdle: result.rawCurrentLoadIdle,
          rawCurrentLoadIrq: result.rawCurrentLoadIrq,
          rawCurrentLoadSteal: result.rawCurrentLoadSteal,
          rawCurrentLoadGuest: result.rawCurrentLoadGuest,
        };
      } else {
        let cores = [];
        for (let i = 0; i < _corecount; i++) {
          cores[i] = {};
          cores[i].load = _cpus[i].load / _cpus[i].currentTick * 100;
          cores[i].loadUser = _cpus[i].loadUser / _cpus[i].currentTick * 100;
          cores[i].loadSystem = _cpus[i].loadSystem / _cpus[i].currentTick * 100;
          cores[i].loadNice = _cpus[i].loadNice / _cpus[i].currentTick * 100;
          cores[i].loadIdle = _cpus[i].loadIdle / _cpus[i].currentTick * 100;
          cores[i].loadIrq = _cpus[i].loadIrq / _cpus[i].currentTick * 100;
          cores[i].rawLoad = _cpus[i].load;
          cores[i].rawLoadUser = _cpus[i].loadUser;
          cores[i].rawLoadSystem = _cpus[i].loadSystem;
          cores[i].rawLoadNice = _cpus[i].loadNice;
          cores[i].rawLoadIdle = _cpus[i].loadIdle;
          cores[i].rawLoadIrq = _cpus[i].loadIrq;
          cores[i].rawLoadSteal = _cpus[i].loadSteal;
          cores[i].rawLoadGuest = _cpus[i].loadGuest;
        }
        result = {
          avgLoad: avgLoad,
          currentLoad: _current_cpu.currentLoad,
          currentLoadUser: _current_cpu.currentLoadUser,
          currentLoadSystem: _current_cpu.currentLoadSystem,
          currentLoadNice: _current_cpu.currentLoadNice,
          currentLoadIdle: _current_cpu.currentLoadIdle,
          currentLoadIrq: _current_cpu.currentLoadIrq,
          currentLoadSteal: _current_cpu.currentLoadSteal,
          currentLoadGuest: _current_cpu.currentLoadGuest,
          rawCurrentLoad: _current_cpu.rawCurrentLoad,
          rawCurrentLoadUser: _current_cpu.rawCurrentLoadUser,
          rawCurrentLoadSystem: _current_cpu.rawCurrentLoadSystem,
          rawCurrentLoadNice: _current_cpu.rawCurrentLoadNice,
          rawCurrentLoadIdle: _current_cpu.rawCurrentLoadIdle,
          rawCurrentLoadIrq: _current_cpu.rawCurrentLoadIrq,
          rawCurrentLoadSteal: _current_cpu.rawCurrentLoadSteal,
          rawCurrentLoadGuest: _current_cpu.rawCurrentLoadGuest,
          cpus: cores
        };
      }
      resolve(result);
    });
  });
}

function currentLoad(callback) {

  return new Promise((resolve) => {
    process.nextTick(() => {
      getLoad().then(result => {
        if (callback) { callback(result); }
        resolve(result);
      });
    });
  });
}

exports.currentLoad = currentLoad;

// --------------------------
// PS - full load
// since bootup

function getFullLoad() {

  return new Promise((resolve) => {
    process.nextTick(() => {

      const cpus = os.cpus();
      let totalUser = 0;
      let totalSystem = 0;
      let totalNice = 0;
      let totalIrq = 0;
      let totalIdle = 0;

      let result = 0;

      if (cpus && cpus.length) {
        for (let i = 0, len = cpus.length; i < len; i++) {
          const cpu = cpus[i].times;
          totalUser += cpu.user;
          totalSystem += cpu.sys;
          totalNice += cpu.nice;
          totalIrq += cpu.irq;
          totalIdle += cpu.idle;
        }
        let totalTicks = totalIdle + totalIrq + totalNice + totalSystem + totalUser;
        result = (totalTicks - totalIdle) / totalTicks * 100.0;

      }
      resolve(result);
    });
  });
}

function fullLoad(callback) {

  return new Promise((resolve) => {
    process.nextTick(() => {
      getFullLoad().then(result => {
        if (callback) { callback(result); }
        resolve(result);
      });
    });
  });
}

exports.fullLoad = fullLoad;
