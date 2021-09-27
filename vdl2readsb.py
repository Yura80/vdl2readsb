#!/usr/bin/env python3
import logging
import json
import gzip
import re
import sys
import argparse
import time
import socket
from datetime import datetime

import vdl2parsedefs


class VDL2MsgParser:
    parsedefs = vdl2parsedefs.parsedefs
    re_parse_pos = re.compile(r'(-?)([01]?\d{2})(\d{2})\.?(\d)$')

    def __init__(self, input, flight_as_callsign=True, parse_location='all', db=None):
        self.logger = logging.getLogger(__name__)
        self.flight_as_callsign = flight_as_callsign
        self.parse_location = parse_location
        self.db = db
        self.reset()
        self.decode(input)

    def reset(self):
        self.jmsg = {}

        self.valid = False
        self.empty = True

        self.type = 8
        self.addr = None
        self.reg = ''
        self.date = ''
        self.time = ''

        self.flight = ''
        self.callsign = ''
        self.alt = ''
        self.speed = ''
        self.track = ''
        self.lat = ''
        self.lon = ''
        self.vrate = ''
        self.squawk = ''
        self.onground = 0

        self.dep_airport = ''
        self.dst_airport = ''
        self.eta = ''

        self.msg_text = ''
        self.msg_label = ''

    def parsePos(self, spos, format='dd', div=1):
        result = ''
        try:
            dtrans = ''.maketrans(
                {'N': '', 'S': '-', 'E': '', 'W': '-', ' ': ''})
            spos = str(spos).translate(dtrans).strip()
            if format in ('dm', 'dms'):
                match = re.search(self.re_parse_pos, spos)
                if match:
                    (sign, d, m, s) = match.group(1, 2, 3, 4)
                    if format == 'dm':
                        m = m + '.' + s
                        s = 0
                    result = round(float(d) + float(m)/60 + float(s)/3600, 5)
                    result *= -1 if sign == '-' else 1
            else:
                result = float(spos)/div
        except Exception as e:
            logger.warning('Error parsing coordinates "%s": ', spos, e)
        return result

    def fixAddrReg(self):
        if self.addr:
            self.addr = self.addr.upper()
        if self.addr == 'FFFFFF':
            self.addr = ''
        if len(self.addr) == 5:
            self.addr = '0' + self.addr

        dbaddr = None
        if self.db and self.reg:
            dbaddr = self.db.reg2icao(self.reg)
            if not dbaddr:
                self.logger.warning('reg2icao: not found "%s"', self.reg)
            else:
                self.logger.debug('reg2icao: %s -> %s', self.reg, self.addr)

        if not self.addr:
            if dbaddr:
                self.addr = dbaddr

        if self.db and self.addr:
            dbreg = self.db.icao2reg(self.addr)
            if not dbreg:
                self.logger.warning(
                    'unknown icao hex: "%s", reg: "%s"', self.addr, self.reg)
            elif self.reg and self.reg != dbreg and self.reg.replace('-', '') != dbreg.replace('-', ''):
                self.logger.warning(
                    'reg mismatch: hex: "%s", db-reg: "%s", msg-reg: "%s"', self.addr, dbreg, self.reg)
            self.reg = dbreg or self.reg

    def decode(self, input, type=None):
        try:
            self.jmsg = json.loads(input) if isinstance(input, str) else input
            if 'vdl2' not in self.jmsg:
                if 'fromHex' in self.jmsg:
                    return self.decodeAirframesIo(self.jmsg)
                else:
                    return False
            avlc = self.jmsg['vdl2']['avlc']
            if avlc['src']['type'] != 'Aircraft':
                return False
            self.addr = avlc['src']['addr']
            self.onground = 1 if avlc['src']['status'] != 'Airborne' else 0
            mtime = datetime.utcfromtimestamp(
                int(self.jmsg['vdl2']['t']['sec']))
            self.date = mtime.strftime('%Y/%m/%d')
            self.time = '{}.{:03d}'.format(mtime.strftime(
                "%H:%M:%S"), int(self.jmsg['vdl2']['t']['usec'])//1000)

            if 'acars' in avlc:
                self.decodeAcars(avlc['acars'])
            if 'xid' in avlc:
                self.decodeXid(avlc['xid'])

            self.valid = True
            return True
        except Exception as e:
            self.logger.warning('Error decoding message: "%s"', input)
            self.logger.warning('%s', e)
            self.valid = False
            return False

    def decodeAcars(self, acars):
        self.reg = (acars.get('reg') or self.reg).lstrip('.')
        self.fixAddrReg()
        self.flight = acars.get('flight') or self.flight
        if self.flight_as_callsign:
            self.callsign = self.flight
        self.type = 1
        mtext = acars.get('msg_text', acars.get('message', {}).get('text', ''))
        self.msg_text = mtext
        self.msg_label = acars.get('label', '')
        if self.msg_text:
            self.empty = False

        if 'arinc622' in acars:
            # ADS-C
            arinc622 = acars['arinc622']
            if 'adsc' in arinc622:
                adsc = arinc622['adsc']
                for tag in adsc.get('tags', []):
                    if 'basic_report' in tag and self.parse_location in ('all', 'adsc'):
                        br = tag['basic_report']
                        self.alt = br.get('alt', '')
                        self.lat = br.get('lat', '')
                        self.lon = br.get('lon', '')
                        self.type = 3
        elif 'miam' in acars:
            miam_acars = acars['miam'].get('single_transfer', {}).get(
                'miam_core', {}).get('data', {}).get('acars', {})
            if len(miam_acars) > 0:
                self.decodeAcars(miam_acars)
        elif mtext:
            self.decodeAcarsMsg(mtext, acars.get('label'))

    def decodeAirframesIo(self, afmsg):
        self.addr = (afmsg.get('fromHex') or '').upper()
        self.reg = (afmsg.get('tail') or self.reg).lstrip('.')
        self.fixAddrReg()
        if not self.addr:
            self.valid = False
            return False

        if 'linkDirection' in afmsg and afmsg['linkDirection'] == 'uplink':
            self.valid = False
            return False

        mtime = datetime.strptime(afmsg['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
        self.date = mtime.strftime('%Y/%m/%d')
        self.time = mtime.strftime("%H:%M:%S.%f")[:-3]

        self.reg = (afmsg.get('reg') or self.reg).lstrip('.')
        self.flight = afmsg.get('flightNumber') or self.flight
        if self.flight_as_callsign:
            self.callsign = self.flight
        self.type = 1
        self.msg_text = afmsg.get('text', '')
        self.msg_label = afmsg.get('label', '')

        if self.parse_location in ('all', 'adsc'):
            self.lat = afmsg.get('latitude') or ''
            self.lon = afmsg.get('longitude') or ''
            self.alt = afmsg.get('altitude') or ''

        if self.msg_text:
            self.decodeAcarsMsg(self.msg_text, self.msg_label)

        if self.lat or self.lon or self.alt:
            if self.lat:
                self.lat = round(self.lat, 5)
            if self.lon:
                self.lon = round(self.lon, 5)
            self.empty = False

        self.valid = True

    def decodeAcarsMsg(self, mtext, label):
        if mtext[0] == '#' and mtext[3] == 'B':
            mtext = mtext[4:]
        for pdef in self.parsedefs:
            if pdef.get('label') == label or not pdef.get('label'):
                if 'pos_re' in pdef and self.parse_location == 'all':
                    match = re.search(pdef['pos_re'], mtext)
                    if match:
                        (slat, slon) = match.group(1, 2)
                        self.lat = self.parsePos(slat, pdef.get(
                            'pos_format'), pdef.get('pos_div', 1))
                        self.lon = self.parsePos(slon, pdef.get(
                            'pos_format'), pdef.get('pos_div', 1))
                        self.type = 3
                if 'alt_re' in pdef and self.parse_location == 'all':
                    match = re.search(pdef['alt_re'], mtext)
                    if match:
                        self.alt = int(match.group(1)) * \
                            pdef.get('alt_mul', 1)
                if 'dep_re' in pdef:
                    match = re.search(pdef['dep_re'], mtext)
                    if match:
                        self.dep_airport = match.group(1).strip()
                if 'dst_re' in pdef:
                    match = re.search(pdef['dst_re'], mtext)
                    if match:
                        self.dst_airport = match.group(1).strip()
                if 'eta_re' in pdef:
                    match = re.search(pdef['eta_re'], mtext)
                    if match:
                        self.eta = match.group(1)

    def decodeXid(self, xid):
        for param in xid.get('vdl_params', []):
            if param.get('name') == 'ac_location' and 'value' in param and self.parse_location == 'all':
                pval = param['value']
                self.alt = pval.get('alt', '')
                if self.alt != '' and int(self.alt) > 60000:
                    self.alt = ''
                # location is too rough
                # self.lat = round(pval.get('loc', {}).get('lat', ''), 5)
                # self.lon = round(pval.get('loc', {}).get('lon', ''), 5)
                self.type = 3
                self.empty = False
            if param.get('name') == 'dst_airport' and 'value' in param:
                self.dst_airport = param['value'].strip('.')
                self.empty = False

    def toSBS(self):
        if not self.valid:
            return None
        return (
            f'MSG,{self.type},1,1,{self.addr},1,'
            f'{self.date},{self.time},{self.date},{self.time},'
            f'{self.callsign},{self.alt},{self.speed},{self.track},'
            f'{self.lat},{self.lon},{self.vrate},{self.squawk},,,,{self.onground},'
            f'{self.reg},{self.flight},{self.dep_airport},{self.dst_airport},{self.eta}'
        )


class AircraftDB:
    def __init__(self, path):
        with gzip.open(path) as f:
            self.db = json.load(f)
            self.revdb = {}
            tmpdb = {}
            for reg, addr in self.db.items():
                self.revdb[addr] = reg
                if '-' in reg:
                    ndreg = reg.replace('-', '')
                    if ndreg not in self.db and ndreg not in tmpdb:
                        tmpdb[ndreg] = addr
            self.db.update(tmpdb)

    def reg2icao(self, reg):
        icao = self.db.get(reg)
        return icao

    def icao2reg(self, icao):
        reg = self.revdb.get(icao)
        return reg


class MsgPrinter:
    def __init__(self, args):
        self.logger = logging.getLogger(__name__)
        self.args = args
        if args.out_tcp:
            self.conn = False
            self.host, self.port = args.out_tcp.split(':', 1)

    def printMsg(self, msg):
        if not msg.valid or (msg.empty and self.args.no_empty):
            return

        if self.args.out_file:
            print(msg.toSBS(), file=self.args.out_file)
            self.args.out_file.flush()

        if self.args.out_tcp:
            try:
                if not self.conn:
                    logger.debug('connecting to %s, port %s',
                                 self.host, self.port)
                    self.sock = socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.connect((self.host, int(self.port)))
                    self.conn = True
                self.sock.send((msg.toSBS() + '\n').encode())
            except Exception as e:
                logger.warning(e)
                self.conn = False

        self.logger.debug('%s', json.dumps(msg.jmsg))
        if msg.msg_text:
            self.logger.info('reg: "%s", flight: "%s", label: "%s", text: "%s"',
                             msg.reg, msg.flight, msg.msg_label, msg.msg_text)
        self.logger.info('%s\n', msg.toSBS())


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--no-empty', dest='no_empty', action='store_true',
                           help='suppress empty messages')
    argparser.add_argument('--no-callsign', dest='callsign', action='store_false',
                           help='don''t output IATA flight number as callsign')
    argparser.add_argument('--location', dest='location', required=False, default='all', type=str,
                           choices=['all', 'adsc', 'none'],
                           help='what kind of location data to parse')
    argparser.add_argument('-d', '--debug', dest='debug', action='store_true',
                           help='print messages and debug info to stderr')
    argparser.add_argument('--db', dest='db', required=False, type=str,
                           default='/usr/local/share/tar1090/git-db/db/regIcao.js', help='path to aircraft db')
    argparser.add_argument('--input', dest='input', required=False, default='stdin', type=str,
                           choices=['stdin', 'zmq', 'airframesio'],
                           help='input data source')
    argparser.add_argument('--out-file', dest='out_file', required=False, type=argparse.FileType('w', encoding='UTF-8'),
                           help='where to send decoded data')
    argparser.add_argument('--out-tcp', dest='out_tcp', required=False, type=str,
                           help='TCP output connection address')
    argparser.add_argument('--zmq-port', dest='zmq_port', required=False, default=5556, type=int,
                           help='ZMQ port number to listen to (if --input=zmq)')
    args = argparser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger(__name__)

    if not args.out_file and not args.out_tcp:
        args.out_file = sys.stdout

    mprinter = MsgPrinter(args)

    db = AircraftDB(args.db)

    if args.input == 'airframesio':
        import socketio
        while True:
            try:
                sio = socketio.Client()

                @sio.on('newMessages')
                def catch_all(event):
                    for m in event:
                        msg = VDL2MsgParser(
                            m, args.callsign, args.location, db=db)
                        mprinter.printMsg(msg)
                if not sio.connected:
                    sio.connect('https://api.airframes.io')
                sio.wait()
            except Exception as e:
                logger.warning(e)
                time.sleep(3)
    elif args.input == 'zmq':
        # stolen from https://github.com/varnav/zvdl2json/blob/main/zvdl2json.py
        import zmq
        context = zmq.Context()
        s = context.socket(zmq.SUB)
        binding = f'tcp://*:{args.zmq_port}'
        s.bind(binding)
        logger.info('ZMQ listening at:', binding)
        s.setsockopt_string(zmq.SUBSCRIBE, '')
        while True:
            data = s.recv_json()
            msg = VDL2MsgParser(data, args.callsign, args.location, db=db)
            mprinter.printMsg(msg)
    else:
        for line in sys.stdin:
            msg = VDL2MsgParser(line, args.callsign, args.location, db=db)
            mprinter.printMsg(msg)
