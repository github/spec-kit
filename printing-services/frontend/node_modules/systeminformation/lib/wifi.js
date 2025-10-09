'use strict';
// @ts-check
// ==================================================================================
// wifi.js
// ----------------------------------------------------------------------------------
// Description:   System Information - library
//                for Node.js
// Copyright:     (c) 2014 - 2025
// Author:        Sebastian Hildebrandt
// ----------------------------------------------------------------------------------
// License:       MIT
// ==================================================================================
// 9. wifi
// ----------------------------------------------------------------------------------

const os = require('os');
const exec = require('child_process').exec;
const execSync = require('child_process').execSync;
const util = require('./util');

let _platform = process.platform;

const _linux = (_platform === 'linux' || _platform === 'android');
const _darwin = (_platform === 'darwin');
const _windows = (_platform === 'win32');

function wifiDBFromQuality(quality) {
  const qual = parseFloat(quality);
  if (qual < 0) { return 0; }
  if (qual >= 100) { return -50; }
  return (qual / 2 - 100);
}

function wifiQualityFromDB(db) {
  const result = 2 * (parseFloat(db) + 100);
  return result <= 100 ? result : 100;
}

const _wifi_frequencies = {
  1: 2412,
  2: 2417,
  3: 2422,
  4: 2427,
  5: 2432,
  6: 2437,
  7: 2442,
  8: 2447,
  9: 2452,
  10: 2457,
  11: 2462,
  12: 2467,
  13: 2472,
  14: 2484,
  32: 5160,
  34: 5170,
  36: 5180,
  38: 5190,
  40: 5200,
  42: 5210,
  44: 5220,
  46: 5230,
  48: 5240,
  50: 5250,
  52: 5260,
  54: 5270,
  56: 5280,
  58: 5290,
  60: 5300,
  62: 5310,
  64: 5320,
  68: 5340,
  96: 5480,
  100: 5500,
  102: 5510,
  104: 5520,
  106: 5530,
  108: 5540,
  110: 5550,
  112: 5560,
  114: 5570,
  116: 5580,
  118: 5590,
  120: 5600,
  122: 5610,
  124: 5620,
  126: 5630,
  128: 5640,
  132: 5660,
  134: 5670,
  136: 5680,
  138: 5690,
  140: 5700,
  142: 5710,
  144: 5720,
  149: 5745,
  151: 5755,
  153: 5765,
  155: 5775,
  157: 5785,
  159: 5795,
  161: 5805,
  165: 5825,
  169: 5845,
  173: 5865,
  183: 4915,
  184: 4920,
  185: 4925,
  187: 4935,
  188: 4940,
  189: 4945,
  192: 4960,
  196: 4980
};

function wifiFrequencyFromChannel(channel) {
  return {}.hasOwnProperty.call(_wifi_frequencies, channel) ? _wifi_frequencies[channel] : null;
}

function wifiChannelFromFrequencs(frequency) {
  let channel = 0;
  for (let key in _wifi_frequencies) {
    if ({}.hasOwnProperty.call(_wifi_frequencies, key)) {
      if (_wifi_frequencies[key] === frequency) { channel = util.toInt(key); }
    }
  }
  return channel;
}

function ifaceListLinux() {
  const result = [];
  const cmd = 'iw dev 2>/dev/null';
  try {
    const all = execSync(cmd, util.execOptsLinux).toString().split('\n').map(line => line.trim()).join('\n');
    const parts = all.split('\nInterface ');
    parts.shift();
    parts.forEach(ifaceDetails => {
      const lines = ifaceDetails.split('\n');
      const iface = lines[0];
      const id = util.toInt(util.getValue(lines, 'ifindex', ' '));
      const mac = util.getValue(lines, 'addr', ' ');
      const channel = util.toInt(util.getValue(lines, 'channel', ' '));
      result.push({
        id,
        iface,
        mac,
        channel
      });
    });
    return result;
  } catch (e) {
    try {
      const all = execSync('nmcli -t -f general,wifi-properties,wired-properties,interface-flags,capabilities,nsp device show 2>/dev/null', util.execOptsLinux).toString();
      const parts = all.split('\n\n');
      let i = 1;
      parts.forEach(ifaceDetails => {
        const lines = ifaceDetails.split('\n');
        const iface = util.getValue(lines, 'GENERAL.DEVICE');
        const type = util.getValue(lines, 'GENERAL.TYPE');
        const id = i++; // // util.getValue(lines, 'GENERAL.PATH');
        const mac = util.getValue(lines, 'GENERAL.HWADDR');
        const channel = '';
        if (type.toLowerCase() === 'wifi') {
          result.push({
            id,
            iface,
            mac,
            channel
          });
        }
      });
      return result;
    } catch (e) {
      return [];
    }
  }
}

