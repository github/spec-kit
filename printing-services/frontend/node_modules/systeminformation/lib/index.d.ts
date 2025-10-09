// Type definitions for systeminformation
// Project: https://github.com/sebhildebrandt/systeminformation
// Definitions by: sebhildebrandt <https://github.com/sebhildebrandt>

/// <reference types="node" />

export namespace Systeminformation {

  // 1. General

  interface TimeData {
    current: number;
    uptime: number;
    timezone: string;
    timezoneName: string;
  }

  // 2. System (HW)

  interface RaspberryRevisionData {
    manufacturer: string;
    processor: string;
    type: string;
    revision: string;
  }
  interface SystemData {
    manufacturer: string;
    model: string;
    version: string;
    serial: string;
    uuid: string;
    sku: string;
    virtual: boolean;
    virtualHost?: string;
    raspberry?: RaspberryRevisionData;
  }

  interface BiosData {
    vendor: string;
    version: string;
    releaseDate: string;
    revision: string;
    serial?: string;
    language?: string;
    features?: string[];
  }

  interface BaseboardData {
    manufacturer: string;
    model: string;
    version: string;
    serial: string;
    assetTag: string;
    memMax: number | null;
    memSlots: number | null;
  }

  interface ChassisData {
    manufacturer: string;
    model: string;
    type: string;
    version: string;
    serial: string;
    assetTag: string;
    sku: string;
  }

  // 3. CPU, Memory, Disks, Battery, Graphics

  interface CpuData {
    manufacturer: string;
    brand: string;
    vendor: string;
    family: string;
    model: string;
    stepping: string;
    revision: string;
    voltage: string;
    speed: number;
    speedMin: number;
    speedMax: number;
    governor: string;
    cores: number;
    physicalCores: number;
    efficiencyCores?: number;
    performanceCores?: number;
    processors: number;
    socket: string;
    flags: string;
    virtualization: boolean;
    cache: CpuCacheData;
  }

  interface CpuCacheData {
    l1d: number;
    l1i: number;
    l2: number;
    l3: number;
  }

  interface CpuCurrentSpeedData {
    min: number;
    max: number;
    avg: number;
    cores: number[];
  }

  interface CpuTemperatureData {
    main: number;
    cores: number[];
    max: number;
    socket?: number[];
    chipset?: number;
  }

  interface MemData {
    total: number;
    free: number;
    used: number;
    active: number;
    available: number;
    buffcache: number;
    buffers: number;
    cached: number;
    slab: number;
    reclaimable: number;
    swaptotal: number;
    swapused: number;
    swapfree: number;
    writeback: number | null;
    dirty: number | null;
  }

  interface MemLayoutData {
    size: number;
    bank: string;
    type: string;
    ecc?: boolean | null;
    clockSpeed: number | null;
    formFactor: string;
    manufacturer?: string;
    partNum: string;
    serialNum: string;
    voltageConfigured: number | null;
    voltageMin: number | null;
    voltageMax: number | null;
  }

  interface SmartData {
    json_format_version: number[];
    smartctl: {
      version: number[];
      platform_info: string;
      build_info: string;
      argv: string[];
      exit_status: number;
    };
    device: {
      name: string;
      info_name: string;
      type: string;
      protocol: string;
    };
    model_family?: string;
    model_name?: string;
    serial_number?: string;
    firmware_version?: string;
    smart_status: {
      passed: boolean;
    };
    trim?: {
      supported: boolean;
    };
    ata_smart_attributes?: {
      revision: number;
      table: {
        id: number;
        name: string;
        value: number;
        worst: number;
        thresh: number;
        when_failed: string;
        flags: {
          value: number;
          string: string;
          prefailure: boolean;
          updated_online: boolean;
          performance: boolean;
          error_rate: boolean;
          event_count: boolean;
          auto_keep: boolean;
        };
        raw: {
          value: number;
          string: string;
        };
      }[];
    };
    ata_smart_error_log?: {
      summary: {
        revision: number;
        count: number;
      };
    };
    ata_smart_self_test_log?: {
      standard: {
        revision: number;
        table: {
          type: {
            value: number;
            string: string;
          };
          status: {
            value: number;
            string: string;
            passed: boolean;
          };
          lifetime_hours: number;
        }[];
        count: number;
        error_count_total: number;
        error_count_outdated: number;
      };
    };
    nvme_pci_vendor?: {
      id: number;
      subsystem_id: number;
    },
    nvme_smart_health_information_log?: {
      critical_warning?: number;
      temperature?: number;
      available_spare?: number;
      available_spare_threshold?: number;
      percentage_used?: number;
      data_units_read?: number;
      data_units_written?: number;
      host_reads?: number;
      host_writes?: number;
      controller_busy_time?: number;
      power_cycles?: number;
      power_on_hours?: number;
      unsafe_shutdowns?: number;
      media_errors?: number;
      num_err_log_entries?: number;
      warning_temp_time?: number;
      critical_comp_time?: number;
      temperature_sensors?: number[];
    },
    user_capacity?: {
      blocks: number;
      bytes: number;
    },
    logical_block_size?: number;
    temperature: {
      current: number;
    };
    power_cycle_count: number;
    power_on_time: {
      hours: number;
    };
  }

