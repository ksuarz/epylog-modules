"""
This module handles generating the reports.
"""
##
# Copyright (C) 2003 by Duke University
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$
#
# @Author Konstantin Ryabitsev <icon@linux.duke.edu>
# @version $Date$
#

import epylog
import os
import re
import time
import tempfile

if 'mkdtemp' not in dir(tempfile):
    ##
    # Must be python < 2.3
    #
    del tempfile
    import mytempfile as tempfile

from publishers import *

class ModuleReport:
    """
    A small helper class to hold Module HTML reports.
    """
    def __init__(self, name, htmlreport):
        self.name = name
        self.htmlreport = htmlreport
        
class Report:
    """
    This helper class holds the contents of a report before it is
    published using publisher classes.
    """
    def __init__(self, config, logger):
        logger.put(5, '>Report.__init__')
        logger.put(3, 'Starting Report object intialization')
        self.logger = logger
        ##
        # publishers:     a tuple of publisher objects
        # filt_fh:        where the filtered strings from modules will go
        # useful:         tells epylog if the report is of any use or not.
        # module_reports: module reports will be put here eventually
        #
        self.publishers = []
        self.filt_fh = None
        self.useful = 0
        self.module_reports = []
        
        self.tmpprefix = config.tmpprefix
        self.runtime = time.localtime()
        sec = 'report'
        try: title = config.get(sec, 'title')
        except: title = '@@HOSTNAME@@ system events: @@LOCALTIME@@'
        try: self.template = config.get(sec, 'template').strip()
        except:
            raise epylog.ConfigError('Report template not specified', logger)
        if not os.access(self.template, os.R_OK):
            msg = 'Report template "%s" is not readable' % self.template
            raise epylog.AccessError(msg, logger)
        try: self.unparsed = config.getboolean(sec, 'include_unparsed')
        except: self.unparsed = 1
        try: publishers = config.get(sec, 'publishers')
        except:
            msg = 'No publishers defined in "%s"' % sec
            raise epylog.ConfigError(msg, logger)

        logger.put(3, 'Title as defined in config is: "%s"' % title)
        hregex = re.compile('@@HOSTNAME@@')
        tregex = re.compile('@@LOCALTIME@@')
        if hregex.search(title):
            import socket
            hostname = socket.gethostname()
            logger.put(3, 'Regexing @@HOSTNAME@@ into "%s"' % hostname)
            title = re.sub(hregex, hostname, title)
        if tregex.search(title):
            timestr = time.strftime('%c', self.runtime)
            logger.put(3, 'Regexing @@LOCALTIME@@ into "%s"' % timestr)
            title = re.sub(tregex, timestr, title)
        self.title = title
        logger.put(3, 'Final title is: "%s"' % self.title)
        
        logger.put(3, 'template=%s' % self.template)
        logger.put(3, 'unparsed=%d' % self.unparsed)
        if self.unparsed:
            logger.put(3, 'Creating a temporary file for filtered strings')
            tempfile.tmpdir = self.tmpprefix
            filen = tempfile.mktemp('FILT')
            self.filt_fh = open(filen, 'w+')
            logger.put(3, 'Filtered strings file created in "%s"' % filen)

        logger.put(3, 'Publishers: "%s"' % publishers)
        logger.put(3, 'Initializing publishers')
        for sec in publishers.split(','):
            sec = sec.strip()
            logger.put(3, 'Looking for section definition "%s"' % sec)
            if sec not in config.sections():
                message = 'Required publisher section "%s" not found' % sec
                raise epylog.ConfigError(message, logger)
            logger.put(3, 'Looking for method declaration')
            try:
                method = config.get(sec, 'method')
            except:
                msg = 'Publishing method not found in "%s"' % sec
                raise epylog.ConfigError(msg, logger)
            logger.put(3, 'Found method "%s"' % method)
            if method == 'file':
                publisher = FilePublisher(sec, config, logger)
            elif method == 'mail':
                publisher = MailPublisher(sec, config, logger)
            else:
                msg = 'Publishing method "%s" not supported' % method
                raise epylog.ConfigError(msg, logger)
            self.publishers.append(publisher)            
        logger.put(3, 'Finished with Report object initialization')
        logger.put(5, '<Report.__init__')

    def append_module_report(self, module_name, module_report):
        """
        Appends a module report.
        """
        logger = self.logger
        logger.put(5, '>Report.append_module_report')
        if len(module_report) > 0:
            modrep = ModuleReport(module_name, module_report)
            logger.put(3, 'Appending report for "%s"' % module_name)
            logger.put(5, 'report follows')
            logger.put(5, module_report)
            self.module_reports.append(modrep)
            self.useful = 1
        else:
            logger.put(3, 'Module report is empty, ignoring')
        logger.put(5, '<Report.append_module_report')

    def append_filtered_strings(self, module_name, fsfh):
        """
        Adds filtered strings to the report.
        """
        logger = self.logger
        logger.put(5, '>Report.append_filtered_strings')
        if self.filt_fh is None:
            logger.put(3, 'No open filt_fh, ignoring')
            return
        fsfh.seek(0, 2)
        if fsfh.tell() != 0:
            logger.put(3, 'Appending filtered strings from module "%s"'
                       % module_name)
            logger.put(5, 'Doing chunked read from %s to %s' %
                       (fsfh.name, self.filt_fh.name))
            fsfh.seek(0)
            while 1:
                chunk = fsfh.read(epylog.CHUNK_SIZE)
                if len(chunk):
                    self.filt_fh.write(chunk)
                    logger.put(5, 'wrote %d bytes' % len(chunk))
                else:
                    logger.put(5, 'EOF reached')
                    break
            self.useful = 1
        else:
            logger.put(3, 'Filtered Strings are empty, ignoring')
        logger.put(5, '<Report.append_filtered_strings')

    def set_stamps(self, stamps):
        """
        Set the timestamps of the report -- the starting and the ending one.
        """
        logger = self.logger
        logger.put(5, '>Report.set_stamps')
        [self.start_stamp, self.end_stamp] = stamps
        logger.put(5, 'start_stamp=%d' % self.start_stamp)
        logger.put(5, 'end_stamp=%d' % self.end_stamp)
        logger.put(5, '<Report.set_stamps')

    def mk_unparsed_from_raw(self, rawfh):
        """
        This is only ever invoked if external modules were used. It takes
        raw strings, fgreps them against the weeded strings, and returns
        all the strings that weren't touched by modules.
        """
        logger = self.logger
        logger.put(5, '>Report.mk_unparsed_from_raw')
        if self.filt_fh is None: return None
        unparsed = ''
        self.filt_fh.seek(0, 2)
        if self.filt_fh.tell():
            logger.puthang(1, 'Doing memory-friendly grep')
            tempfile.tempdir = self.tmpprefix
            weedfh = open(tempfile.mktemp('WEED'), 'w+')
            self._memory_friendly_grep(rawfh, weedfh)
            logger.endhang(3)
            logger.puthang(3, 'Reading in weeded logs')
            weedfh.seek(0)
            unparsed = weedfh.read()
            weedfh.close()
            logger.endhang(1)
        logger.put(5, '<Report.mk_unparsed_from_raw')
        return unparsed
    
    def publish(self, rawfh, unparsed):
        """
        Publishes the report using all enabled publishers.
        """
        logger = self.logger
        logger.put(5, '>Report.publish')
        if self.filt_fh is not None:
            if unparsed is None: unparsed = self.mk_unparsed_from_raw(rawfh)
        else: unparsed = ''
        logger.puthang(3, 'Reading in the template file "%s"' % self.template)
        fh = open(self.template)
        template = fh.read()
        fh.close()
        logger.endhang(3)
        starttime = time.strftime('%c', time.localtime(self.start_stamp))
        endtime = time.strftime('%c', time.localtime(self.end_stamp))
        for publisher in self.publishers:
            logger.puthang(3, 'Invoking publisher "%s"' % publisher.name)
            publisher.publish(template,
                              starttime,
                              endtime,
                              self.title,
                              self.module_reports,
                              unparsed,
                              rawfh)
            logger.endhang(3)


    def is_report_useful(self):
        """
        Returns 0 if the report is not useful (no new strings in logs).
        """
        return self.useful

    def _memory_friendly_grep(self, rawfh, weedfh):
        """
        Utility method to do a memory-friendly grep. Fgrepping huge
        logfiles may use up a LOT of memory and cause the process to
        run away. This only uses a certain amount of lines at a time,
        making sure that only a small fraction of memory is ever used.

        This is only invoked if external modules were used.
        """
        logger = self.logger
        logger.put(5, '>Report._memory_friendly_grep')
        tempfile.tmpdir = self.tmpprefix
        temp_raw = tempfile.mktemp('TEMPRAW')
        temp_filt = tempfile.mktemp('TEMPFILT')
        temp_weed = tempfile.mktemp('TEMPWEED')
        logger.put(5, 'temp_raw=%s' % temp_raw)
        logger.put(5, 'temp_filt=%s' % temp_filt)
        logger.put(5, 'temp_weed=%s' % temp_weed)
        logger.put(5, 'Kerchunking %s into %s' % (rawfh.name, temp_raw))
        temp_rawfh = open(temp_raw, 'w')
        rawfh.seek(0)
        while 1:
            chunk = rawfh.read(epylog.CHUNK_SIZE)
            if chunk:
                temp_rawfh.write(chunk)
                logger.put(5, 'wrote %d bytes' % len(chunk))
            else:
                logger.put(5, 'Reached EOF')
                break
        temp_rawfh.close()

        self.filt_fh.seek(0, 2)
        filtfh_size = self.filt_fh.tell()
        logger.put(5, 'filtfh_size=%d' % filtfh_size)
        self.filt_fh.seek(0)
        donesize = 0
        while 1:
            logger.put(5, 'new iteration of filt_fh')
            if self.filt_fh.tell() == filtfh_size:
                logger.put(5, 'No more lines in filt_fh')
                break
            if os.access(temp_weed, os.F_OK):
                logger.put(5, 'Moving %s to %s' % (temp_weed, temp_raw))
                os.rename(temp_weed, temp_raw)
            try:
                os.remove(temp_filt)
            except:
                pass
            temp_filtfh = open(temp_filt, 'w')
            s = self._dump_lines(self.filt_fh, temp_filtfh, epylog.GREP_LINES)
            temp_filtfh.close()
            donesize = donesize + s
            done = (donesize*100)/filtfh_size
            self._call_fgrep(temp_raw, temp_filt, temp_weed)
            logger.put(1, '%d%% done' % done)
            if not os.stat(temp_weed).st_size:
                logger.put(5, 'Nothing left after weeding')
                break
        logger.put(5, 'Reading weeding results from temp_weed')
        temp_weedfh = open(temp_weed)
        weedfh.write(temp_weedfh.read())
        temp_weedfh.close()
        logger.put(3, 'Done doing memory friendly grep')
        logger.put(5, '<Report._memory_friendly_grep')

    def _dump_lines(self, fromfh, tofh, number):
        """
        Dumps lines from one fh into another.
        """
        logger = self.logger
        logger.put(5, '>Report._dump_lines')
        logger.put(5, 'reading %d lines from "%s"' % (number, fromfh.name))
        chunksize = 0
        for i in range(number):
            line = fromfh.readline()
            if not line:
                logger.put(5, 'end of file reached at iter %d' % i)
                break
            chunksize = chunksize + len(line)
            tofh.write(line)
        writenum = i + 1
        logger.put(3, 'wrote %d lines into %s' % (writenum, tofh.name))
        logger.put(5, 'total size of chunk: %d' % chunksize)
        logger.put(5, '<Report._dump_lines')
        return chunksize

    def _call_fgrep(self, raw, filt, weed):
        """
        Makes a syscall to grep.
        """
        logger = self.logger
        logger.put(5, '>Report._call_fgrep')
        fgrep = '/bin/fgrep -v -f %s %s > %s' % (filt, raw, weed)
        logger.put(3, 'Calling fgrep with command "%s"' % fgrep)
        ecode = os.system(fgrep)
        logger.put(5, 'ecode=%d' % ecode)
        if ecode and ecode != 256:
            msg = 'Call to fgrep for weed failed with exit code %d' % ecode
            raise epylog.SysCallError(msg, logger)
        logger.put(5, '<Report._call_fgrep')
        
