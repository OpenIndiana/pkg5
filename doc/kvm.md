
# KVM branded-zone support

KVM branded zones are configured mainly via custom attributes in the zone
configuration.

To get started, `pkg install system/zones/brand/kvm` and configure a zone with the
kvm brand and the appropriate attributes; see the example zone at the end of
this page.

To troubleshoot problems if the zone fails to start, review the log file
which will be created at `/path/to/zone/root/tmp/init.log`

### Attributes

| Attribute	| Default		| Syntax		| Example
| ---		| ---			| ---			| ---
| bootdisk<sup>1</sup>	| 			| path[,serial=<serno>] | tank/hdd/kvm1
| bootorder	| cd			| \[c\]\[d\]\[n\]
| cdrom<sup>2</sup>		|			| path to ISO		  | /data/iso/FreeBSD-11.1-RELEASE-amd64-bootonly.iso
| cpu		| qemu64		|
| console	| pipe,id=console0,path=/dev/zconsole<sup>4</sup>	| options		|
| disk<sup>1</sup>		| 			| path[,serial=<serno>] | tank/hdd/kvm2,serial=1234
| diskif	| virtio		| virtio,ahci
| netif		| virtio-net-pci	| virtio-net-pci,e1000
| ram		| 1G			| n(G\|M)		| 8G
| type		| generic		| generic
| vcpus		| 1			|  n			| 16
| vnc<sup>3</sup>		| off			| off,on,options	| unix:/tmp/vm.vnc

#### Notes

<ol>
<li>You will also need to pass the underlying disk device through to the zone via a <i>device</i> entry, see the example below;</li>
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
bloody# zonecfg -z oi info
zonename: oi
zonepath: /data/zone/oi
brand: kvm
autoboot: false
bootargs:
pool:
limitpriv:
scheduling-class:
ip-type: exclusive
hostid:
fs-allowed:
fs:
        dir: /tank/iso/OI-hipster-minimal-20180427.iso
        special: /tank/iso/OI-hipster-minimal-20180427.iso
        raw not specified
        type: lofs
        options: [ro,nodevices]
net:
        address not specified
        allowed-address: 10.0.0.112/24
        defrouter not specified
        global-nic not specified
        mac-addr not specified
        physical: oi0
        vlan-id not specified
device:
        match: /dev/zvol/rdsk/tank/hdd/oi0
device:
        match: /dev/zvol/rdsk/tank/hdd/oi1
device:
        match: /dev/zvol/rdsk/tank/hdd/oi2
attr:
        name: vcpus
        type: string
        value: 16
attr:
        name: ram
        type: string
        value: 4G
attr:
        name: cdrom
        type: string
        value: /tank/iso/OI-hipster-minimal-20180427.iso
attr:
        name: vnc
        type: string
        value: on
attr:
        name: bootdisk
        type: string
        value: tank/hdd/oi0
attr:
        name: disk
        type: string
        value: tank/hdd/oi1
attr:
        name: disk
        type: string
        value: tank/hdd/oi2,serial=1234
```

```
bloody# zonecfg -z oi export
create -b
set zonepath=/data/zone/oi
set brand=kvm
set autoboot=false
set ip-type=exclusive
add fs
set dir=/tank/iso/OI-hipster-minimal-20180427.iso
set special=/tank/iso/OI-hipster-minimal-20180427.iso
set type=lofs
add options ro
add options nodevices
end
add net
set allowed-address=10.0.0.112/24
set physical=oi0
end
add device
set match=/dev/zvol/rdsk/tank/hdd/oi0
end
add device
set match=/dev/zvol/rdsk/tank/hdd/oi1
end
add device
set match=/dev/zvol/rdsk/tank/hdd/oi2
end
add attr
set name=vcpus
set type=string
set value=16
end
add attr
set name=ram
set type=string
set value=4G
end
add attr
set name=cdrom
set type=string
set value=/tank/iso/OI-hipster-minimal-20180427.iso
end
add attr
set name=vnc
set type=string
set value=on
end
add attr
set name=bootdisk
set type=string
set value=tank/hdd/oi0
end
add attr
set name=disk
set type=string
set value=tank/hdd/oi1
end
add attr
set name=disk
set type=string
set value=tank/hdd/oi2,serial=1234
end
```

You can connect to kvm vga console of zone with vncviewer and socat. For example:
```
# socat TCP-LISTEN:5500  UNIX-CONNECT:/data/zone/oi/root/tmp/vm.vnc 
$ vncviewer localhost:5500
```

