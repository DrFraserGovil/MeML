import datetime
import meml.util
import re

class Date:
    def __init__(self,value):
        if "@" not in value:
            self.Date = value
            self.WasParsed = False
        else:
            self.RequiresRewrite = True
            base_date = datetime.date.today()
            value = value.lower()
            if value == "@today":
                date = base_date
            elif value == "@yesterday":
                date = (base_date - datetime.timedelta(days=1))
            else:
                match = re.match(r'@today\s*([+-])\s*(\d+)', value)

                if match:
                    operator = match.group(1)
                    days = int(match.group(2))
                    delta = datetime.timedelta(days=days)
                    if operator == "+":
                        date = base_date + delta
                    else:
                        date = base_date - delta
                else:
                    meml.util.FatalError(f"Could not parse date command '{value}' -- accepted are @yesterday and @today (+/- integer)")
            self.Date = f"{date.day}/{date.month}/{date.year}"
            self.WasParsed = True
    def Rewrite(self):
        return self.Date
    def Format(self):
        try:
            # Parse the d/m/y string
            day, month, year = map(int, self.Date.split('/'))
            dt = datetime.date(year, month, day)
            
            # Determine the ordinal suffix
            if 11 <= day <= 13:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
                
            # Format: "Monday 9th February 2026"
            return dt.strftime(f"%A %B {day}{suffix}, %Y")
        except (ValueError, AttributeError):
            # Fallback if the date is malformed or not a standard d/m/y
            return self.Date