function nmiDeviceLinux(iface) {
  const cmd = `nmcli -t -f general,wifi-properties,capabilities,ip4,ip6 device show ${iface} 2> /dev/null`;
  try {
    const lines = execSync(cmd, util.execOptsLinux).toString().split('\n');
    const ssid = util.getValue(lines, 'GENERAL.CONNECTION');
    return {
      iface,
      type: util.getValue(lines, 'GENERAL.TYPE'),
      vendor: util.getValue(lines, 'GENERAL.VENDOR'),
      product: util.getValue(lines, 'GENERAL.PRODUCT'),
      mac: util.getValue(lines, 'GENERAL.HWADDR').toLowerCase(),
      ssid: ssid !== '--' ? ssid : null
    };
  } catch (e) {
    return {};
  }
}

function nmiConnectionLinux(ssid) {
  const cmd = `nmcli -t --show-secrets connection show ${ssid} 2>/dev/null`;
  try {
    const lines = execSync(cmd, util.execOptsLinux).toString().split('\n');
    const bssid = util.getValue(lines, '802-11-wireless.seen-bssids').toLowerCase();
    return {
      ssid: ssid !== '--' ? ssid : null,
      uuid: util.getValue(lines, 'connection.uuid'),
      type: util.getValue(lines, 'connection.type'),
      autoconnect: util.getValue(lines, 'connection.autoconnect') === 'yes',
      security: util.getValue(lines, '802-11-wireless-security.key-mgmt'),
      bssid: bssid !== '--' ? bssid : null
    };
  } catch (e) {
    return {};
  }
}

function wpaConnectionLinux(iface) {
  if (!iface) {
    return {};
  }
  const cmd = `wpa_cli -i ${iface} status 2>&1`;
  try {
    const lines = execSync(cmd, util.execOptsLinux).toString().split('\n');
    const freq = util.toInt(util.getValue(lines, 'freq', '='));
    return {
      ssid: util.getValue(lines, 'ssid', '='),
      uuid: util.getValue(lines, 'uuid', '='),
      security: util.getValue(lines, 'key_mgmt', '='),
      freq,
      channel: wifiChannelFromFrequencs(freq),
      bssid: util.getValue(lines, 'bssid', '=').toLowerCase()
    };
  } catch (e) {
    return {};
  }
}

function getWifiNetworkListNmi() {
  const result = [];
  const cmd = 'nmcli -t -m multiline --fields active,ssid,bssid,mode,chan,freq,signal,security,wpa-flags,rsn-flags device wifi list 2>/dev/null';
  try {
    const stdout = execSync(cmd, util.execOptsLinux);
    const parts = stdout.toString().split('ACTIVE:');
    parts.shift();
    parts.forEach(part => {
      part = 'ACTIVE:' + part;
      const lines = part.split(os.EOL);
      const channel = util.getValue(lines, 'CHAN');
      const frequency = util.getValue(lines, 'FREQ').toLowerCase().replace('mhz', '').trim();
      const security = util.getValue(lines, 'SECURITY').replace('(', '').replace(')', '');
      const wpaFlags = util.getValue(lines, 'WPA-FLAGS').replace('(', '').replace(')', '');
      const rsnFlags = util.getValue(lines, 'RSN-FLAGS').replace('(', '').replace(')', '');
      const quality = util.getValue(lines, 'SIGNAL');
      result.push({
        ssid: util.getValue(lines, 'SSID'),
        bssid: util.getValue(lines, 'BSSID').toLowerCase(),
        mode: util.getValue(lines, 'MODE'),
        channel: channel ? parseInt(channel, 10) : null,
        frequency: frequency ? parseInt(frequency, 10) : null,
        signalLevel: wifiDBFromQuality(quality),
        quality: quality ? parseInt(quality, 10) : null,
        security: security && security !== 'none' ? security.split(' ') : [],
        wpaFlags: wpaFlags && wpaFlags !== 'none' ? wpaFlags.split(' ') : [],
        rsnFlags: rsnFlags && rsnFlags !== 'none' ? rsnFlags.split(' ') : []
      });
    });
    return result;
  } catch (e) {
    return [];
  }
}

