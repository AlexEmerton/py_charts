#!/usr/bin/env python
#
# Copyright (c) 2015 Corey Goldberg
# License: MIT


import collections
import textwrap
import plotly
import plotly.graph_objs as go

from selenium import webdriver


class PageLoadTimer:

    def __init__(self, driver):
        """
            takes:
                'driver': webdriver instance from selenium.
        """
        self.driver = driver
        self.times = None

        self.jscript = textwrap.dedent("""
            var performance = window.performance || {};
            var timings = performance.timing || {};
            return timings;
            """)

    def inject_timing_js(self):
        timings = self.driver.execute_script(self.jscript)
        return timings

    def get_event_times(self):
        timings = self.inject_timing_js()
        # the W3C Navigation Timing spec guarantees a monotonic clock:
        #  "The difference between any two chronologically recorded timing
        #   attributes must never be negative. For all navigations, including
        #   subdocument navigations, the user agent must record the system
        #   clock at the beginning of the root document navigation and define
        #   subsequent timing attributes in terms of a monotonic clock
        #   measuring time elapsed from the beginning of the navigation."
        # However, some navigation events produce a value of 0 when unable to
        # retrieve a timestamp.  We filter those out here:
        good_values = [epoch for epoch in timings.values() if epoch != 0]
        # rather than time since epoch, we care about elapsed time since first
        # sample was reported until event time.  Since the dict we received was
        # inherently unordered, we order things here, according to W3C spec
        # fields.
        ordered_events = ('navigationStart', 'fetchStart', 'domainLookupStart',
                          'domainLookupEnd', 'connectStart', 'connectEnd',
                          'secureConnectionStart', 'requestStart',
                          'responseStart', 'responseEnd', 'domLoading',
                          'domInteractive', 'domContentLoadedEventStart',
                          'domContentLoadedEventEnd', 'domComplete',
                          'loadEventStart', 'loadEventEnd'
                          )
        event_times = ((event, timings[event] - min(good_values)) for event in ordered_events if event in timings)
        self.times = collections.OrderedDict(event_times)
        return self.times

    def plot(self, filename):
        plotly.offline.plot({
            "data": [go.Bar(
                labels=list(self.times.keys())[5:],
                values=list(self.times.values())[5:]
            )]
        }, auto_open=False, filename='plots/{}.html'.format(str(filename)))

    @staticmethod
    def plot_all(plots):
        traces = []

        for plot in plots:
            traces.append(go.Bar(
                x=list(plot.keys())[5:],
                y=list(plot.values())[5:],
                name=plot['name']
            ))

        layout = go.Layout(
            barmode='group'
        )

        fig = go.Figure(traces, layout)
        plotly.offline.plot(fig, filename='grouped-bar.html')


if __name__ == '__main__':
    url = 'https://hub-test.octopuscash.com'
    plots = []

    for x in range(10):
        driver = webdriver.Firefox(executable_path='D:\Alex\Desktop\Work\geckodriver-v0.24.0-win64\geckodriver.exe')
        driver.delete_all_cookies()

        driver.get(url)
        timer = PageLoadTimer(driver)
        times = timer.get_event_times()
        print(times)
        # timer.plot(x)
        times['name'] = '{}.html'.format(str(x))
        driver.quit()

        plots.append(times)

    timer.plot_all(plots)