  interface DiskLayoutData {
    device: string;
    type: string;
    name: string;
    vendor: string;
    size: number;
    bytesPerSector: number;
    totalCylinders: number;
    totalHeads: number;
    totalSectors: number;
    totalTracks: number;
    tracksPerCylinder: number;
    sectorsPerTrack: number;
    firmwareRevision: string;
    serialNum: string;
    interfaceType: string;
    smartStatus: string;
    temperature: null | number;
    smartData?: SmartData;
  }

  interface BatteryData {
    hasBattery: boolean;
    cycleCount: number;
    isCharging: boolean;
    voltage: number;
    designedCapacity: number;
    maxCapacity: number;
    currentCapacity: number;
    capacityUnit: string;
    percent: number;
    timeRemaining: number;
    acConnected: boolean;
    type: string;
    model: string;
    manufacturer: string;
    serial: string;
    additionalBatteries?: BatteryData[];
  }

  interface GraphicsData {
    controllers: GraphicsControllerData[];
    displays: GraphicsDisplayData[];
  }

  interface GraphicsControllerData {
    vendor: string;
    subVendor?: string;
    vendorId?: string;
    model: string;
    deviceId?: string;
    bus: string;
    busAddress?: string;
    vram: number | null;
    vramDynamic: boolean;
    external?: boolean;
    cores?: number;
    metalVersion?: string;
    subDeviceId?: string;
    driverVersion?: string;
    name?: string;
    pciBus?: string;
    pciID?: string;
    fanSpeed?: number;
    memoryTotal?: number;
    memoryUsed?: number;
    memoryFree?: number;
    utilizationGpu?: number;
    utilizationMemory?: number;
    temperatureGpu?: number;
    temperatureMemory?: number;
    powerDraw?: number;
    powerLimit?: number;
    clockCore?: number;
    clockMemory?: number;
  }

  interface GraphicsDisplayData {
    vendor: string;
    vendorId: string | null;
    model: string;
    productionYear: number | null;
    serial: string | null;
    deviceName: string | null;
    displayId: string | null;
    main: boolean;
    builtin: boolean;
    connection: string | null;
    sizeX: number | null;
    sizeY: number | null;
    pixelDepth: number | null;
    resolutionX: number | null;
    resolutionY: number | null;
    currentResX: number | null;
    currentResY: number | null;
    positionX: number;
    positionY: number;
    currentRefreshRate: number | null;
  }

  // 4. Operating System

  interface OsData {
    platform: string;
    distro: string;
    release: string;
    codename: string;
    kernel: string;
    arch: string;
    hostname: string;
    fqdn: string;
    codepage: string;
    logofile: string;
    serial: string;
    build: string;
    servicepack: string;
    uefi: boolean | null;
    hypervizor?: boolean;
    remoteSession?: boolean;
  }

  interface UuidData {
    os: string;
    hardware: string;
    macs: string[];
  }