function getWifiNetworkListIw(iface) {
  const result = [];
  try {
    let iwlistParts = execSync(`export LC_ALL=C; iwlist ${iface} scan 2>&1; unset LC_ALL`, util.execOptsLinux).toString().split('        Cell ');
    if (iwlistParts[0].indexOf('resource busy') >= 0) { return -1; }
    if (iwlistParts.length > 1) {
      iwlistParts.shift();
      iwlistParts.forEach(element => {
        const lines = element.split('\n');
        const channel = util.getValue(lines, 'channel', ':', true);
        const address = (lines && lines.length && lines[0].indexOf('Address:') >= 0 ? lines[0].split('Address:')[1].trim().toLowerCase() : '');
        const mode = util.getValue(lines, 'mode', ':', true);
        const frequency = util.getValue(lines, 'frequency', ':', true);
        const qualityString = util.getValue(lines, 'Quality', '=', true);
        const dbParts = qualityString.toLowerCase().split('signal level=');
        const db = dbParts.length > 1 ? util.toInt(dbParts[1]) : 0;
        const quality = db ? wifiQualityFromDB(db) : 0;
        const ssid = util.getValue(lines, 'essid', ':', true);

        // security and wpa-flags
        const isWpa = element.indexOf(' WPA ') >= 0;
        const isWpa2 = element.indexOf('WPA2 ') >= 0;
        const security = [];
        if (isWpa) { security.push('WPA'); }
        if (isWpa2) { security.push('WPA2'); }
        const wpaFlags = [];
        let wpaFlag = '';
        lines.forEach(function (line) {
          const l = line.trim().toLowerCase();
          if (l.indexOf('group cipher') >= 0) {
            if (wpaFlag) {
              wpaFlags.push(wpaFlag);
            }
            const parts = l.split(':');
            if (parts.length > 1) {
              wpaFlag = parts[1].trim().toUpperCase();
            }
          }
          if (l.indexOf('pairwise cipher') >= 0) {
            const parts = l.split(':');
            if (parts.length > 1) {
              if (parts[1].indexOf('tkip')) { wpaFlag = (wpaFlag ? 'TKIP/' + wpaFlag : 'TKIP'); }
              else if (parts[1].indexOf('ccmp')) { wpaFlag = (wpaFlag ? 'CCMP/' + wpaFlag : 'CCMP'); }
              else if (parts[1].indexOf('proprietary')) { wpaFlag = (wpaFlag ? 'PROP/' + wpaFlag : 'PROP'); }
            }
          }
          if (l.indexOf('authentication suites') >= 0) {
            const parts = l.split(':');
            if (parts.length > 1) {
              if (parts[1].indexOf('802.1x')) { wpaFlag = (wpaFlag ? '802.1x/' + wpaFlag : '802.1x'); }
              else if (parts[1].indexOf('psk')) { wpaFlag = (wpaFlag ? 'PSK/' + wpaFlag : 'PSK'); }
            }
          }
        });
        if (wpaFlag) {
          wpaFlags.push(wpaFlag);
        }

        result.push({
          ssid,
          bssid: address,
          mode,
          channel: channel ? util.toInt(channel) : null,
          frequency: frequency ? util.toInt(frequency.replace('.', '')) : null,
          signalLevel: db,
          quality,
          security,
          wpaFlags,
          rsnFlags: []
        });
      });
    }
    return result;
  } catch (e) {
    return -1;
  }
}

