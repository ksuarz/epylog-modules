Epylog
======
Epylog is a new log notifier and parser which runs periodically out of
cron, looks at your logs, processes the entries in order to present
them in a more comprehensive format, and then provides you with the
output. It is written specifically with large network clusters in mind
where a lot of machines (around 50 and upwards) log to the same
loghost using syslog or syslog-ng.

Alternatively, Epylog can be invoked from the command line and provide
a log report based on a certain provided time period. In this case it
relies on syslog timestamps to find the offsets, as opposed to the
end-of-log offsets stored during the last run, though this behavior is
not as reliable and is easily thwarted by skewed clocks.

AUTHOR
-------
Konstantin Ryabitsev <icon@linux.duke.edu>

OBTAINING
----------
http://linux.duke.edu/projects/epylog/

BUGS
------
Please file the bugs in the Epylog bugzilla:
http://devel.linux.duke.edu/bugzilla/

MAILING LIST
-------------
The mailing list for epylog-related questions is:
epylog@linux.duke.edu. Please send all your inquires there.

LICENSE
--------
Copyright (C) 2001-2004 by Duke University

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
 
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  
02111-1307, USA.

This license does not include files in the "modules" directory. They
are covered under different licenses (see further).

MODULES
--------
Modules are the parsing soul of epylog. For more info please see "man
epylog-modules". If you wrote a module, you are encouraged to
contribute it to the epylog so other people can make use of it. 
Please inquire on the list for more information.

MODULES LICENSE
----------------
Modules are considered a separate entity and are licensed to you as
per the licensing conditions mentioned individually within the source
of each module.

-- 
$Id$