  interface VersionData {
    kernel?: string;
    openssl?: string;
    systemOpenssl?: string;
    systemOpensslLib?: string;
    node?: string;
    v8?: string;
    npm?: string;
    yarn?: string;
    pm2?: string;
    gulp?: string;
    grunt?: string;
    git?: string;
    tsc?: string;
    mysql?: string;
    redis?: string;
    mongodb?: string;
    nginx?: string;
    php?: string;
    docker?: string;
    postfix?: string;
    postgresql?: string;
    perl?: string;
    python?: string;
    python3?: string;
    pip?: string;
    pip3?: string;
    java?: string;
    gcc?: string;
    virtualbox?: string;
    dotnet?: string;
  }

  interface UserData {
    user: string;
    tty: string;
    date: string;
    time: string;
    ip: string;
    command: string;
  }

  // 5. File System

  interface FsSizeData {
    fs: string;
    type: string;
    size: number;
    used: number;
    available: number;
    use: number;
    mount: string;
    rw: boolean | null;
  }

  interface FsOpenFilesData {
    max: number;
    allocated: number;
    available: number;
  }

  interface BlockDevicesData {
    name: string;
    identifier: string;
    type: string;
    fsType: string;
    mount: string;
    size: number;
    physical: string;
    uuid: string;
    label: string;
    model: string;
    serial: string;
    removable: boolean;
    protocol: string;
    group?: string;
    device?: string;
  }

  interface FsStatsData {
    rx: number;
    wx: number;
    tx: number;
    rx_sec: number | null;
    wx_sec: number | null;
    tx_sec: number | null;
    ms: number;
  }

  interface DisksIoData {
    rIO: number;
    wIO: number;
    tIO: number;
    rIO_sec: number | null;
    wIO_sec: number | null;
    tIO_sec: number | null;
    rWaitTime: number;
    wWaitTime: number;
    tWaitTime: number;
    rWaitPercent: number | null;
    wWaitPercent: number | null;
    tWaitPercent: number | null;
    ms: number;
  }

  // 6. Network related functions

  interface NetworkInterfacesData {
    iface: string;
    ifaceName: string;
    default: boolean;
    ip4: string;
    ip4subnet: string;
    ip6: string;
    ip6subnet: string;
    mac: string;
    internal: boolean;
    virtual: boolean;
    operstate: string;
    type: string;
    duplex: string;
    mtu: number | null;
    speed: number | null;
    dhcp: boolean;
    dnsSuffix: string;
    ieee8021xAuth: string;
    ieee8021xState: string;
    carrierChanges: number;
  }

  interface NetworkStatsData {
    iface: string;
    operstate: string;
    rx_bytes: number;
    rx_dropped: number;
    rx_errors: number;
    tx_bytes: number;
    tx_dropped: number;
    tx_errors: number;
    rx_sec: number;
    tx_sec: number;
    ms: number;
  }

  interface NetworkConnectionsData {
    protocol: string;
    localAddress: string;
    localPort: string;
    peerAddress: string;
    peerPort: string;
    state: string;
    pid: number;
    process: string;
  }

  interface InetChecksiteData {
    url: string;
    ok: boolean;
    status: number;
    ms: number;
  }

  interface WifiNetworkData {
    ssid: string;
    bssid: string;
    mode: string;
    channel: number;
    frequency: number;
    signalLevel: number;
    quality: number;
    security: string[];
    wpaFlags: string[];
    rsnFlags: string[];
  }

  interface WifiInterfaceData {
    id: string;
    iface: string;
    model: string;
    vendor: string;
    mac: string;
  }

  interface WifiConnectionData {
    id: string;
    iface: string;
    model: string;
    ssid: string;
    bssid: string;
    channel: number;
    frequency: number;
    type: string;
    security: string;
    signalLevel: number;
    quality: number;
    txRate: number;
  }

  // 7. Current Load, Processes & Services

  interface CurrentLoadData {
    avgLoad: number;
    currentLoad: number;
    currentLoadUser: number;
    currentLoadSystem: number;
    currentLoadNice: number;
    currentLoadIdle: number;
    currentLoadIrq: number;
    currentLoadSteal: number;
    currentLoadGuest: number;
    rawCurrentLoad: number;
    rawCurrentLoadUser: number;
    rawCurrentLoadSystem: number;
    rawCurrentLoadNice: number;
    rawCurrentLoadIdle: number;
    rawCurrentLoadIrq: number;
    rawCurrentLoadSteal: number;
    rawCurrentLoadGuest: number;
    cpus: CurrentLoadCpuData[];
  }