function parseWifiDarwinXX(wifiObj) {
  const result = [];
  if (wifiObj) {
    wifiObj.forEach(function (wifiItem) {
      const signalLevel = wifiItem.RSSI;
      let security = [];
      let wpaFlags = [];
      let ssid = wifiItem.SSID_STR || '';
      if (wifiItem.WPA_IE) {
        security.push('WPA');
        if (wifiItem.WPA_IE.IE_KEY_WPA_UCIPHERS) {
          wifiItem.WPA_IE.IE_KEY_WPA_UCIPHERS.forEach(function (ciphers) {
            if (ciphers === 0 && wpaFlags.indexOf('unknown/TKIP') === -1) { wpaFlags.push('unknown/TKIP'); }
            if (ciphers === 2 && wpaFlags.indexOf('PSK/TKIP') === -1) { wpaFlags.push('PSK/TKIP'); }
            if (ciphers === 4 && wpaFlags.indexOf('PSK/AES') === -1) { wpaFlags.push('PSK/AES'); }
          });
        }
      }
      if (wifiItem.RSN_IE) {
        security.push('WPA2');
        if (wifiItem.RSN_IE.IE_KEY_RSN_UCIPHERS) {
          wifiItem.RSN_IE.IE_KEY_RSN_UCIPHERS.forEach(function (ciphers) {
            if (ciphers === 0 && wpaFlags.indexOf('unknown/TKIP') === -1) { wpaFlags.push('unknown/TKIP'); }
            if (ciphers === 2 && wpaFlags.indexOf('TKIP/TKIP') === -1) { wpaFlags.push('TKIP/TKIP'); }
            if (ciphers === 4 && wpaFlags.indexOf('PSK/AES') === -1) { wpaFlags.push('PSK/AES'); }
          });
        }
      }
      if (wifiItem.SSID && ssid === '') {
        try {
          ssid = Buffer.from(wifiItem.SSID, 'base64').toString('utf8');
        } catch (err) {
          util.noop();
        }
      }
      result.push({
        ssid,
        bssid: wifiItem.BSSID || '',
        mode: '',
        channel: wifiItem.CHANNEL,
        frequency: wifiFrequencyFromChannel(wifiItem.CHANNEL),
        signalLevel: signalLevel ? parseInt(signalLevel, 10) : null,
        quality: wifiQualityFromDB(signalLevel),
        security,
        wpaFlags,
        rsnFlags: []
      });
    });
  }
  return result;
}

