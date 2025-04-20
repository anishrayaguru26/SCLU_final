from datetime import date
from jugaad_data.nse import bhavcopy_save, bhavcopy_fo_save

# Download bhavcopy
path = "/Users/anishrayaguru/Desktop/SCLU/Trader_only_api"
#bhavcopy_save(date(2020,1,1), path)

# Download bhavcopy for futures and options
#bhavcopy_fo_save(date(2020,1,1), path)

# Download stock data to pandas dataframe
from jugaad_data.nse import stock_df
df = stock_df(symbol="SBIN", from_date=date(2025,1,1),
            to_date=date(2025,1,30), series="EQ")

print(df.head())