  interface CurrentLoadCpuData {
    load: number;
    loadUser: number;
    loadSystem: number;
    loadNice: number;
    loadIdle: number;
    loadIrq: number;
    loadSteal: number;
    loadGuest: number;
    rawLoad: number;
    rawLoadUser: number;
    rawLoadSystem: number;
    rawLoadNice: number;
    rawLoadIdle: number;
    rawLoadIrq: number;
    rawLoadSteal: number;
    rawLoadGuest: number;
  }

  interface ProcessesData {
    all: number;
    running: number;
    blocked: number;
    sleeping: number;
    unknown: number;
    list: ProcessesProcessData[];
  }

  interface ProcessesProcessData {
    pid: number;
    parentPid: number;
    name: string;
    cpu: number;
    cpuu: number;
    cpus: number;
    mem: number;
    priority: number;
    memVsz: number;
    memRss: number;
    nice: number;
    started: string;
    state: string;
    tty: string;
    user: string;
    command: string;
    params: string;
    path: string;
  }

  interface ProcessesProcessLoadData {
    proc: string;
    pid: number;
    pids: number[];
    cpu: number;
    mem: number;
  }

  interface ServicesData {
    name: string;
    running: boolean;
    startmode: string;
    pids: number[];
    cpu: number;
    mem: number;
  }

  // 8. Docker

  interface DockerInfoData {
    id: string;
    containers: number;
    containersRunning: number;
    containersPaused: number;
    containersStopped: number;
    images: number;
    driver: string;
    memoryLimit: boolean;
    swapLimit: boolean;
    kernelMemory: boolean;
    cpuCfsPeriod: boolean;
    cpuCfsQuota: boolean;
    cpuShares: boolean;
    cpuSet: boolean;
    ipv4Forwarding: boolean;
    bridgeNfIptables: boolean;
    bridgeNfIp6tables: boolean;
    debug: boolean;
    nfd: number;
    oomKillDisable: boolean;
    ngoroutines: number;
    systemTime: string;
    loggingDriver: string;
    cgroupDriver: string;
    nEventsListener: number;
    kernelVersion: string;
    operatingSystem: string;
    osType: string;
    architecture: string;
    ncpu: number;
    memTotal: number;
    dockerRootDir: string;
    httpProxy: string;
    httpsProxy: string;
    noProxy: string;
    name: string;
    labels: string[];
    experimentalBuild: boolean;
    serverVersion: string;
    clusterStore: string;
    clusterAdvertise: string;
    defaultRuntime: string;
    liveRestoreEnabled: boolean;
    isolation: string;
    initBinary: string;
    productLicense: string;
  }

  interface DockerImageData {
    id: string;
    container: string;
    comment: string;
    os: string;
    architecture: string;
    parent: string;
    dockerVersion: string;
    size: number;
    sharedSize: number;
    virtualSize: number;
    author: string;
    created: number;
    containerConfig: any;
    graphDriver: any;
    repoDigests: any;
    repoTags: any;
    config: any;
    rootFS: any;
  }

  interface DockerContainerData {
    id: string;
    name: string;
    image: string;
    imageID: string;
    command: string;
    created: number;
    started: number;
    finished: number;
    createdAt: string;
    startedAt: string;
    finishedAt: string;
    state: string;
    restartCount: number;
    platform: string;
    driver: string;
    ports: number[];
    mounts: DockerContainerMountData[];
  }

  interface DockerContainerMountData {
    Type: string;
    Source: string;
    Destination: string;
    Mode: string;
    RW: boolean;
    Propagation: string;
  }

  interface DockerContainerStatsData {
    id: string;
    memUsage: number;
    memLimit: number;
    memPercent: number;
    cpuPercent: number;
    pids: number;
    netIO: {
      rx: number;
      wx: number;
    };
    blockIO: {
      r: number;
      w: number;
    };
    restartCount: number;
    cpuStats: any;
    precpuStats: any;
    memoryStats: any;
    networks: any;
  }