function parseWifiDarwin(wifiStr) {
  const result = [];
  try {
    let wifiObj = JSON.parse(wifiStr);
    wifiObj = wifiObj.SPAirPortDataType[0].spairport_airport_interfaces[0].spairport_airport_other_local_wireless_networks;
    wifiObj.forEach(function (wifiItem) {

      let security = [];
      const sm = wifiItem.spairport_security_mode || '';
      if (sm === 'spairport_security_mode_wep') {
        security.push('WEP');
      } else if (sm === 'spairport_security_mode_wpa2_personal') {
        security.push('WPA2');
      } else if (sm.startsWith('spairport_security_mode_wpa2_enterprise')) {
        security.push('WPA2 EAP');
      } else if (sm.startsWith('pairport_security_mode_wpa3_transition')) {
        security.push('WPA2/WPA3');
      } else if (sm.startsWith('pairport_security_mode_wpa3')) {
        security.push('WPA3');
      }
      const channel = parseInt(('' + wifiItem.spairport_network_channel).split(' ')[0]) || 0;
      const signalLevel = wifiItem.spairport_signal_noise || null;

      result.push({
        ssid: wifiItem._name || '',
        bssid: wifiItem.spairport_network_bssid || null,
        mode: wifiItem.spairport_network_phymode,
        channel,
        frequency: wifiFrequencyFromChannel(channel),
        signalLevel: signalLevel ? parseInt(signalLevel, 10) : null,
        quality: wifiQualityFromDB(signalLevel),
        security,
        wpaFlags: [],
        rsnFlags: []
      });
    });
    return result;
  } catch (e) {
    return result;
  }
};
function wifiNetworks(callback) {
  return new Promise((resolve) => {
    process.nextTick(() => {
      let result = [];
      if (_linux) {
        result = getWifiNetworkListNmi();
        if (result.length === 0) {
          try {
            const iwconfigParts = execSync('export LC_ALL=C; iwconfig 2>/dev/null; unset LC_ALL', util.execOptsLinux).toString().split('\n\n');
            let iface = '';
            iwconfigParts.forEach(element => {
              if (element.indexOf('no wireless') === -1 && element.trim() !== '') {
                iface = element.split(' ')[0];
              }
            });
            if (iface) {
              let ifaceSanitized = '';
              const s = util.isPrototypePolluted() ? '---' : util.sanitizeShellString(iface, true);
              const l = util.mathMin(s.length, 2000);

              for (let i = 0; i <= l; i++) {
                if (s[i] !== undefined) {
                  ifaceSanitized = ifaceSanitized + s[i];
                }
              }

              const res = getWifiNetworkListIw(ifaceSanitized);
              if (res === -1) {
                // try again after 4 secs
                setTimeout(function (iface) {
                  const res = getWifiNetworkListIw(iface);
                  if (res != -1) { result = res; }
                  if (callback) {
                    callback(result);
                  }
                  resolve(result);
                }, 4000);
              } else {
                result = res;
                if (callback) {
                  callback(result);
                }
                resolve(result);
              }
            } else {
              if (callback) {
                callback(result);
              }
              resolve(result);
            }
          } catch (e) {
            if (callback) {
              callback(result);
            }
            resolve(result);
          }
        } else {
          if (callback) {
            callback(result);
          }
          resolve(result);
        }
      } else if (_darwin) {
        let cmd = 'system_profiler SPAirPortDataType -json 2>/dev/null';
        exec(cmd, { maxBuffer: 1024 * 40000 }, function (error, stdout) {
          result = parseWifiDarwin(stdout.toString());
          if (callback) {
            callback(result);
          }
          resolve(result);
        });
      } else if (_windows) {
        let cmd = 'netsh wlan show networks mode=Bssid';
        util.powerShell(cmd).then((stdout) => {
          const ssidParts = stdout.toString('utf8').split(os.EOL + os.EOL + 'SSID ');
          ssidParts.shift();

          ssidParts.forEach(ssidPart => {
            const ssidLines = ssidPart.split(os.EOL);
            if (ssidLines && ssidLines.length >= 8 && ssidLines[0].indexOf(':') >= 0) {
              const bssidsParts = ssidPart.split(' BSSID');
              bssidsParts.shift();

              bssidsParts.forEach((bssidPart) => {
                const bssidLines = bssidPart.split(os.EOL);
                const bssidLine = bssidLines[0].split(':');
                bssidLine.shift();
                const bssid = bssidLine.join(':').trim().toLowerCase();
                const channel = bssidLines[3].split(':').pop().trim();
                const quality = bssidLines[1].split(':').pop().trim();

                result.push({
                  ssid: ssidLines[0].split(':').pop().trim(),
                  bssid,
                  mode: '',
                  channel: channel ? parseInt(channel, 10) : null,
                  frequency: wifiFrequencyFromChannel(channel),
                  signalLevel: wifiDBFromQuality(quality),
                  quality: quality ? parseInt(quality, 10) : null,
                  security: [ssidLines[2].split(':').pop().trim()],
                  wpaFlags: [ssidLines[3].split(':').pop().trim()],
                  rsnFlags: []
                });
              });
            }
          });

          if (callback) {
            callback(result);
          }
          resolve(result);
        });
      } else {
        if (callback) {
          callback(result);
        }
        resolve(result);
      }
    });
  });
}

exports.wifiNetworks = wifiNetworks;

