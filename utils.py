from config import utils, channels
import pandas as pd 
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pytz import timezone

def save_member_list(members, path):
    rows = []
    for member in members:
      rows.append({"Nickname": member.display_name, "Username": member.name})
    df = pd.DataFrame(rows, columns=["Nickname", "Username"])
    df.to_csv(path, index=False)

def get_countdown():
    move_in = "2021-08-21 08:00:00"
    move_in_datetime = datetime.strptime(move_in, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone('US/Eastern'))
    diff = relativedelta(move_in_datetime, datetime.now(timezone('US/Eastern')))
    day_label = "day" if diff.days == 1 else "days"
    hours_label = "hour" if diff.hours == 1 else "hours"
    if diff.days >= 0 and diff.hours >= 0:
        return "Move-in: {0.days} {1} {2.hours} {3}".format(diff, day_label, diff, hours_label)
    return "Move-in: 0 days 0 hours"

async def clear_channel(name):
    async for message in channels[name].history(limit=None):
        await message.delete()

if __name__ == "__main__":
    print(get_countdown())