  interface DockerContainerProcessData {
    pidHost: string;
    ppid: string;
    pgid: string;
    user: string;
    ruser: string;
    group: string;
    rgroup: string;
    stat: string;
    time: string;
    elapsed: string;
    nice: string;
    rss: string;
    vsz: string;
    command: string;
  }

  interface DockerVolumeData {
    name: string;
    driver: string;
    labels: any;
    mountpoint: string;
    options: any;
    scope: string;
    created: number;
  }

  // 9. Virtual Box

  interface VboxInfoData {
    id: string;
    name: string;
    running: boolean;
    started: string;
    runningSince: number;
    stopped: string;
    stoppedSince: number;
    guestOS: string;
    hardwareUUID: string;
    memory: number;
    vram: number;
    cpus: number;
    cpuExepCap: string;
    cpuProfile: string;
    chipset: string;
    firmware: string;
    pageFusion: boolean;
    configFile: string;
    snapshotFolder: string;
    logFolder: string;
    hpet: boolean;
    pae: boolean;
    longMode: boolean;
    tripleFaultReset: boolean;
    apic: boolean;
    x2Apic: boolean;
    acpi: boolean;
    ioApic: boolean;
    biosApicMode: string;
    bootMenuMode: string;
    bootDevice1: string;
    bootDevice2: string;
    bootDevice3: string;
    bootDevice4: string;
    timeOffset: string;
    rtc: string;
  }

  interface PrinterData {
    id: number;
    name: string;
    model: string;
    uri: string;
    uuid: string;
    local: boolean;
    status: string;
    default: boolean;
    shared: boolean;
  }

  interface UsbData {
    id: number | string;
    bus: number;
    deviceId: number;
    name: string;
    type: string;
    removable: boolean;
    vendor: string;
    manufacturer: string;
    maxPower: string;
    serialNumber: string;
  }

  interface AudioData {
    id: number | string;
    name: string;
    manufacturer: string;
    default: boolean;
    revision: string;
    driver: string;
    channel: string;
    in: boolean;
    out: boolean;
    type: string;
    status: string;
  }

  interface BluetoothDeviceData {
    device: string;
    name: string;
    macDevice: string;
    macHost: string;
    batteryPercent: number;
    manufacturer: string;
    type: string;
    connected: boolean;
  }

  // 10. "Get All at once" - functions

  interface StaticData {
    version: string;
    system: SystemData;
    bios: BiosData;
    baseboard: BaseboardData;
    chassis: ChassisData;
    os: OsData;
    uuid: UuidData;
    versions: VersionData;
    cpu: CpuData;
    graphics: GraphicsData;
    net: NetworkInterfacesData[];
    memLayout: MemLayoutData[];
    diskLayout: DiskLayoutData[];
  }

  interface DynamicData {
    time: TimeData;
    node: string;
    v8: string;
    cpuCurrentSpeed: CpuCurrentSpeedData;
    users: UserData[];
    processes: ProcessesData[];
    currentLoad: CurrentLoadData;
    cpuTemperature: CpuTemperatureData;
    networkStats: NetworkStatsData[];
    networkConnections: NetworkConnectionsData[];
    mem: MemData;
    battery: BatteryData;
    services: ServicesData[];
    fsSize: FsSizeData;
    fsStats: FsStatsData;
    disksIO: DisksIoData;
    wifiNetworks: WifiNetworkData;
    inetLatency: number;
  }
}

export function version(): string;
export function system(cb?: (data: Systeminformation.SystemData) => any): Promise<Systeminformation.SystemData>;
export function bios(cb?: (data: Systeminformation.BiosData) => any): Promise<Systeminformation.BiosData>;
export function baseboard(cb?: (data: Systeminformation.BaseboardData) => any): Promise<Systeminformation.BaseboardData>;
export function chassis(cb?: (data: Systeminformation.ChassisData) => any): Promise<Systeminformation.ChassisData>;