function getVendor(model) {
  model = model.toLowerCase();
  let result = '';
  if (model.indexOf('intel') >= 0) { result = 'Intel'; }
  else if (model.indexOf('realtek') >= 0) { result = 'Realtek'; }
  else if (model.indexOf('qualcom') >= 0) { result = 'Qualcom'; }
  else if (model.indexOf('broadcom') >= 0) { result = 'Broadcom'; }
  else if (model.indexOf('cavium') >= 0) { result = 'Cavium'; }
  else if (model.indexOf('cisco') >= 0) { result = 'Cisco'; }
  else if (model.indexOf('marvel') >= 0) { result = 'Marvel'; }
  else if (model.indexOf('zyxel') >= 0) { result = 'Zyxel'; }
  else if (model.indexOf('melanox') >= 0) { result = 'Melanox'; }
  else if (model.indexOf('d-link') >= 0) { result = 'D-Link'; }
  else if (model.indexOf('tp-link') >= 0) { result = 'TP-Link'; }
  else if (model.indexOf('asus') >= 0) { result = 'Asus'; }
  else if (model.indexOf('linksys') >= 0) { result = 'Linksys'; }
  return result;
}

function formatBssid(s) {
  s = s.replace(/</g, '').replace(/>/g, '').match(/.{1,2}/g) || [];
  return s.join(':');
}

