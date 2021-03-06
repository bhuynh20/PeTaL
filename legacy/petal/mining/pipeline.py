from time import time, sleep
from pprint import pprint
import json
import inspect
import os

from importlib import reload

import scheduler
import modules


class PipelineInterface:
    '''
    This class defines an interface to a data mining server. It allows modules and settings to the scheduler to be updated dynamically without stopping processing.
    '''
    def __init__(self):
        self.scheduler = scheduler.Scheduler()
        self.times = dict()
        self.load_settings()
        self.reload_modules()

    def reload_modules(self):
        global modules # Required to reload the module at the global level
        modules = reload(modules)
        for name, item in inspect.getmembers(modules):
            if inspect.isclass(item):
                filetime = os.stat('modules/{}.py'.format(name)).st_mtime
                if name not in self.times or self.times[name] != filetime:
                    self.times[name] = filetime
                    if name not in self.blacklist:
                        print('Reloading module: ', name)
                        self.scheduler.schedule(item())

    def load_settings(self, filename='settings.json'):
        with open('settings.json', 'r') as infile:
            settings = json.load(infile)
        pprint(settings)
        for k, v in settings.items():
            if k.startswith('scheduler:'):
                k = k.replace('scheduler:', '')
                setattr(self.scheduler, k, v)
            elif k.startswith('pipeline:'):
                k = k.replace('pipeline:', '')
                setattr(self, k, v)

    def start_server(self):
        start = time()
        self.reload_modules()
        self.scheduler.start()
        try:
            while True:
                self.scheduler.check_added()
                sleep(self.sleep_time)
                self.scheduler.display()
                duration = time() - start
                if duration > self.reload_time:
                    print('Reloading settings', flush=True)
                    start = time()
                    self.load_settings()
                    self.reload_modules()
        finally:
            self.scheduler.stop()


if __name__ == '__main__':
    interface = PipelineInterface() # The entry point for mining server
    interface.start_server()


