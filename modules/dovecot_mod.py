#!/usr/bin/python -tt
"""
This module watches Dovecot, recording information about logins, disconnects,
and the like. Output gives a high-level view of all the disconnects and login
failures.
"""

import sys
import re

##
# This is for testing purposes, so you can invoke this from the
# modules directory. See also the testing notes at the end of the
# file.
#
sys.path.insert(0, '../py/')
from epylog import InternalModule

class dovecot_mod(InternalModule):

    def __init__(self, opts, logger):
        """
        Sets up the module, naturally.
        """
        InternalModule.__init__(self)
        self.logger = logger

        # For this mod, we'll use 5 as the default log level for general debug
        # statements and the like
        logger.put(5, 'Mod instantiated!');

        self.regex_map = {
            # Logins
            re.compile(r'imap-login:\slogin:', re.I)                    : self.login_imap,
            re.compile(r'pop3-login:\slogin:', re.I)                    : self.login_pop,

            # Logouts
            re.compile(r'imap\(\w*\): disconnected: logged out', re.I)  : self.logout_imap,
            re.compile(r'pop3\(\w*\): disconnected: logged out', re.I)  : self.logout_pop,

            # Disconnects and closed connections
            re.compile(r'disconnected:?\s(?:for)?\sinactivity', re.I)   : self.disc_inactivity,
            re.compile(r'disconnected:\sinternal\serror', re.I)         : self.disc_interr,
            re.compile(r'disconnected\sby\sserver', re.I)               : self.disc_server,
            re.compile(r'disconnected\sby\sclient', re.I)               : self.disc_client,
            re.compile(r'disconnected\sin\sidle', re.I)                 : self.disc_idle,
            re.compile(r'disconnected\sin\sappend', re.I)               : self.disc_append,
            re.compile(r'imap\(\w*\):\sconnection\sclosed', re.I)       : self.close_imap,
            re.compile(r'pop3\(\w*\):\sconnection\sclosed', re.I)       : self.close_pop,

            # Other things: failures, etc.
            re.compile(r'authenticated user not found', re.I)           : self.user_notfound,
            re.compile(r'auth error: userdb\(\)')
            re.compile(r'auth\sfail(?:ed)?', re.I)                      : self.auth_fail,
            re.compile(r'no\sauth\sattempt', re.I)                      : self.no_auth_atmpt,
            re.compile(r'(?:too\smany)?\s?invalid\simap', re.I)         : self.invalid_imap,
            re.compile(r'(?:disallowed)?\s?plaintext\sauth', re.I)      : self.disallow_ptxt,
            re.compile(r'\seof\s', re.I)                                : self.unex_eof,

            # Lines we choose to forcefully ignore
            re.compile(r'director:\serror', re.I)                       : self.ignore
        }

        # Useful strings for formatting the output
        self.report_table = '<table width="100%%" cellpadding="2">%s</table>'
        self.report_line = '<tr><td id="msg" width="90%%">%s</td><td id="mult">%s</td></tr><br/>'

    ##
    # Login routines
    #
    def login_imap(self, linemap):
        """
        Records successful IMAP logins.
        Log message: imap-login: Login: ...
        """
        return {('IMAP Login'): linemap['multiplier']}

    def login_pop(self, linemap):
        """
        Records successful POP logins.
        Log message: pop3-login: Login: ...
        """
        return {('POP3 Login'): linemap['multiplier']}

    ##
    # Logout routines
    #
    def logout_imap(self, linemap): 
        """
        Records success (i.e. no indication of failure) on IMAP logout.
        Log message: imap(<user>): Disconnected: Logged out
        """
        return {('IMAP Logout'): linemap['multiplier']}

    def logout_pop(self, linemap):
        """
        Records success (i.e. no indication of failure) on POP3 logout.
        Log message: pop3(<user>): Disconnected: Logged out
        """
        return {('POP Logout'): linemap['multiplier']}

    ##
    # Disconnects and connection closures
    #
    def disc_inactivity(self, linemap):
        """
        Catches disconnects due to inactivity.
        Log message: (<user>): Disconnected for inactivity
        """
        return {('disc_inactivity'): linemap['multiplier']}

    def disc_interr(self, linemap):
        """
        Catches unknown internal errors.
        Log message:    imap(<user>): Disconnected: Internal error occurred.
                        Refer to server log for more information.
        """
        return {('disc_interr'): linemap['multiplier']}

    def disc_server(self, linemap):
        """
        Catches disconnects by the server.
        Log message: Disconnected by server
        """
        return {('disc_server'): linemap['multiplier']}

    def disc_client(self, linemap):
        """
        Catches disconnects from the client side.
        Log message: Disconnected by client
        """
        return {('disc_client'): linemap['multiplier']};

    def disc_idle(self, linemap):
        """
        Catches disconnects due to idleness.
        Log message: Disconnected: disconnected in IDLE
        """
        return {('disc_idle'): linemap['multiplier']}

    def disc_append(self, linemap):
        """
        Catches failed append errors.
        Log message: Disconnected in APPEND
        """
        return {('disc_append'): linemap['multiplier']}

    def close_imap(self, linemap):
        """
        Catches closed IMAP connections.
        Log message: imap(<user>): Connection closed
        """
        return {('close_imap'): linemap['multiplier']}

    def close_pop(self, linemap):
        """
        Catches closed POP3 connections.
        Log message: pop3(<user>): Connection closed
        """
        return {('close_pop'): linemap['multiplier']}

    ##
    # Other failures
    #
    def auth_fail(self, linemap):
        """
        Occurs when disconnected due to an authentification failure.
        Log message: Disconnected (auth failed)
        """
        return {('auth_fail'): linemap['multiplier']}

    def no_auth_atmpt(self, linemap):
        """
        Log message: Aborted login (no auth attempts in <num> secs)
        Or: Disconnected (no auth attempts in <num> secs)
        """
        return {('no auth attempt'): linemap['multiplier']}

    def invalid_imap(self, linemap):
        """
        Catches disconnects due to invalid commands.
        Log message: imap(<user>): Disconnected: Too many invalid IMAP commands
        """
        return {('invalid imap'): linemap['multiplier']}

    def disallow_ptxt(self, linemap):
        """
        Occurs when someone tries something bad during auth.
        Log message: Aborted login (tried to use disallowed plaintext auth)
        """
        return {('disallow ptxt'): linemap['multiplier']}

    def unex_eof(self, linemap):
        """
        Catches eof errors.
        Log message: Unexpected eof
        """
        # TODO what the hell is the real unexpected eof message
        return {('unex eof'): linemap['multiplier']}


    ##
    # Happens
    #
    def ignore(self, linemap):
        """
        We purposely want to ignore these messages.
        Currently ignored log messages: Director errors
        """
        return {('Ignored'): linemap['multiplier']}

    ##
    # Returns the final report.
    # TODO. Let's hope that Epylog does its math correctly.
    #
    def finalize(self, resultset):
        report = []

        while True:
            try:
                key, mult = resultset.popitem()
                report.append(self.report_line % (key, mult))
            except KeyError:
                break

        final_report = ''.join(report)
        final_report = self.report_table % final_report
        return final_report

##
# This is useful when testing your module out.
# Invoke without command-line parameters to learn about the proper
# invocation.
#
if __name__ == '__main__':
    from epylog.helpers import ModuleTest
    ModuleTest(dovecot_mod, sys.argv)
