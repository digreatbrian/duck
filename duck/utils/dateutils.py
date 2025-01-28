"""
Date and Time Utilities Module

Provides utility functions for working with dates and times, including formatting,
parsing, calculating time differences, and handling time zones. It also provides functions to get the current time in different formats,
including local time and Greenwich Mean Time (GMT).
"""
import time
import datetime


def seconds_to_minutes(secs):
    """
    Convert seconds to minutes.

    Args:
        secs (float): The number of seconds.

    Returns:
        float: The number of minutes.
    """
    return secs / 60


def seconds_to_hours(secs):
    """
    Convert seconds to hours.

    Args:
        secs (float): The number of seconds.

    Returns:
        float: The number of hours.
    """
    return secs / 3600


def seconds_to_days(secs):
    """
    Convert seconds to days.

    Args:
        secs (float): The number of seconds.

    Returns:
        float: The number of days.
    """
    return secs / 86400


def seconds_to_weeks(secs):
    """
    Convert seconds to weeks.

    Args:
        secs (float): The number of seconds.

    Returns:
        float: The number of weeks.
    """
    return secs / 604800


def seconds_to_months(secs):
    """
    Convert seconds to months.

    Args:
        secs (float): The number of seconds.

    Returns:
        float: The number of months.
    """
    return secs / 2.628e6


def seconds_to_years(secs):
    """
    Convert seconds to years.

    Args:
        secs (float): The number of seconds.

    Returns:
        float: The number of years.
    """
    return secs / 3.154e7


def minutes_to_seconds(mins):
    """
    Convert minutes to seconds.

    Args:
        mins (float): The number of minutes.

    Returns:
        float: The number of seconds.
    """
    return mins * 60


def hours_to_seconds(hrs):
    """
    Convert hours to seconds.

    Args:
        hrs (float): The number of hours.

    Returns:
        float: The number of seconds.
    """
    return hrs * 3600


def days_to_seconds(days):
    """
    Convert days to seconds.

    Args:
        days (float): The number of days.

    Returns:
        float: The number of seconds.
    """
    return days * 86400


def weeks_to_seconds(weeks):
    """
    Convert weeks to seconds.

    Args:
        weeks (float): The number of weeks.

    Returns:
        float: The number of seconds.
    """
    return weeks * 604800


def months_to_seconds(months):
    """
    Convert months to seconds.

    Args:
        months (float): The number of months.

    Returns:
        float: The number of seconds.
    """
    return months * 2.628e6


def years_to_seconds(yrs):
    """
    Convert years to seconds.

    Args:
        yrs (float): The number of years.

    Returns:
        float: The number of seconds.
    """
    return yrs * 3.154e7


def datetime_difference(date_x: datetime.datetime,
                        date_y: datetime.datetime) -> dict:
    """
    Get the difference between two datetime objects (date_x and date_y).

    Args:
        date_x (datetime.datetime): The first datetime object.
        date_y (datetime.datetime): The second datetime object.

    Returns:
        dict: A dictionary containing the difference in years, months, weeks, days, hours, minutes, and seconds.

    Raises:
        ValueError: If either date_x or date_y is not an instance of datetime.datetime.
    """
    if not isinstance(date_x, datetime.datetime):
        raise ValueError(
            "Argument date_x to 'datetime_difference' function should be an instance of datetime.datetime"
        )

    if not isinstance(date_y, datetime.datetime):
        raise ValueError(
            "Argument date_y to 'datetime_difference' function should be an instance of datetime.datetime"
        )

    _diff = date_x - date_y
    try:
        s = _diff.total_seconds()
    except AttributeError:
        s = days_to_seconds(_diff.days)

    dt = {
        "years": 0,
        "months": 0,
        "weeks": 0,
        "days": 0,
        "hours": 0,
        "minutes": 0,
        "seconds": 0,
    }

    def convert(secs):
        """
        Convert seconds to a dictionary of time units.

        Args:
            secs (float): The number of seconds.
        """
        real_t = seconds_to_years(secs)
        if real_t >= 0.99:
            t = round(real_t)
            dt["years"] = t
            secs = years_to_seconds(real_t - t)

        real_t = seconds_to_months(secs)
        if real_t >= 1:
            t = round(real_t)
            dt["months"] = t
            secs = months_to_seconds(real_t - t)

        real_t = seconds_to_weeks(secs)
        if real_t >= 1:
            t = round(real_t)
            dt["weeks"] = t
            secs = weeks_to_seconds(real_t - t)

        real_t = seconds_to_days(secs)
        if real_t >= 1:
            t = round(real_t)
            dt["days"] = t
            secs = days_to_seconds(real_t - t)

        real_t = seconds_to_hours(secs)
        if real_t >= 1:
            t = round(real_t)
            dt["hours"] = t
            secs = hours_to_seconds(real_t - t)

        real_t = seconds_to_minutes(secs)
        if real_t >= 1:
            t = round(real_t)
            dt["minutes"] = t
            secs = minutes_to_seconds(real_t - t)

        if secs >= 1:
            dt["seconds"] = round(secs)

    convert(s)
    return dt


