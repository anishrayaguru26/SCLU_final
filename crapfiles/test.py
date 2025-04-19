#import datetime
from datetime import datetime
#2024-07-03 09:15:00+05:30
dtformat=(f'%Y-%m-%d %H:%M:%S+05:30')
x = datetime.strptime('2024-07-03 09:15:00+05:30',dtformat)

print(x)

