from . import core
import datetime

@core.app_template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    if value:
        return value.strftime(format)
    return ""
