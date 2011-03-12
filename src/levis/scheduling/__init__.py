"""
Scheduling application, essential characteristics:

    - 365 days divided in 12 months.
    - No specialcase handling of leap-years.
    - Supports recurring events on the scheme:
        Daily
        Weekly
        Monthly by day in the month
        Monthly by day in the week
        Yearly by date (month, day of month)
    - Mutually exclusive events to avoid conflicts.

"""