"""Local host lifetime, never a remotely selectable operation."""
import math


def duration_for(duration=None, application=False):
    if type(application) is not bool or (application and duration is not None):
        raise ValueError('invalid_host_lifetime')
    if application:return None
    duration=70 if duration is None else duration
    if type(duration) is not int or not 1<=duration<=75:
        raise ValueError('invalid_host_lifetime')
    return duration


def end_at(started,duration):
    return math.inf if duration is None else started+duration


def finish_collector(collector, pending=lambda:None):
    """Never exit while our collector is still active; no forced termination."""
    result=collector.stop(3)
    if not result.stopped:
        pending()
        while not result.stopped:result=collector.stop(0.25)
    return result
