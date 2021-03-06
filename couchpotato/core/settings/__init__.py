from __future__ import with_statement
from couchpotato.api import addApiView
from couchpotato.core.event import addEvent, fireEvent
from couchpotato.core.helpers.encoding import isInt, toUnicode
from couchpotato.core.helpers.request import getParams, jsonified
from couchpotato.core.helpers.variable import mergeDicts, tryInt
import ConfigParser
import os.path
import time


class Settings():

    options = {}
    types = {}

    def __init__(self):

        addApiView('settings', self.view)
        addApiView('settings.save', self.saveView)

    def setFile(self, config_file):
        self.file = config_file

        self.p = ConfigParser.RawConfigParser()
        self.p.read(config_file)

        from couchpotato.core.logger import CPLog
        self.log = CPLog(__name__)

        self.connectEvents()

    def parser(self):
        return self.p

    def sections(self):
        return self.p.sections()

    def connectEvents(self):
        addEvent('settings.options', self.addOptions)
        addEvent('settings.register', self.registerDefaults)
        addEvent('settings.save', self.save)

    def registerDefaults(self, section_name, options = {}, save = True):
        self.addSection(section_name)
        for option_name, option in options.iteritems():
            self.setDefault(section_name, option_name, option.get('default', ''))

            if option.get('type'):
                self.setType(section_name, option_name, option.get('type'))

        if save:
            self.save(self)

    def set(self, section, option, value):
        return self.p.set(section, option, value)

    def get(self, option = '', section = 'core', default = '', type = None):
        try:

            try: type = self.types[section][option]
            except: type = 'unicode' if not type else type

            if hasattr(self, 'get%s' % type.capitalize()):
                return getattr(self, 'get%s' % type.capitalize())(section, option)
            else:
                return self.getUnicode(section, option)

        except:
            return default

    def getEnabler(self, section, option):
        return self.getBool(section, option)

    def getBool(self, section, option):
        try:
            return self.p.getboolean(section, option)
        except:
            return self.p.get(section, option)

    def getInt(self, section, option):
        try:
            return self.p.getint(section, option)
        except:
            return tryInt(self.p.get(section, option))

    def getUnicode(self, section, option):
        value = self.p.get(section, option)
        return toUnicode(value).strip()

    def getValues(self):
        values = {}
        for section in self.sections():
            values[section] = {}
            for option in self.p.items(section):
                (option_name, option_value) = option
                values[section][option_name] = self.get(option_name, section)
        return values

    def save(self):
        with open(self.file, 'wb') as configfile:
            self.p.write(configfile)

        self.log.debug('Saved settings')

    def addSection(self, section):
        if not self.p.has_section(section):
            self.p.add_section(section)

    def setDefault(self, section, option, value):
        if not self.p.has_option(section, option):
            self.p.set(section, option, value)

    def setType(self, section, option, type):
        if not self.types.get(section):
            self.types[section] = {}

        self.types[section][option] = type

    def addOptions(self, section_name, options):

        if not self.options.get(section_name):
            self.options[section_name] = options
        else:
            options['groups'] = self.options[section_name].get('groups') + options.get('groups')
            self.options[section_name] = mergeDicts(self.options[section_name], options)

    def getOptions(self):
        return self.options


    def view(self):

        return jsonified({
            'options': self.getOptions(),
            'values': self.getValues()
        })

    def saveView(self):

        params = getParams()

        section = params.get('section')
        option = params.get('name')
        value = params.get('value')

        # See if a value handler is attached, use that as value
        new_value = fireEvent('setting.save.%s.%s' % (section, option), value, single = True)

        self.set(section, option, new_value if new_value else value)
        self.save()

        return jsonified({
            'success': True,
        })