function wifiConnections(callback) {

  return new Promise((resolve) => {
    process.nextTick(() => {
      const result = [];

      if (_linux) {
        const ifaces = ifaceListLinux();
        const networkList = getWifiNetworkListNmi();
        ifaces.forEach(ifaceDetail => {
          let ifaceSanitized = '';
          const s = util.isPrototypePolluted() ? '---' : util.sanitizeShellString(ifaceDetail.iface, true);
          const ll = util.mathMin(s.length, 2000);

          for (let i = 0; i <= ll; i++) {
            if (s[i] !== undefined) {
              ifaceSanitized = ifaceSanitized + s[i];
            }
          }

          const nmiDetails = nmiDeviceLinux(ifaceSanitized);
          const wpaDetails = wpaConnectionLinux(ifaceSanitized);
          const ssid = nmiDetails.ssid || wpaDetails.ssid;
          const network = networkList.filter(nw => nw.ssid === ssid);
          let ssidSanitized = '';
          const t = util.isPrototypePolluted() ? '---' : util.sanitizeShellString(ssid, true);
          const l = util.mathMin(t.length, 32);
          for (let i = 0; i <= l; i++) {
            if (t[i] !== undefined) {
              ssidSanitized = ssidSanitized + t[i];
            }
          }

          const nmiConnection = nmiConnectionLinux(ssidSanitized);
          const channel = network && network.length && network[0].channel ? network[0].channel : (wpaDetails.channel ? wpaDetails.channel : null);
          const bssid = network && network.length && network[0].bssid ? network[0].bssid : (wpaDetails.bssid ? wpaDetails.bssid : null);
          const signalLevel = network && network.length && network[0].signalLevel ? network[0].signalLevel : null;
          if (ssid && bssid) {
            result.push({
              id: ifaceDetail.id,
              iface: ifaceDetail.iface,
              model: nmiDetails.product,
              ssid,
              bssid: network && network.length && network[0].bssid ? network[0].bssid : (wpaDetails.bssid ? wpaDetails.bssid : null),
              channel,
              frequency: channel ? wifiFrequencyFromChannel(channel) : null,
              type: nmiConnection.type ? nmiConnection.type : '802.11',
              security: nmiConnection.security ? nmiConnection.security : (wpaDetails.security ? wpaDetails.security : null),
              signalLevel,
              quality: wifiQualityFromDB(signalLevel),
              txRate: null
            });
          }
        });
        if (callback) {
          callback(result);
        }
        resolve(result);
      } else if (_darwin) {
        let cmd = 'system_profiler SPNetworkDataType SPAirPortDataType -xml 2>/dev/null; echo "######" ; ioreg -n AppleBCMWLANSkywalkInterface -r 2>/dev/null';
        exec(cmd, function (error, stdout) {
          try {
            const parts = stdout.toString().split('######');
            const profilerObj = util.plistParser(parts[0]);
            const networkObj = profilerObj[0]._SPCommandLineArguments.indexOf('SPNetworkDataType') >= 0 ? profilerObj[0]._items : profilerObj[1]._items;
            const airportObj = profilerObj[0]._SPCommandLineArguments.indexOf('SPAirPortDataType') >= 0 ? profilerObj[0]._items[0].spairport_airport_interfaces : profilerObj[1]._items[0].spairport_airport_interfaces;

            // parts[1] : ioreg
            let lines3 = [];
            if (parts[1].indexOf('  | {') > 0 && parts[1].indexOf('  | }') > parts[1].indexOf('  | {')) {
              lines3 = parts[1].split('  | {')[1].split('  | }')[0].replace(/ \| /g, '').replace(/"/g, '').split('\n');
            }

            const networkWifiObj = networkObj.find((item) => { return item._name === 'Wi-Fi'; });
            const airportWifiObj = airportObj[0].spairport_current_network_information;

            const channel = parseInt(('' + airportWifiObj.spairport_network_channel).split(' ')[0]) || 0;
            const signalLevel = airportWifiObj.spairport_signal_noise || null;

            let security = [];
            const sm = airportWifiObj.spairport_security_mode || '';
            if (sm === 'spairport_security_mode_wep') {
              security.push('WEP');
            } else if (sm === 'spairport_security_mode_wpa2_personal') {
              security.push('WPA2');
            } else if (sm.startsWith('spairport_security_mode_wpa2_enterprise')) {
              security.push('WPA2 EAP');
            } else if (sm.startsWith('pairport_security_mode_wpa3_transition')) {
              security.push('WPA2/WPA3');
            } else if (sm.startsWith('pairport_security_mode_wpa3')) {
              security.push('WPA3');
            }

            result.push({
              id: networkWifiObj._name || 'Wi-Fi',
              iface: networkWifiObj.interface || '',
              model: networkWifiObj.hardware || '',
              ssid: airportWifiObj._name || '',
              bssid: airportWifiObj.spairport_network_bssid || '',
              channel,
              frequency: channel ? wifiFrequencyFromChannel(channel) : null,
              type: airportWifiObj.spairport_network_phymode || '802.11',
              security,
              signalLevel: signalLevel ? parseInt(signalLevel, 10) : null,
              quality: wifiQualityFromDB(signalLevel),
              txRate: airportWifiObj.spairport_network_rate || null,
            });

          } catch (e) {
            util.noop();
          }
          if (callback) {
            callback(result);
          }
          resolve(result);
        });
      } else if (_windows) {
        let cmd = 'netsh wlan show interfaces';
        util.powerShell(cmd).then(function (stdout) {
          const allLines = stdout.toString().split('\r\n');
          for (let i = 0; i < allLines.length; i++) {
            allLines[i] = allLines[i].trim();
          }
          const parts = allLines.join('\r\n').split(':\r\n\r\n');
          parts.shift();
          parts.forEach(part => {
            const lines = part.split('\r\n');
            if (lines.length >= 5) {
              const iface = lines[0].indexOf(':') >= 0 ? lines[0].split(':')[1].trim() : '';
              const model = lines[1].indexOf(':') >= 0 ? lines[1].split(':')[1].trim() : '';
              const id = lines[2].indexOf(':') >= 0 ? lines[2].split(':')[1].trim() : '';
              const ssid = util.getValue(lines, 'SSID', ':', true);
              const bssid = util.getValue(lines, 'BSSID', ':', true) || util.getValue(lines, 'AP BSSID', ':', true);
              const quality = util.getValue(lines, 'Signal', ':', true);
              const signalLevel = wifiDBFromQuality(quality);
              const type = util.getValue(lines, 'Radio type', ':', true) || util.getValue(lines, 'Type de radio', ':', true) || util.getValue(lines, 'Funktyp', ':', true) || null;
              const security = util.getValue(lines, 'authentication', ':', true) || util.getValue(lines, 'Authentification', ':', true) || util.getValue(lines, 'Authentifizierung', ':', true) || null;
              const channel = util.getValue(lines, 'Channel', ':', true) || util.getValue(lines, 'Canal', ':', true) || util.getValue(lines, 'Kanal', ':', true) || null;
              const txRate = util.getValue(lines, 'Transmit rate (mbps)', ':', true) || util.getValue(lines, 'Transmission (mbit/s)', ':', true) || util.getValue(lines, 'Empfangsrate (MBit/s)', ':', true) || null;
              if (model && id && ssid && bssid) {
                result.push({
                  id,
                  iface,
                  model,
                  ssid,
                  bssid,
                  channel: util.toInt(channel),
                  frequency: channel ? wifiFrequencyFromChannel(channel) : null,
                  type,
                  security,
                  signalLevel,
                  quality: quality ? parseInt(quality, 10) : null,
                  txRate: util.toInt(txRate) || null
                });
              }
            }
          });
          if (callback) {
            callback(result);
          }
          resolve(result);
        });
      } else {
        if (callback) {
          callback(result);
        }
        resolve(result);
      }
    });
  });
}

exports.wifiConnections = wifiConnections;

function wifiInterfaces(callback) {

  return new Promise((resolve) => {
    process.nextTick(() => {
      const result = [];

      if (_linux) {
        const ifaces = ifaceListLinux();
        ifaces.forEach(ifaceDetail => {
          const nmiDetails = nmiDeviceLinux(ifaceDetail.iface);
          result.push({
            id: ifaceDetail.id,
            iface: ifaceDetail.iface,
            model: nmiDetails.product ? nmiDetails.product : null,
            vendor: nmiDetails.vendor ? nmiDetails.vendor : null,
            mac: ifaceDetail.mac,
          });
        });
        if (callback) {
          callback(result);
        }
        resolve(result);
      } else if (_darwin) {
        let cmd = 'system_profiler SPNetworkDataType';
        exec(cmd, function (error, stdout) {
          const parts1 = stdout.toString().split('\n\n    Wi-Fi:\n\n');
          if (parts1.length > 1) {
            const lines = parts1[1].split('\n\n')[0].split('\n');
            const iface = util.getValue(lines, 'BSD Device Name', ':', true);
            const mac = util.getValue(lines, 'MAC Address', ':', true);
            const model = util.getValue(lines, 'hardware', ':', true);
            result.push({
              id: 'Wi-Fi',
              iface,
              model,
              vendor: '',
              mac
            });
          }
          if (callback) {
            callback(result);
          }
          resolve(result);
        });
      } else if (_windows) {
        let cmd = 'netsh wlan show interfaces';
        util.powerShell(cmd).then(function (stdout) {
          const allLines = stdout.toString().split('\r\n');
          for (let i = 0; i < allLines.length; i++) {
            allLines[i] = allLines[i].trim();
          }
          const parts = allLines.join('\r\n').split(':\r\n\r\n');
          parts.shift();
          parts.forEach(part => {
            const lines = part.split('\r\n');
            if (lines.length >= 5) {
              const iface = lines[0].indexOf(':') >= 0 ? lines[0].split(':')[1].trim() : '';
              const model = lines[1].indexOf(':') >= 0 ? lines[1].split(':')[1].trim() : '';
              const id = lines[2].indexOf(':') >= 0 ? lines[2].split(':')[1].trim() : '';
              const macParts = lines[3].indexOf(':') >= 0 ? lines[3].split(':') : [];
              macParts.shift();
              const mac = macParts.join(':').trim();
              const vendor = getVendor(model);
              if (iface && model && id && mac) {
                result.push({
                  id,
                  iface,
                  model,
                  vendor,
                  mac,
                });
              }
            }
          });
          if (callback) {
            callback(result);
          }
          resolve(result);
        });
      } else {
        if (callback) {
          callback(result);
        }
        resolve(result);
      }
    });
  });
}

exports.wifiInterfaces = wifiInterfaces;
