import datetime
import dateutil.tz


FAR_FUTURE = datetime.datetime.max.replace(tzinfo=dateutil.tz.tzutc())
DISTANT_PAST = datetime.datetime.min.replace(tzinfo=dateutil.tz.tzutc())
