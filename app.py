#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import yfinance as yf
import pandas as pd
import pickle
from datetime import datetime
import pytz

# Load the trained model
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)


# In[ ]:


import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()


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

if st.button("Predict"):
    
    if ticker == "":
        st.error("No ticker entered.")
    else:
        ticker_data = find_cases(ticker)
        feature_columns = ['MA_10', 'MA_50', 'MA_100', 'MA_200']
        input_data = ticker_data[feature_columns].iloc[[-1]]

        if input_data.empty:
            st.warning("Not enough data to calculate MAs.")
        else:
            prediction = model.predict(input_data)[0]
            if prediction == 1:
                msg = f"chances are HIGH for {ticker}"
            else:
                msg = f"chances are low for {ticker}"

            ### adding to database the prediction details
            # Define IST timezone
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            db.collection("prediction_logs").add({
                "ticker": str(ticker),
                "prediction": int(prediction),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S")
            })
            
            st.success(f"📈 Result is {msg}")


# # Paper Trading Code

# In[ ]:


st.title("Paper-Trading Arena : Enter your paper-trade below")
st.write("No Login, No Signup!!!! Only a single password used to place/access your trades")

ticker_for_paper_trade = st.text_input("Enter Ticker for Paper-Trade (e.g., DLF.NS):")
password = st.text_input("Enter your unique identification code (please note if this exists in our db, it will be matched to that trade, \
else new id will be created:")
order_options = ['Buy', 'Sell']
order = st.selectbox("Enter Order Type (buy/sell):", order_options)
quantity_options = [1, 10, 100, 500, 1000, 2000, 5000, 10000]
quantity = st.selectbox("Enter Quantity (eg 100, 200):", quantity_options)
st.write("Please Note: Price will be either the current market price or the last traded price on Exchange if closed")


# In[ ]:


def find_price(ticker):
    try:
        data = yf.download(ticker, period='1y', interval='1d')
        return round(data.iloc[-1,0],1)
    except:
        return "na"


# In[ ]:


if st.button("Place Order"):
    if ticker_for_paper_trade == '' or password == '' or order == '' or quantity == '':
        st.error("Incorrect trade. Please re-enter correct details in an orderly manner.")
    else:
        last_price = find_price(ticker_for_paper_trade)

        if last_price == "na":
            st.warning("No price available for this ticker.")
        else:
            ### adding to database the prediction details
            # Define IST timezone
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            db.collection("paper_trading_data").add({
                "Ticker": str(ticker_for_paper_trade),
                "password": str(password),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "Order": str(order),
                "Quantity": int(quantity),
                "Price": int(last_price)
            })
            
            st.success(f"📈 Trade placed for {ticker_for_paper_trade} at price of {last_price}")


#### fetching tradebook code
def fetch_data(user_id):
    if user_id:
        # Query Firestore for trades with matching user_id
        trades_ref = db.collection("paper_trading_data").where("password", "==", user_id)
        results = trades_ref.stream()
        
        # Convert results to list of dicts
        trades_list = [doc.to_dict() for doc in results]
        
        if trades_list:
            # Convert list of dicts to DataFrame
            df = pd.DataFrame(trades_list)
    return df

st.title("Use your password, to look at your trade book")
# Input for user ID
user_id = st.text_input("Enter User ID:")

if st.button("Fetch Trades"):
    if user_id:
        try:
            # Query Firestore for trades with matching user_id
            trades_ref = db.collection("paper_trading_data").where("user_id", "==", user_id)
            results = trades_ref.stream()
    
            # Convert results to list of dicts
            trades_list = [doc.to_dict() for doc in results]
    
            if trades_list:
                # Convert list of dicts to DataFrame
                df = pd.DataFrame(trades_list)
    
                st.success(f"Showing {len(df)} trades for User ID: {user_id}")
                
                # Display as interactive DataFrame
                st.dataframe(df)
    
            else:
                st.warning("No trades found for this ID.")
        except:
            st.warning("Invalid ID.")
