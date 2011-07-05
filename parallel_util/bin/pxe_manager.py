#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2011 Ryohei Ueda
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from optparse import OptionParser
from xml.dom import minidom, Node
import xml
from string import Template

DHCP_HOST_TMPL = """
host ${hostname}{
 hardware ethernet ${mac};
 fixed-address ${ip};
 next-server ${pxe_server};
 filename ${pxe_filename};
}
"""

def parse_options():
    parser = OptionParser()
    parser.add_option("--xml", dest = "xml",
                      default = os.path.join(os.path.dirname(__file__),
                                             "pxe.xml"),
                      help = "xml file to configure pxe boot environment")
    parser.add_option("--add", dest = "add", nargs = 3,
                      help = """add new machine to xml file.
(hostname, macaddress, ip)""")
    parser.add_option("--generate-dhcp", dest = "generate_dhcp",
                      action = "store_true",
                      help = "generate dhcp file")
    parser.add_option("--prefix-dhcp-file", dest = "prefix_dhcp_file",
                      default = os.path.join(os.path.dirname(__file__),
                                             "dhcpd.conf.pre"),
                      help = """pxe_manager only generates host syntax.
if you want to create a full dhcpd.conf, you can specify a file to be a
prefix of dhcpd.conf""")
    parser.add_option("--pxe-filename", dest = "pxe_filename",
                      default = "pxelinux.0",
                      help = "file name of pxelinux.")
    parser.add_option("--pxe-server", dest = "pxe_server",
                      default = "192.168.101.153",
                      help = "the ip address of pxe server.")
    parser.add_option("--list", dest = "list",
                      action = "store_true",
                      help = "print the list of the machines registered")
    parser.add_option("--root", dest = "root",
                      nargs = 1,
                      default = "/data/tf/root",
                      help = "NFS root directory")
    
    (options, args) = parser.parse_args()
    return options

def open_xml(xml):
    if os.path.exists(xml):
        dom = minidom.parse(xml)
    else:
        dom = minidom.Document()
        root = dom.createElement("pxe")
        dom.appendChild(root)
    return dom

def write_xml(dom, xml):
    # write it to xml
    f = open(xml, "w")
    f.write(dom.toxml())
    f.close()

def find_machine_tag_by_hostname(dom, hostname):
    machines = dom.getElementsByTagName("machine")
    for m in machines:
        if m.getAttribute("name") == hostname:
            return m
    return False

def get_root_pxe(dom):
    return dom.childNodes[0]

def add_machine(hostname, mac, ip, xml):    # <machine name="hostname">
    #   <ip> 0.0.0.0 </ip>
    #   <mac> 00:00:00:00 </mac>
    # </machine>
    dom = open_xml(xml)
    root = get_root_pxe(dom)
    machine_tag = find_machine_tag_by_hostname(root, hostname)
    if machine_tag:
        root.removeChild(machine_tag)
    machine_tag = dom.createElement("machine")
    machine_tag.setAttribute("name", hostname)
    root.appendChild(machine_tag)
    ip_tag = dom.createElement("ip")
    mac_tag = dom.createElement("mac")
    ip_tag.appendChild(dom.createTextNode(ip))
    mac_tag.appendChild(dom.createTextNode(mac))
    machine_tag.appendChild(ip_tag)
    machine_tag.appendChild(mac_tag)
    write_xml(dom, xml)

def generate_dhcp(pxe_filename, pxe_server, prefix_dhcp_file, xml):
    dom = open_xml(xml)
    root = get_root_pxe(dom)
    generated_string = []
    machine_tags = root.getElementsByTagName("machine")
    for m in machine_tags:
        hostname = m.getAttribute("name")
        ip_tag = m.getElementsByTagName("ip")[0]
        mac_tag = m.getElementsByTagName("mac")[0]
        ip = ip_tag.childNodes[0].data.strip()
        mac = mac_tag.childNodes[0].data.strip()
        template = Template(DHCP_HOST_TMPL)
        host_str = template.substitute({"hostname": hostname,
                                        "ip": ip,
                                        "mac": mac,
                                        "pxe_server": pxe_server,
                                        "pxe_filename": pxe_filename})
        generated_string.append(host_str)
    if prefix_dhcp_file:
        f = open(prefix_dhcp_file)
        prefix_str = "".join(f.readlines())
    else:
        prefix_str = ""
    print prefix_str + "\n".join(generated_string)

def print_machine_list(xml):
    dom = open_xml(xml)
    root = get_root_pxe(dom)
    machine_tags = root.getElementsByTagName("machine")
    for m in machine_tags:
        hostname = m.getAttribute("name")
        ip_tag = m.getElementsByTagName("ip")[0]
        mac_tag = m.getElementsByTagName("mac")[0]
        ip = ip_tag.childNodes[0].data.strip()
        mac = mac_tag.childNodes[0].data.strip()
        print """%s:
  ip: %s
  mac: %s
""" % (hostname, ip, mac)
    
def main():
    options = parse_options()
    
    if options.add:
        add_machine(options.add[0], options.add[1], options.add[2],
                    options.xml)
    if options.generate_dhcp:
        generate_dhcp(options.pxe_filename,
                      options.pxe_server,
                      options.prefix_dhcp_file,
                      options.xml)
    if options.list:
        print_machine_list(options.xml)
        
if __name__ == "__main__":
    main()