export function time(): Systeminformation.TimeData;
export function osInfo(cb?: (data: Systeminformation.OsData) => any): Promise<Systeminformation.OsData>;
export function versions(apps?: string, cb?: (data: Systeminformation.VersionData) => any): Promise<Systeminformation.VersionData>;
export function versions(cb?: (data: Systeminformation.VersionData) => any): Promise<Systeminformation.VersionData>;
export function shell(cb?: (data: string) => any): Promise<string>;
export function uuid(cb?: (data: Systeminformation.UuidData) => any): Promise<Systeminformation.UuidData>;

export function cpu(cb?: (data: Systeminformation.CpuData) => any): Promise<Systeminformation.CpuData>;
export function cpuFlags(cb?: (data: string) => any): Promise<string>;
export function cpuCache(cb?: (data: Systeminformation.CpuCacheData) => any): Promise<Systeminformation.CpuCacheData>;
export function cpuCurrentSpeed(cb?: (data: Systeminformation.CpuCurrentSpeedData) => any): Promise<Systeminformation.CpuCurrentSpeedData>;
export function cpuTemperature(cb?: (data: Systeminformation.CpuTemperatureData) => any): Promise<Systeminformation.CpuTemperatureData>;
export function currentLoad(cb?: (data: Systeminformation.CurrentLoadData) => any): Promise<Systeminformation.CurrentLoadData>;
export function fullLoad(cb?: (data: number) => any): Promise<number>;

export function mem(cb?: (data: Systeminformation.MemData) => any): Promise<Systeminformation.MemData>;
export function memLayout(cb?: (data: Systeminformation.MemLayoutData[]) => any): Promise<Systeminformation.MemLayoutData[]>;

export function battery(cb?: (data: Systeminformation.BatteryData) => any): Promise<Systeminformation.BatteryData>;
export function graphics(cb?: (data: Systeminformation.GraphicsData) => any): Promise<Systeminformation.GraphicsData>;

export function fsSize(drive?: string, cb?: (data: Systeminformation.FsSizeData[]) => any): Promise<Systeminformation.FsSizeData[]>;
export function fsSize(cb?: (data: Systeminformation.FsSizeData[]) => any): Promise<Systeminformation.FsSizeData[]>;
export function fsOpenFiles(cb?: (data: Systeminformation.FsOpenFilesData[]) => any): Promise<Systeminformation.FsOpenFilesData[]>;
export function blockDevices(cb?: (data: Systeminformation.BlockDevicesData[]) => any): Promise<Systeminformation.BlockDevicesData[]>;
export function fsStats(cb?: (data: Systeminformation.FsStatsData) => any): Promise<Systeminformation.FsStatsData>;
export function disksIO(cb?: (data: Systeminformation.DisksIoData) => any): Promise<Systeminformation.DisksIoData>;
export function diskLayout(cb?: (data: Systeminformation.DiskLayoutData[]) => any): Promise<Systeminformation.DiskLayoutData[]>;

export function networkInterfaceDefault(cb?: (data: string) => any): Promise<string>;
export function networkGatewayDefault(cb?: (data: string) => any): Promise<string>;
export function networkInterfaces(): Promise<Systeminformation.NetworkInterfacesData[]>;
export function networkInterfaces(defaultString: 'default'): Promise<Systeminformation.NetworkInterfacesData>;
export function networkInterfaces(rescan: boolean): Promise<Systeminformation.NetworkInterfacesData[]>;
export function networkInterfaces(
  cb:
    | ((data: Systeminformation.NetworkInterfacesData[] | Systeminformation.NetworkInterfacesData) => any)
    | boolean
    | string,
  rescan?: boolean,
  defaultString?: string
): Promise<Systeminformation.NetworkInterfacesData[] | Systeminformation.NetworkInterfacesData>;

export function networkStats(ifaces?: string, cb?: (data: Systeminformation.NetworkStatsData[]) => any): Promise<Systeminformation.NetworkStatsData[]>;
export function networkStats(cb?: (data: Systeminformation.NetworkStatsData[]) => any): Promise<Systeminformation.NetworkStatsData[]>;
export function networkConnections(cb?: (data: Systeminformation.NetworkConnectionsData[]) => any): Promise<Systeminformation.NetworkConnectionsData[]>;
export function inetChecksite(url: string, cb?: (data: Systeminformation.InetChecksiteData) => any): Promise<Systeminformation.InetChecksiteData>;
export function inetLatency(host?: string, cb?: (data: number) => any): Promise<number>;
export function inetLatency(cb?: (data: number) => any): Promise<number>;

