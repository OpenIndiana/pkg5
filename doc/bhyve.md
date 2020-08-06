
# Bhyve branded-zone support

Bhyve branded zones are configured mainly via custom attributes in the zone
configuration.

To get started, `pkg install system/zones/brand/bhyve` and configure a zone with the
bhyve brand and the appropriate attributes; see the example zone at the end of
this page.

To troubleshoot problems if the zone fails to start, review the log file
which will be created at `/path/to/zone/root/tmp/init.log`

### Attributes

| Attribute	| Default		| Syntax		| Example
| ---		| ---			| ---			| ---
| acpi		| on			| on,off
| bootdisk<sup>1</sup>	| 			| path[,serial=<serno>] | tank/hdd/bhyve1
| bootorder	| cd			| \[c\]\[d\]
| bootrom<sup>3</sup>	| BHYVE_RELEASE	| firmware name\|path to firmware | BHYVE_DEBUG
| cdrom<sup>4</sup>		|			| path to ISO		  | /data/iso/FreeBSD-11.1-RELEASE-amd64-bootonly.iso
| console	| /dev/zconsole<sup>6</sup>	| options		| socket,/tmp/vm.com1,wait
| disk<sup>1</sup>		| 			| path[,serial=<serno>] | tank/hdd/bhyve2,serial=1234
| diskN<sup>2</sup>		| 			| path[,serial=<serno>] | tank/hdd/bhyve2,serial=1234
| diskif	| virtio-blk		| virtio-blk,ahci-hd
| hostbridge	| i440fx		| i440fx,q35,amd,netapp,none
| netif		| virtio-net-viona	| virtio-net-viona,e1000
| ram		| 1G			| n(G\|M)		| 8G
| type		| generic		| generic,windows,openbsd
| vcpus		| 1			| [[cpus=]numcpus][,sockets=n][,cores=n][,threads=n]] | cpus=16,sockets=2,cores=4,threads=2
| vnc<sup>5</sup>		| off			| off,on,options	| socket,/tmp/vm.vnc,w=1024,h=768,wait
| extra		|			| extra arguments for hypervisor |

#### Notes

<ol>
<li>You will also need to pass the underlying disk device through to the zone via a <i>device</i> entry, see the example below;</li>
<li>Use diskN to specify the slot into which the disk will be placed. A plain <i>disk</i> tag will be put in the lowest available slot.</li>
<li>Available firmware files can be found in <i>/usr/share/bhyve/firmware/</i>;</li>
<li>The ISO file needs passing through to the zone via a lofs mount, see the example below;</li>
<li>Setting vnc to <i>on</i> is the same as setting it to <i>unix=/tmp/vm.vnc</i>.</li>
<li>You can connect to the virtual machine console from the global zone with <i>zlogin -C zonename</i>;</li>
</ol>

### Example zone

The following example zone is shown twice, once in info format and once in
export (showing the necessary commands for creation). Note that the example
shows setting the `allowed-address` attribute for the network interface -
this does not configure the address within the virtual machine but rather
prevents the use of any other address (L3 protection).

```
hipster# zonecfg -z bhyve info
zonename: bhyve
zonepath: /data/zone/bhyve
brand: bhyve
autoboot: false
bootargs:
pool:
limitpriv:
scheduling-class:
ip-type: exclusive
hostid:
fs-allowed:
fs:
        dir: /tank/iso/FreeBSD-11.1-RELEASE-amd64-bootonly.iso
        special: /tank/iso/FreeBSD-11.1-RELEASE-amd64-bootonly.iso
        raw not specified
        type: lofs
        options: [ro,nodevices]
net:
        address not specified
        allowed-address: 10.0.0.112/24
        defrouter not specified
        physical: bhyve0
device:
        match: /dev/zvol/rdsk/tank/hdd/bhyve0
device:
        match: /dev/zvol/rdsk/tank/hdd/bhyve1
device:
        match: /dev/zvol/rdsk/tank/hdd/bhyve2
attr:
        name: vcpus
        type: string
        value: cpus=16,sockets=2,cores=4,threads=2
attr:
        name: ram
        type: string
        value: 4G
attr:
        name: bootrom
        type: string
        value: BHYVE_DEBUG
attr:
        name: console
        type: string
        value: socket,/tmp/vm.com1
attr:
        name: hostbridge
        type: string
        value: amd
attr:
        name: bootdisk
        type: string
        value: tank/hdd/bhyve0
attr:
        name: disk
        type: string
        value: tank/hdd/bhyve1
attr:
        name: disk1
        type: string
        value: tank/hdd/bhyve2,serial=1234
attr:
        name: cdrom
        type: string
        value: /tank/iso/FreeBSD-11.1-RELEASE-amd64-bootonly.iso
attr:
        name: vnc
        type: string
        value: unix=/tmp/vm.vnc,wait
```

```
hipster# zonecfg -z bhyve export
create -b
set zonepath=/data/zone/bhyve
set brand=bhyve
set autoboot=false
set ip-type=exclusive
add fs
set dir=/tank/iso/debian-9.4.0-amd64-netinst.iso
set special=/tank/iso/debian-9.4.0-amd64-netinst.iso
set type=lofs
add options ro
add options nodevices
end
add net
set allowed-address=10.0.0.112/24
set physical=bhyve0
end
add device
set match=/dev/zvol/rdsk/tank/hdd/bhyve0
end
add device
set match=/dev/zvol/rdsk/tank/hdd/bhyve1
end
add device
set match=/dev/zvol/rdsk/tank/hdd/bhyve2
end
add attr
set name=vcpus
set type=string
set value=cpus=16,sockets=2,cores=4,threads=2
end
add attr
set name=ram
set type=string
set value=4G
end
add attr
set name=bootrom
set type=string
set value=BHYVE_DEBUG
end
add attr
set name=console
set type=string
set value=socket,/tmp/vm.com1
end
add attr
set name=hostbridge
set type=string
set value=amd
end
add attr
set name=bootdisk
set type=string
set value=tank/hdd/bhyve0
end
add attr
set name=disk
set type=string
set value=tank/hdd/bhyve1
end
add attr
set name=disk1
set type=string
set value=tank/hdd/bhyve2,serial=1234
end
add attr
set name=cdrom
set type=string
set value=/tank/iso/debian-9.4.0-amd64-netinst.iso
end
add attr
set name=vnc
set type=string
set value=unix=/tmp/vm.vnc,wait
end
```

