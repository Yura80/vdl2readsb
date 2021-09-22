#!/usr/bin/env python3
import logging
import json
import re
import sys
import argparse
from datetime import datetime

import vdl2parsedefs

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class VDL2MsgParser:
    parsedefs = vdl2parsedefs.parsedefs
    re_parse_pos = re.compile(r'(-?)(0?\d{2})(\d{2})\.?(\d{1,2})')

    def __init__(self, input, flight_as_callsign=True, parse_location='all'):
        self.flight_as_callsign = flight_as_callsign
        self.parse_location = parse_location
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

    def decode(self, input):
        try:
            self.jmsg = json.loads(input)
            if 'vdl2' not in self.jmsg:
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
                self.decodeACARS(avlc['acars'])
            if 'xid' in avlc:
                self.decodeXID(avlc['xid'])

            self.valid = True
            return True
        except Exception as e:
            logger.warning('Error decoding message: "%s"', input)
            logger.warning('%s', e)
            self.valid = False
            return False

    def decodeACARS(self, acars):
        self.reg = acars.get('reg', self.reg).lstrip('.')
        self.flight = acars.get('flight', self.flight)
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
                self.decodeACARS(miam_acars)
        else:
            for pdef in self.parsedefs:
                if pdef.get('label') == acars.get('label') or not pdef.get('label'):
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

    def decodeXID(self, xid):
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


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--no-empty', dest='no_empty', action='store_true',
                           help='suppress empty messages')
    argparser.add_argument('--no-callsign', dest='callsign', action='store_false',
                           help='don''t output IATA flight number as callsign')
    argparser.add_argument('--location', dest='location', required=False, default='all', type=str,
                           choices=['all', 'adsc', 'none'],
                           help='what kind of location data to parse')
    args = argparser.parse_args()

    logger.setLevel(logging.DEBUG)
    for line in sys.stdin:
        msg = VDL2MsgParser(line, args.callsign, args.location)
        if not msg.valid or (msg.empty and args.no_empty):
            continue
        print(msg.toSBS())
        sys.stdout.flush()
        logger.debug('%s', json.dumps(msg.jmsg))
        if msg.msg_text:
            logger.info('reg: "%s", flight: "%s", label: "%s", text: "%s"',
                        msg.reg, msg.flight, msg.msg_label, msg.msg_text)
        logger.info('%s\n', msg.toSBS())
