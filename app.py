#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import yfinance as yf
import pandas as pd
import pickle

# Load the trained model
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)



# In[ ]:


def find_cases(ticker):
    Ticker= ticker

    # step1- download data
    data = yf.download(Ticker, start='2015-01-01', end='2025-12-31', interval='1d')['Close']
    
    # step2- reset index
    data = data.reset_index()
    
    # step3- add year, month, day columns and insert to them
    data['year'] = [data.iloc[i,0].year for i in range(0,len(data))]
    data['month'] = [data.iloc[i,0].month for i in range(0,len(data))]
    data['day'] = [data.iloc[i,0].day for i in range(0,len(data))]
    
    # step4- add MAs
    data['ma_10'] = data[Ticker].rolling(window=10).mean()
    data['ma_50'] = data[Ticker].rolling(window=50).mean()
    data['ma_100'] = data[Ticker].rolling(window=100).mean()
    data['ma_200'] = data[Ticker].rolling(window=200).mean()

    result_dict = {
    'year': [],
    'month': [],
    '10th_price': [],
    '30th_price': [],
    'MA_10': [],
    'MA_50': [],
    'MA_100': [],
    'MA_200': []
    }

    ## step5- put buy,sell trades into a df for future use
    for row in range(200,len(data)):
        
        if data.iloc[row-1,4] <= 10 and  data.iloc[row,4] > 10:
            # phase = 'buy'
            result_dict['year'].append(data.iloc[row-1,2])
            result_dict['month'].append(data.iloc[row-1,3])
            result_dict['10th_price'].append(data.iloc[row-1,1])
            result_dict['MA_10'].append(0 if data.iloc[row-1,1] < data.iloc[row-1,5] else 1)
            result_dict['MA_50'].append(0 if data.iloc[row-1,1] < data.iloc[row-1,6] else 1)
            result_dict['MA_100'].append(0 if data.iloc[row-1,1] < data.iloc[row-1,7] else 1)
            result_dict['MA_200'].append(0 if data.iloc[row-1,1] < data.iloc[row-1,8] else 1)
    
        
        elif data.iloc[row-1,4] > 10 and  data.iloc[row,4] <= 10 and len(result_dict['10th_price']) > len(result_dict['30th_price']):
            # phase = 'sell'
            result_dict['30th_price'].append(data.iloc[row-1,1])
    
    
    ### suppose we are in middle of month, then end sell price is today's date
    if len(result_dict['10th_price']) != len(result_dict['30th_price']):
        result_dict['30th_price'].append(data.iloc[-1,1])

    # step6- Convert to DataFrame and add "Success" column
    df = pd.DataFrame.from_dict(result_dict)
    df['Ticker'] = Ticker
    df['success'] = [1 if df.iloc[row,2] < df.iloc[row,3] else 0 for row in range(0,len(df))]

    return df


# In[ ]:


st.title("Stock Movement Predictor 🚀")
ticker = st.text_input("Enter NSE Stock Ticker (e.g., DLF.NS):")

if ticker:
    # Fetch data
    
    if ticker == "":
        st.error("Could not fetch data for this ticker.")
    else:
        ticker_data = find_cases(ticker)
        feature_columns = ['MA_10', 'MA_50', 'MA_100', 'MA_200']
        input_data = ticker_data[feature_columns].iloc[[-1]]

        if input_data.empty:
            st.warning("Not enough data to calculate MAs.")
        else:
            prediction = model.predict(input_data)[0]
            st.success(f"📈 Success Probability: {prediction}")

