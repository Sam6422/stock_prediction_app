APP-LINK - https://simple-stock-prediction-app1.streamlit.app/

Objective - can a stock finish the month with a 2% gain over the close from the last date till 10th of that month?

Methodology - using a 30,000 rows dataset taking 10 years data into account is used for finding the accuracy of this prediction. The ML model underneath predicts the probability of occurence of True (1) or False (0).
The predictions gets logged into a NoSQL firebase database in the form of (Ticker-Prediction-Date-Time). Apart from these 4 datapoints, nothing else is stored in our storage.

--------------------------------------------------------------------------------------------------------------------------
How to use this?

STEP1- insert any ticker from yahoofinance (eg DLF.NS).

STEP2- just press "Predict" button

STEP3- result - "HIGH" indicates >2% return is likely, while "low" indicates it is unlikely.
--------------------------------------------------------------------------------------------------------------------------

NOTE- the reference point from which the >2% return chance is considered is the final trading day till 10th of the current month.

Disclaimer - this is only an educational project. Please do not use it for making any trading or financial decisions.
