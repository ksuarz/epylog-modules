#!/usr/bin/python -tt

import re
import string
import epylog
from epylog import Result

class annoy_mod(epylog.module.PythonModule):
    def __init__(self, opts, logger):
        epylog.module.PythonModule.__init__(self)
        self.logger = logger
        rc = re.compile
        self.regex_map = {
            ##
            # GConf, the bane of all existence
            #
            rc('gconfd.*: Failed to get lock.*Failed to create'): self.gconf,
            rc('gconfd.*: Error releasing lockfile'): self.gconf,
            rc('gconfd.*: .* Could not lock temporary file'): self.gconf,
            rc('gconfd.*: .* another process has the lock'): self.gconf,
            ##
            # Look for fatal X errors. These usually occur when
            # someone logs out, but if they repeat a lot, then it's
            # something that should be looked at.
            #
            rc('Fatal X error'): self.fatalx,
            ##
            # Look for sftp activity.
            #
            rc('sftp-server.*:'): self.sftp,
            rc('subsystem request for sftp'): self.sftp,
            ##
            # Look for misc floppy errors (vmware likes to leave those).
            #
            rc('floppy0:|\(floppy\)'): self.floppy_misc,
            ##
            # Look for ypserv errors
            #
            rc('ypserv.*: refused connect'): self.ypserv
        }
        self.ypserv_re = rc('from\s(.*):\d+\sto\sprocedure\s(\S+)')
        try: self.report_wrap = opts['report_wrap']
        except KeyError: self.report_wrap = '<table border="0">%s</table>'
        try: self.report_line = opts['report_line']
        except KeyError: self.report_line = '<tr><td>%s:</td><td>%s</td></tr>'

    def gconf(self, linemap):
        msg = 'Gconf locking errors'
        return Result((linemap['system'], msg), linemap['multiplier'])

    def fatalx(self, linemap):
        msg = 'Fatal X errors'
        return Result((linemap['system'], msg), linemap['multiplier'])

    def sftp(self, linemap):
        msg = 'SFTP activity'
        return Result((linemap['system'], msg), linemap['multiplier'])

    def floppy_misc(self, linemap):
        msg = 'misc floppy errors'
        return Result((linemap['system'], msg), linemap['multiplier'])
    
    def ypserv(self, linemap):
        mo = self.ypserv_re.search(linemap['message'])
        if mo:
            fromip, proc = mo.groups()
            ypclient = self.gethost(fromip)
            msg = '%s denied from %s' % (proc, ypclient)
            return Result((linemap['system'], msg), linemap['multiplier'])
        return None            

    def finalize(self, rs):
        logger = self.logger
        logger.put(5, '>annoy_mod.finalize')
        report = ''
        for system in rs.get_distinct(()):
            mymap = rs.get_submap((system,))
            messages = []
            for message in mymap.keys():
                messages.append('%s(%d)' % (message[0], mymap[message]))
            report += self.report_line % (system, string.join(messages, ', '))
        report = self.report_wrap % report
        return report