export function wifiNetworks(cb?: (data: Systeminformation.WifiNetworkData[]) => any): Promise<Systeminformation.WifiNetworkData[]>;
export function wifiInterfaces(cb?: (data: Systeminformation.WifiInterfaceData[]) => any): Promise<Systeminformation.WifiInterfaceData[]>;
export function wifiConnections(cb?: (data: Systeminformation.WifiConnectionData[]) => any): Promise<Systeminformation.WifiConnectionData[]>;

export function users(cb?: (data: Systeminformation.UserData[]) => any): Promise<Systeminformation.UserData[]>;

export function processes(cb?: (data: Systeminformation.ProcessesData) => any): Promise<Systeminformation.ProcessesData>;
export function processLoad(processNames: string, cb?: (data: Systeminformation.ProcessesProcessLoadData[]) => any): Promise<Systeminformation.ProcessesProcessLoadData[]>;
export function services(serviceName: string, cb?: (data: Systeminformation.ServicesData[]) => any): Promise<Systeminformation.ServicesData[]>;

export function dockerInfo(cb?: (data: Systeminformation.DockerInfoData) => any): Promise<Systeminformation.DockerInfoData>;
export function dockerImages(all?: boolean, cb?: (data: Systeminformation.DockerImageData[]) => any): Promise<Systeminformation.DockerImageData[]>;
export function dockerImages(cb?: (data: Systeminformation.DockerImageData[]) => any): Promise<Systeminformation.DockerImageData[]>;
export function dockerContainers(all?: boolean, cb?: (data: Systeminformation.DockerContainerData[]) => any): Promise<Systeminformation.DockerContainerData[]>;
export function dockerContainers(cb?: (data: Systeminformation.DockerContainerData[]) => any): Promise<Systeminformation.DockerContainerData[]>;
export function dockerContainerStats(id?: string, cb?: (data: Systeminformation.DockerContainerStatsData[]) => any): Promise<Systeminformation.DockerContainerStatsData[]>;
export function dockerContainerStats(cb?: (data: Systeminformation.DockerContainerStatsData[]) => any): Promise<Systeminformation.DockerContainerStatsData[]>;
export function dockerContainerProcesses(id?: string, cb?: (data: any) => any): Promise<Systeminformation.DockerContainerProcessData[]>;
export function dockerContainerProcesses(cb?: (data: any) => any): Promise<Systeminformation.DockerContainerProcessData[]>;
export function dockerVolumes(cb?: (data: Systeminformation.DockerVolumeData[]) => any): Promise<Systeminformation.DockerVolumeData[]>;
export function dockerAll(cb?: (data: any) => any): Promise<any>;

export function vboxInfo(cb?: (data: Systeminformation.VboxInfoData[]) => any): Promise<Systeminformation.VboxInfoData[]>;

export function printer(cb?: (data: Systeminformation.PrinterData[]) => any): Promise<Systeminformation.PrinterData[]>;

export function usb(cb?: (data: Systeminformation.UsbData[]) => any): Promise<Systeminformation.UsbData[]>;

export function audio(cb?: (data: Systeminformation.AudioData[]) => any): Promise<Systeminformation.AudioData[]>;

export function bluetoothDevices(cb?: (data: Systeminformation.BluetoothDeviceData[]) => any): Promise<Systeminformation.BluetoothDeviceData[]>;

export function getStaticData(cb?: (data: Systeminformation.StaticData) => any): Promise<Systeminformation.StaticData>;
export function getDynamicData(srv?: string, iface?: string, cb?: (data: any) => any): Promise<Systeminformation.DynamicData>;
export function getAllData(srv?: string, iface?: string, cb?: (data: any) => any): Promise<Systeminformation.StaticData & Systeminformation.DynamicData>;
export function get(valuesObject: any, cb?: (data: any) => any): Promise<any>;
export function observe(valuesObject: any, interval: number, cb?: (data: any) => any): number;

export function powerShellStart(): void;
export function powerShellRelease(): void;
