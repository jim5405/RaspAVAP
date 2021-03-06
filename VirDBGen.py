# this script only run on python 2.7

import sys
import re
import urllib2
import random
import hashlib
import os

print """\n# Malware analysis related scripts:
# https://github.com/notnop
# Happy reversing\n"""

# Global vars

try:
    samples_nr = int(sys.argv[1])
except Exception as exception:
    print exception
    samples_nr = 101

useragent = {'User-Agent': "Your daily malware source"}

final_list = []  # malware address colector

print """\nYou want latest %d samples from:
\t# http://vxvault.net
\t# http://malc0de.com
\t# http://tracker.h3x.eu
""" % (samples_nr)

print "Searching..."


# VxVault - aka siri
def vxvault(nr_samples):
    global final_list

    lista_url = []
    adresa = "http://vxvault.net/ViriList.php?s=0&m=" + str(nr_samples)

    try:
        req = urllib2.Request(adresa, None, useragent)
        continut_pagina = urllib2.urlopen(req).read()

        # find all malware address
        pagina = continut_pagina.split("\r")
        for i in pagina:
            match = re.search(
                "href='ViriFiche\.php\?ID=[\d]+'>(.+)</a></TD>", i)
            if match:
                temp_mal_address = match.group(1)
                if not re.search("[\d]{1,2}-[\d]{1,2}", temp_mal_address):

                    # add malware address
                    lista_url.append(temp_mal_address)

        final_list += lista_url

    except Exception as e:
        print "vxvault: " + str(e)

    print "[*]   VxVault - Done ", len(lista_url)


# Malcode
def Malcode(nr_adrese):
    global final_list

    lista_url = []

    if nr_adrese <= 50:
        pags = 1
    else:
        pags = (nr_adrese / 50) + 1

    # browsing pages
    for i in range(0, pags):
        adresa = "http://malc0de.com/database/?&page=" + str(i)

        try:
            req = urllib2.Request(adresa, None, useragent)
            continut = urllib2.urlopen(req, timeout=60).read()
            b = re.findall("<td>[\d]{4}-[\d]{2}-[\d]{2}<\/td>\n.+\n", continut)
            if b:
                for i in b:
                    data = re.search("<td>([\d]{4}-[\d]{2}-[\d]{2})<\/td>", i)
                    malware = re.search("\t<td>(.+)<\/td>", i)
                    if data and malware:
                        malware = re.sub("<br\/>", "", malware.group(1))
                        lista_url.append(malware)
        except Exception as e:
            print "Malcode: " + str(e)

    final_list += lista_url

    print "[*]   Malcode - Done ", len(lista_url)


def h3x_get(nr_adrese):
    lst = []

    adresa = "http://tracker.h3x.eu/"
    req = urllib2.Request(adresa, None, useragent)
    continut_pagina = urllib2.urlopen(req).readlines()

    # print continut_pagina

    for linie in continut_pagina:
        adrese = re.findall("href='/site/([A-Za-z0-9%\._-]+)", linie)
        lst += adrese
        if len(lst) >= nr_adrese:
            return lst
    return lst


def h3x_clean(x=1000):
    global final_list
    lista = h3x_get(x)
    new_list = []

    # cleanig
    for i in lista:
        i = re.sub("%3A", ":", i)
        i = re.sub("%2F", "/", i)
        new_list.append(i)

    final_list += new_list

    print "[*]   tracker.h3x - Done ", len(new_list)


# Colect samples address:
Malcode(samples_nr)
vxvault(samples_nr)
h3x_clean(samples_nr)


final_list = list(set(final_list))
print "\nUnique addresses: ", len(final_list)

print "Downloading..."


# generate random string
charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def get_random_word(a):
    word = ''
    for i in range(a):
        word += random.choice(charset)
    return word


# md5 file
def md5Checksum(filePath):
    fh = open(filePath, 'rb')
    m = hashlib.md5()
    while True:
        data = fh.read(8192)
        if not data:
            break
        m.update(data)
    return m.hexdigest()


def download_file(address, dldagent={'User-Agent': "Chromium"},
                  destination_folder="/home/pi/samples/",
                  logs="logs.txt"):

    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # file name
    f_name = destination_folder + str(get_random_word(8))

    # try to download sample
    try:

        # check if url start with "http://
        if address[:7] != "http://":
            address = "http://" + address

        # construct url and set timeout
        req = urllib2.Request(address, None, dldagent)
        u = urllib2.urlopen(req, timeout=59).read()  # timeout 1 min

        # write to file
        f = open(f_name, 'wb')
        f.write(u)
        f.close()

        # write info to logs
        with open(destination_folder + logs, "a") as handle:
            md5hash = md5Checksum(f_name)
            handle.write(md5hash + "\t" + f_name + "\t" + address + "\n")
            handle.close

        print "\n" + "Downloaded: " + f_name,

    except Exception as e:
        # adding error to logs
        with open(destination_folder + logs, "a") as handle:
            handle.write("\nError: " + address + "\t" + str(e) + "\n")
            handle.close()
        pass


for mal in final_list:
    download_file(mal)
os.system("python /home/pi/yabin/yabin.py -y /home/pi/samples/ | cat >> /home/pi/custom_rule.yara")
