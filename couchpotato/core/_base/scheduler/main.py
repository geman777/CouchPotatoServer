from apscheduler.scheduler import Scheduler as Sched
from couchpotato.core.event import addEvent
from couchpotato.core.logger import CPLog
from couchpotato.core.plugins.base import Plugin
import logging

log = CPLog(__name__)


class Scheduler(Plugin):

    crons = {}
    intervals = {}
    started = False

    def __init__(self):

        sl = logging.getLogger('apscheduler.scheduler')
        sl.disabled = True

        addEvent('schedule.cron', self.cron)
        addEvent('schedule.interval', self.interval)
        addEvent('schedule.start', self.start)
        addEvent('schedule.restart', self.start)

        addEvent('app.load', self.start)
        addEvent('app.shutdown', self.stop)

        self.sched = Sched(misfire_grace_time = 60)

    def remove(self, identifier):
        for type in ['interval', 'cron']:
            try:
                self.sched.unschedule_job(getattr(self, type)[identifier]['job'])
                log.debug('%s unscheduled %s' % (type.capitalize(), identifier))
            except:
                pass

    def start(self):

        # Stop all running
        self.stop()

        # Crons
        for identifier in self.crons:
            try:
                self.remove(identifier)
                cron = self.crons[identifier]
                job = self.sched.add_cron_job(cron['handle'], day = cron['day'], hour = cron['hour'], minute = cron['minute'])
                cron['job'] = job
            except ValueError, e:
                log.error("Failed adding cronjob: %s" % e)

        # Intervals
        for identifier in self.intervals:
            try:
                self.remove(identifier)
                interval = self.intervals[identifier]
                job = self.sched.add_interval_job(interval['handle'], hours = interval['hours'], minutes = interval['minutes'], seconds = interval['seconds'], repeat = interval['repeat'])
                interval['job'] = job
            except ValueError, e:
                log.error("Failed adding interval cronjob: %s" % e)

        # Start it
        self.sched.start()
        self.started = True

    def stop(self):

        if self.started:
            self.sched.shutdown()

        self.started = False

    def cron(self, identifier = '', handle = None, day = '*', hour = '*', minute = '*'):
        log.info('Scheduling "%s", cron: day = %s, hour = %s, minute = %s' % (identifier, day, hour, minute))

        self.remove(identifier)
        self.crons[identifier] = {
            'handle': handle,
            'day': day,
            'hour': hour,
            'minute': minute,
        }

    def interval(self, identifier = '', handle = None, hours = 0, minutes = 0, seconds = 0, repeat = 0):
        log.info('Scheduling %s, interval: hours = %s, minutes = %s, seconds = %s, repeat = %s' % (identifier, hours, minutes, seconds, repeat))

        self.remove(identifier)
        self.intervals[identifier] = {
            'handle': handle,
            'repeat': repeat,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
        }