def datetime_difference_upto_now(previous_datetime: datetime.datetime) -> dict:
    """
    Get the difference between a previous_datetime object up to now.

    Args:
        previous_datetime (datetime.datetime): The previous datetime object.

    Returns:
        dict: A dictionary containing the difference in years, months, weeks, days, hours, minutes, and seconds.

    Raises:
        ValueError: If previous_datetime is not an instance of datetime.datetime.
    """
    if not isinstance(previous_datetime, datetime.datetime):
        raise ValueError(
            "Argument previous_datetime to 'datetime_difference_upto_now' function should be an instance of datetime.datetime"
        )
    now = datetime.datetime.now(previous_datetime.tzinfo)
    return datetime_difference(now, previous_datetime)


def build_readable_date(date_: dict, one_date=False) -> str:
    """
    Build a readable date from a dictionary of datetime values.

    Args:
        date_ (dict): A dictionary containing the difference in years, months, weeks, days, hours, minutes, and seconds.
        one_date (bool): If True, return only the first non-zero date component.

    Returns:
        str: A readable date string.

    Raises:
        KeyError: If the dictionary does not contain all the required keys.
    """
    r = []
    try:
        years = date_["years"]
        months = date_["months"]
        weeks = date_["weeks"]
        days = date_["days"]
        hours = date_["hours"]
        minutes = date_["minutes"]
        seconds = date_["seconds"]

        if years:
            if years == 1:
                r.append(f"{years} year")
            else:
                r.append(f"{years} years")

        if months:
            if months == 1:
                r.append(f" {months} month")
            else:
                r.append(f" {months} months")

        if weeks:
            if weeks == 1:
                r.append(f" {weeks} week")
            else:
                r.append(f" {weeks} weeks")

        if days:
            if days == 1:
                r.append(f" {days} day")
            else:
                r.append(f" {days} days")

        if hours:
            if hours == 1:
                r.append(f" {hours} hour")
            else:
                r.append(f" {hours} hours")

        if minutes:
            if minutes == 1:
                r.append(f" {minutes} minute")
            else:
                r.append(f" {minutes} minutes")

        if seconds:
            if seconds == 1:
                r.append(f" {seconds} second")
            else:
                r.append(f" {seconds} seconds")

        if len(r) >= 2:
            if one_date:
                return (r[0]).strip()
            return (r[0] + r[1]).strip()

        elif len(r) == 1:
            return r[0].strip()

        else:
            return "Just now"

    except KeyError:
        raise KeyError(
            "Argument date_ for 'build_readable_date' function should have all the keys from 'years' up to 'seconds'"
        )


def format_date(date: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Formats a given datetime object into a string with the specified format.

    Args:
        date (datetime): The datetime object to format.
        format_str (str): The format string.

    Returns:
        str: The formatted date string.
    """
    return date.strftime(format_str)


def parse_date(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime.datetime:
    """
    Parses a date string into a datetime object using the given format.

    Args:
        date_str (str): The date string to parse.
        format_str (str): The format string.

    Returns:
        datetime: The parsed datetime object.
    """
    return datetime.datetime.strptime(date_str, format_str)


def calculate_date_diff(start_date: datetime, end_date: datetime) -> datetime.timedelta:
    """
    Calculates the difference between two datetime objects.

    Args:
        start_date (datetime): The start date.
        end_date (datetime): The end date.

    Returns:
        timedelta: The difference between the two dates.
    """
    return end_date - start_date


def convert_timezone(date: datetime, from_timezone: str, to_timezone: str) -> datetime.datetime:
    """
    Converts a datetime object from one time zone to another.

    Args:
        date (datetime): The datetime to convert.
        from_timezone (str): The original time zone (e.g., "UTC").
        to_timezone (str): The target time zone (e.g., "US/Eastern").

    Returns:
        datetime: The converted datetime object.
    """
    import pytz
    
    from_zone = pytz.timezone(from_timezone)
    to_zone = pytz.timezone(to_timezone)

    # Set the time zone for the original date
    date = from_zone.localize(date)

    # Convert to the target time zone
    return date.astimezone(to_zone)


def local_date() -> str:
    """
    Returns the current local date and time in a formatted string.

    The format is: "Day, DD Mon YYYY HH:MM:SS".

    Returns:
        str: The formatted local date and time.
    """
    timestamp = time.time()
    weekdayname = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    monthname = [
        None,
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    year, month, day, hh, mm, ss, wd, y, z = time.localtime(timestamp)
    localtime = "%s, %02d %3s %04d %02d:%02d:%02d" % (
        weekdayname[wd],
        day,
        monthname[month],
        year,
        hh,
        mm,
        ss,
    )
    return localtime


def short_local_date() -> str:
    """
    Returns the current local date and time in a short formatted string.

    The format is: "DD/MM/YYYY HH:MM:SS".

    Returns:
        str: The formatted local date and time.
    """
    return time.strftime("%d/%m/%Y %H:%M:%S")


def django_short_local_date() -> str:
    """
    Returns the current local date and time in a short django formatted string.

    The format is: "DD/Mon/YYYY HH:MM:SS".

    Returns:
        str: The formatted local date and time.
    """
    return time.strftime("%d/%b/%Y %H:%M:%S")


def gmt_date() -> str:
    """
    Returns the current Greenwich Mean Time (GMT) in a formatted string.

    The format is: "Day, DD Mon YYYY HH:MM:SS GMT".

    Returns:
        str: The formatted GMT date and time.
    """
    timestamp = time.time()
    weekdayname = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    monthname = [
        None,
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
    gmt_time_str = f"{weekdayname[wd]}, {day:02d} {monthname[month]} {year:04d} {hh:02d}:{mm:02d}:{ss:02d} GMT"
    return gmt_time_str
