import pandas as pd
import time
import praw
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from time import sleep, perf_counter
from tqdm import tqdm
from dateutil.parser import parse
from json import dumps, loads
from kafka import KafkaProducer, KafkaConsumer
import random
from threading import Thread
import re
import emoji
from keras.models import load_model
from keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from keras.preprocessing.text import tokenizer_from_json
import numpy as np
import json
from influxdb_client import InfluxDBClient, Point, WriteOptions
import os
from collections import OrderedDict
from csv import DictReader
import reactivex as rx
from reactivex import operators as ops
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from datetime import datetime, timedelta
from application.realtime_analysis2 import real_time_Reddit_preprocessing, scrap_reddit_rt


i=0
mapp={}
LSTMs={}

def scrap_reddit(num_posts=365000, number_of_days=1):

    #reddit part
    reddit = praw.Reddit(
    client_id="jhJU7xIVl5fzppId4X0Adw",
    client_secret="iqKkX4dVpbccJSNIXuiV1x3QO2mixA",
    user_agent="stock_data/1.0 by Basic_Fix1900",
    )

    # Define the subreddit and search query
    subreddit_name = "all"  # You can change this to the subreddit you are interested in
    csv_label = "Apple"
    search_queries = ["Apple", "Iphone", "Macbook", "Ipad", "Imac", "IOS", "Apple watch"]
    num_posts/=len(search_queries)

    # Set the start and end dates for the time window
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=number_of_days)

    post_data = []
    for search_query in search_queries:
        print("search query: ", search_query)
        # Search for posts
        posts = reddit.subreddit(subreddit_name).search(
            query=search_query,
            sort="relevance",
            time_filter="year",
            syntax="lucene",
            limit=num_posts,
        )

        # Extract post information and append to the list
        p=1
        for post in posts:
            print("post: ", p)
            c=1
            post_date = datetime.utcfromtimestamp(post.created_utc)
            if start_date <= post_date <= end_date:
                for comment in post.comments:
                    print("comment: ", c)
                    if isinstance(comment, praw.models.Comment):
                        if "bot" in comment.body:
                            continue
                        comment_date = datetime.utcfromtimestamp(comment.created_utc)
                        if start_date <= comment_date <= end_date:
                            post_comments = {
                                "Comment_Created_UTC": comment_date,
                                "Comment_Body": comment.body,
                                "Comment_Score": comment.score,
                                "Post_Created_UTC": post_date,
                                "Post":post.title,
                                "Post_Score": post.score,
                                "Post_Num_Comments": post.num_comments,
                                "Post_URL": post.url,
                            }
                            post_data.append(post_comments)
                    c+=1
            if p%50==0:
                # Create a DataFrame from the list
                df = pd.DataFrame(post_data)
                # Save the DataFrame to a CSV file
                csv_file_path = f"reddit_comments_{subreddit_name}_{csv_label}_{num_posts}_year1.csv"
                df.to_csv(csv_file_path, index=False, encoding="utf-8")
            p+=1
            # Introduce a delay to avoid rate limiting
            time.sleep(0.1)  # You can adjust the delay as needed

    # Create a DataFrame from the list
    df = pd.DataFrame(post_data)
    print(df.columns)
    if not df.empty:
        df = df.sort_values("Comment_Created_UTC")

    # Save the DataFrame to a CSV file
    # csv_file_path = f"reddit_comments_{subreddit_name}_{csv_label}_{num_posts}_year_1.csv"
    # df.to_csv(csv_file_path, index=False, encoding="utf-8")
    # print(df)
    # print(f"Data saved to {csv_file_path}")
    
    return df

def scrap_data_dynamically(ticker, lastdate, numDays=1862, order="DESC"):
    url = "https://finance.yahoo.com/quote/"+ ticker +"/history"

    driver = webdriver.Chrome()
    driver.set_page_load_timeout(5)
    try:
        driver.get(url)
    except TimeoutException:
        driver.execute_script("window.stop();")

    driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
    start = 0
    finish = 4200
    columns = ["Date", "Close"]
    table = []
    pbar = tqdm(total = 100)
    lePas = int((1/numDays)*100)
    for i in range (1, 1862):
        if(i==numDays):
            break
        if (i-1)%100==0 and i!=1 :
            driver.execute_script(f'window.scrollTo({start},{finish});')
            start = finish
            finish += 4200
            sleep(1)
        try:
            date_ = driver.find_element(By.XPATH,f'//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[2]/table/tbody/tr[{i}]/td[1]/span').text
            # Convert date_ string to a datetime object
            date_object = datetime.strptime(date_, "%b %d, %Y")
            # Format the datetime object as "YYYY-MM-DD"
            formatted_date = date_object.strftime("%Y-%m-%d")
            # Convert lastdate string to a datetime object
            if type(lastdate) == str:
                lastdate = datetime.strptime(lastdate, "%Y-%m-%d")
            # Compare the datetime objects
            if lastdate >= date_object:
                break
            table.append(
                [
                    driver.find_element(By.XPATH,f'//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[2]/table/tbody/tr[{i}]/td[1]/span').text,
                    driver.find_element(By.XPATH,f'//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[2]/table/tbody/tr[{i}]/td[4]/span').text,
                ]
            )
        except NoSuchElementException:
            print(f"Only {i} days are availables !")
            break
        finally:
            sleep(0.3)
            pbar.update(lePas)
    pbar.close()

    driver.quit()

    AscDict=[]
    if order =='ASC':
        for i in range(len(table)-1,-1,-1):
            AscDict.append(table[i])
        table=AscDict
    scrapped_data = pd.DataFrame(table, columns=columns)

    return scrapped_data

def clean_data(scrapped_data):
    pbar = tqdm(total = 100)
    for date in scrapped_data["Date"]:
        date_formatted = parse(date)
        date_formatted= date_formatted.strftime("%Y-%m-%d")
        date_index = scrapped_data["Date"] == date
        scrapped_data["Date"].loc[date_index]= date_formatted
    pbar.update(50)
    for close_str in scrapped_data["Close"]:
        if(type(close_str)!= float):
            close_float = float(close_str.replace(',',''))
            close_index = scrapped_data["Close"] == close_str
            scrapped_data["Close"].loc[close_index] = close_float
    pbar.update(50)
    pbar.close()
    return scrapped_data

def load_data(ticker,lastdate, numDays=1862,order="DESC"):
    time_start = perf_counter()
    scrapped_data = scrap_data_dynamically(ticker=ticker , lastdate=lastdate, numDays=numDays,order=order)
    time_finish = perf_counter()
    print("\n\n\n\nDuration:",time_finish-time_start,"\n\n\n\n")
    cleaned_data = clean_data(scrapped_data)
    return cleaned_data

def scrap_yahoo_finance_data(ticker, lastdate):
    return load_data(ticker,lastdate=lastdate)

def compute_numdays(lastdate):
    today =  datetime.now()
    # date_obj1 = datetime.strptime(lastdate, "%Y-%m-%d")
    print(type(lastdate))
    date_obj1 = lastdate
    date_difference = today - date_obj1
    numDays = date_difference.days
    return numDays

def preprocess_text_with_stemming_and_lemmatization(text):
    global i
    if i % 100 == 0:
        print(i)
    i += 1
    # Replace contractions
    text = re.sub(r"won\'t", "will not", text)
    text = re.sub(r"can\'t", "can not", text)
    # Remove non-alphanumeric characters
    text = re.sub('[^a-zA-Z0-9]', ' ', text)
    # Remove emojis
    text = re.sub(emoji.get_emoji_regexp(), "", text)
    return text

def preprocessing_reddit(df):
    # df = pd.read_csv("reddit_comments_all_Apple_365000_year1.csv")
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    global i
    i=0   
    start_preprocessing = time.perf_counter()
    df["clean_Comment_Body"] = df["Comment_Body"].apply(preprocess_text_with_stemming_and_lemmatization)
    end_preprocessing = time.perf_counter()
    print("duration = ", end_preprocessing - start_preprocessing)
    return df

def computeCommentsWeights(row):
    global i
    global mapp
    print(i)
    i+=1
    min_value = mapp[('Comment_Score', 'min')][row['Comment_Created_UTC']] 
    max_value = mapp[('Comment_Score', 'max')][row['Comment_Created_UTC']]
    if min_value == max_value:
        return 1
    print("max_value: ", max_value) 
    print("min_value: ", min_value) 
    return (row["Comment_Score"] - min_value)/(max_value - min_value)

def extract_positive_rate(percentage_of_comment_weight_per_day_df):
    Positive_Weight = {}
    for index in percentage_of_comment_weight_per_day_df.index.values:
        date, sentiment = index
        if date in Positive_Weight:
            continue
        else:
            if sentiment == 1:
                Positive_Weight[date] = percentage_of_comment_weight_per_day_df.loc[(date, sentiment), :]["Comment Weight"]
            else:
                Positive_Weight[date] = 1 - percentage_of_comment_weight_per_day_df.loc[(date, sentiment), :]["Comment Weight"]

    return list(Positive_Weight.keys()), list(Positive_Weight.values())

def create_dataset(reddit_df, yahoo_df):
    df = reddit_df
    X = df[['clean_Comment_Body']]
    model_path = 'application/BiLSTM.h5'
    loaded_model = load_model(model_path)
    with open("application/tokenizer_config.json", 'r', encoding='utf-8') as f:
        loaded_tokenizer_json = json.load(f)

    tokenizer = tokenizer_from_json(loaded_tokenizer_json)
    X_seq = tokenizer.texts_to_sequences(X.values.reshape(-1))

    X_seq_padded = pad_sequences(X_seq, maxlen=64)
    y = loaded_model.predict(X_seq_padded)
    df["comment_sentiment"]=(y > 0.5).astype(int)
    print("£"*1000)
    print(df['Comment_Created_UTC'])
    df['Comment_Created_UTC'] = pd.to_datetime(df['Comment_Created_UTC'])
    print("$"*1000)
    print(df['Comment_Created_UTC'])
    df['Comment_Created_UTC'] = df['Comment_Created_UTC'].dt.date
    result_df = df.groupby(['Comment_Created_UTC', 'comment_sentiment']).agg({
        'Comment_Score': 'sum',
    }).reset_index()
    aggregations = {
     "Comment_Score": ['min', 'max'],
    }
    new_df = df[['Comment_Created_UTC', "Comment_Score",'comment_sentiment']].groupby(['Comment_Created_UTC']).agg(aggregations)
    new_df 
    global mapp
    mapp = new_df.to_dict()
    global i
    i=1
    df["Comment Weight"] = df.apply(computeCommentsWeights, axis=1)
    sum_of_comment_weights_per_day_per_sentiment_df = df[['Comment_Created_UTC', "Comment Weight",'comment_sentiment']].groupby(['Comment_Created_UTC', 'comment_sentiment']).sum()
    sum_of_comment_weights_per_day_df = df[['Comment_Created_UTC', "Comment Weight"]].groupby(['Comment_Created_UTC']).sum()
    percentage_of_comment_weight_per_day_df = sum_of_comment_weights_per_day_per_sentiment_df / sum_of_comment_weights_per_day_df
    dates , positive_rate = extract_positive_rate(percentage_of_comment_weight_per_day_df)
    num_of_comments_per_day = df[['Comment_Created_UTC', 'Comment_Body']].groupby(['Comment_Created_UTC']).count().values.reshape(-1)
    dataset = pd.DataFrame(columns=["Date", "Positive Comments Rate", "# Comments"])
    dataset["Date"] = dates
    dataset["Positive Comments Rate"] = positive_rate
    dataset["# Comments"] = num_of_comments_per_day
    dataset["Date"] = pd.to_datetime(dataset["Date"])
    apple_stock = yahoo_df
    apple_stock = apple_stock[["Date", "Close"]]
    apple_stock['Date'] = pd.to_datetime(apple_stock['Date'])
    result_df = pd.merge(apple_stock, dataset, on='Date', how='inner')
    result_df
    return result_df

def df_to_X_y(df, window_size=6):
    df_as_np = df.to_numpy()
    X, y = [], []
    for i in range(len(df_as_np)-window_size):
        row = [ r for r in df_as_np[i:i+window_size]]
        X.append(row)
        label =  df_as_np[i+window_size][0] # 0 : to select the last column = target in our case
        y.append(label)
    return np.array(X), np.array(y)

def LSTM_predict(data, model_path ='sentiment_bad_model.h5'):
    loaded_model = load_model('sentiment_bad_model.h5')
    data["Date"] = pd.to_datetime(data["Date"])
    stock_price = data.set_index('Date')
    window_size=6
    X3, _ = df_to_X_y(stock_price, window_size=window_size)
    print("#"*100)
    print(stock_price)
    print("#"*100)
    stock_price_test , X_test = stock_price, X3
    print(X_test)
    print("#"*100)
    # print(loaded_model.predict(X_test))
    # X_test_reshaped = X_test.reshape(X_test.shape[0], X_test.shape[1] * X_test.shape[2])
    predictions= loaded_model.predict(X_test.astype(float)).flatten()
    pred_df = pd.DataFrame(columns=["Date", "Close"])
    pred_df["Close"] = predictions
    #just one day
    # current_timestamp = pd.Timestamp(stock_price_test.index[0])
    # next_day_timestamp = current_timestamp + pd.Timedelta(days=1)
    pred_df["Date"] = list(stock_price_test.index)[:len(predictions)]
    return pred_df

def query_InfluxDB():
    token = "zvQULighqQrexRsG6GIaSvv6DxSXxr_9JnLZysy0VHThrra09e2mvriF-1521VK_5j-nmTN25p37119gocabNQ=="
    org = "ENSIAS1"
    url = "http://localhost:8086"

    # Define the InfluxDB query
    query = '''from(bucket: "Bucket1")
    |> range(start: -2y)
    |> filter(fn: (r) => r["_measurement"] == "financial-forecasting-using-social-media")
    '''

    # Create InfluxDB client
    client = InfluxDBClient(url=url, token=token, org=org)

    # Execute the InfluxDB query
    try:
        query_api = client.query_api()
        result = query_api.query(query=query, org=org)

        # Store results in a list of dictionaries
        results = []
        for table in result:
            for record in table.records:
                timestamp = record.get_time()
                field = record.get_field()
                value = record.get_value()

                # Create a dictionary for each record
                results.append({'Timestamp': timestamp, field: value})

        df = pd.DataFrame(results).set_index('Timestamp')
        df = df.sort_index(ascending=False)
        df_merged = df.groupby(df.index).first()
        df_merged = df_merged.sort_index(ascending=False)
        df_merged.index = df_merged.index.tz_convert(None)
        df_merged = df_merged.reset_index(drop=False)
        df_merged = df_merged.rename(columns={"Timestamp":"Date", "close": "Close", "positive comments rate":"Positive Comments Rate", "# comments":"# Comments"})
        df_merged = df_merged[["Date", "Close","Positive Comments Rate" ,"# Comments"]]
        client.close()
        return df_merged

    except Exception as e:
        print(f"Error: {e}")
        
    client.close()
    return None

def parse_row(row: OrderedDict):
    return Point("financial-forecasting-using-social-media") \
        .tag("type", "1year-AAPL-daily") \
        .field("# comments", int(row['# Comments'])) \
        .field("positive comments rate", float(row['Positive Comments Rate'])) \
        .field("close", float(row['Close'])) \
        .time(row['Date'])

def parse_row_predicted(row: OrderedDict):
    return Point("financial-forecasting-using-social-media-predicted") \
        .tag("type", "float") \
        .field("predicted close", float(row['Close'])) \
        .time(row['Date'])

def write_data(df, is_historical=True):
    token = "zvQULighqQrexRsG6GIaSvv6DxSXxr_9JnLZysy0VHThrra09e2mvriF-1521VK_5j-nmTN25p37119gocabNQ=="
    org = "ENSIAS1"
    url = "http://localhost:8086"


    """
    Converts csv into sequence of data point
    """
    if is_historical:
        data = rx.from_iterable(df.to_dict(orient='records')).pipe(ops.map(lambda row: parse_row(row)))
    else:
        data = rx.from_iterable(df.to_dict(orient='records')).pipe(ops.map(lambda row: parse_row_predicted(row)))

    with InfluxDBClient(url=url, token=token, org=org, debug=True) as client:

        """
        Create client that writes data in batches with 50_000 items.
        """
        with client.write_api(write_options=WriteOptions(batch_size=50_000, flush_interval=10_000)) as write_api:

            """
            Write data into InfluxDB
            """
            write_api.write(bucket="Bucket1", record=data)

def z_score_normalize_train(train_data, test_data):
    # Calculate mean and std_dev using training data
    mean = np.mean(train_data, axis=0)
    std_dev = np.std(train_data, axis=0)
    # Normalize training data
    normalized_train_data = (train_data - mean) / std_dev
    # Normalize testing data using mean and std_dev of training data
    normalized_test_data = (test_data - mean) / std_dev
    return normalized_train_data, normalized_test_data, mean, std_dev

def inverse_transform(normalized_data, mean, std_dev):
    # Reverse the normalization process
    original_data = normalized_data * std_dev + mean
    return original_data

# Create sequences with a window size of 6 for input features and 7 for output
def create_sequences(data, window_size, target_size):
    X, y = [], []
    for i in range(len(data) - window_size - target_size + 1):
        X.append(data.iloc[i:i+window_size].values)
        y.append(data.iloc[i+window_size:i+window_size+target_size, 0].values)  # Assuming 'Close' is the target variable
    return np.array(X), np.array(y)

def predict(data, window_size=90, target_size=7, epochs=5):

    global LSTMs
    
    # Load your data
    data = data.set_index("Date")
    data = data.sort_values(by="Date", ascending=True)

    X, y = create_sequences(data, window_size, target_size)

    # Split the data into training and testing sets without shuffling
    train_ratio = 0.8
    val_ratio = 0.1
    test_ratio = 0.1

    # Calculate split points
    train_split = int(train_ratio * len(X))
    val_split = int((train_ratio + val_ratio) * len(X))

    # Split the data
    X_train, X_val, X_test = X[:train_split], X[train_split:val_split], X[val_split:]
    y_train, y_val, y_test = y[:train_split], y[train_split:val_split], y[val_split:]
    X_train, X_val, X_test = X_train.astype(float), X_val.astype(float), X_test.astype(float)
    y_train, y_val, y_test = y_train.astype(float), y_val.astype(float), y_test.astype(float)

    X_train_n, X_val_n, mean_X, std_dev_X = z_score_normalize_train(X_train, X_val)
    y_train_n, y_val_n, mean_y, std_dev_y = z_score_normalize_train(y_train, y_val)
    X_train_n, X_test_n, mean_X, std_dev_X = z_score_normalize_train(X_train, X_test)
    y_train_n, y_test_n, mean_y, std_dev_y = z_score_normalize_train(y_train, y_test)
    print("X_train.shape: ", X_train.shape)
    if (window_size, target_size) not in LSTMs:
        # Build the LSTM model
        model = Sequential()
        model.add(LSTM(100, activation='relu', input_shape=(window_size, X_train.shape[2]), return_sequences=True))
        model.add(LSTM(50, activation='relu', return_sequences=True))
        model.add(LSTM(25, activation='relu'))
        model.add(Dense(target_size))
        model.compile(optimizer='adam', loss='mean_squared_error')
        # Train the model
        print("X_train: ", X_train)

        print("X_train_n: ", X_train_n)
        model.fit(X_train_n, y_train_n, epochs=epochs, batch_size=32, validation_data=(X_val_n, y_val_n))
        model.save(f'lstm_model_{window_size}_{target_size}.h5')
        LSTMs[(window_size, target_size)] = f'lstm_model_{window_size}_{target_size}.h5'
    else:
        model = load_model(LSTMs[(window_size, target_size)])
        model.fit(X_train_n, y_train_n, epochs=epochs, batch_size=32, validation_data=(X_val_n, y_val_n))
    print(data.tail(window_size).to_numpy())
    features =np.array([data.tail(window_size).to_numpy()]).astype(float)
    _, features_n, _, _ = z_score_normalize_train(X_train, features)
    print(features_n)
    predictions_n = model.predict(features_n)
    predictions = inverse_transform(predictions_n, mean_y, std_dev_y)
    print(predictions)
    predictions = predictions.reshape(-1)
    print(predictions)
    return predictions

def make_dataframe(target_size, predictions, lastdate, lastClose):
    start_date = lastdate + timedelta(days=1)
    date_index = pd.date_range(start=lastdate, periods=target_size+1, freq='D').normalize()
    print("date_index: ", date_index)
    print("lastClose: ", lastClose)
    print("predictions: ", predictions)
    print("list(predictions): ", list(predictions))
    close = [lastClose] + list(predictions)
    print("close: ", close)
    data = {
        'Close': close, 
        'Date': date_index
    }
    df = pd.DataFrame(data)
    print(df)
    return df

def delete_data(start_date="1980-12-31", end_date="2080-12-31"):

    client = InfluxDBClient(url="http://localhost:8086", token="zvQULighqQrexRsG6GIaSvv6DxSXxr_9JnLZysy0VHThrra09e2mvriF-1521VK_5j-nmTN25p37119gocabNQ==")

    delete_api = client.delete_api()

    """
    Delete Data
    """
    start = start_date + "T00:00:00Z"
    stop = end_date + "T23:59:59Z"
    # start = "1970-01-01T00:00:00Z"
    # stop = "2021-02-01T00:00:00Z"
    delete_api.delete(start, stop, '_measurement="financial-forecasting-using-social-media-predicted"', bucket='Bucket1', org='ENSIAS1')

    """
    Close client
    """
    client.close()

def kafka_realtime_reddit_scraping():
    producers = [
        KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda x: dumps(x).encode('utf-8')
        )
    ]

    # Kafka consumer setup
    consumers = [
        KafkaConsumer(
            bootstrap_servers='localhost:9092',
            auto_offset_reset='earliest',
            group_id='Reddit_Scrapping',
            value_deserializer=lambda x: loads(x.decode('utf-8'))
        )
    ]

    # Create and start threads for producers and consumers
    producer_threads = [Thread(target=scrap_reddit_rt, args=(producers[0], 1_000_000_000, 1, 60, 100))]
    consumer_threads = [Thread(target=real_time_Reddit_preprocessing, args=(consumers[0], "Reddit_Scrapping"))]

    for thread in producer_threads:
        thread.start()

    for thread in consumer_threads:
        thread.start()

    # Wait for producer and consumer threads to finish
    for thread in producer_threads:
        thread.join()

    for thread in consumer_threads:
        thread.join()



def main(window_size, target_size, epochs):
    global LSTMs
    old_dataset = query_InfluxDB()
    print(old_dataset)
    old_dataset.dropna(inplace=True)
    lastdate = old_dataset.Date.max()
    print('$'*100)
    print(lastdate)
    lastClose = old_dataset.loc[old_dataset["Date"]==lastdate, "Close"].values[0]
    number_of_days = compute_numdays(lastdate)
    #scrapping
    reddit_df=pd.DataFrame()
    num_posts=50
    while reddit_df.empty:
        num_posts+=50
        reddit_df = scrap_reddit(num_posts=num_posts, number_of_days=number_of_days)
    print("+"*1000)
    print(reddit_df)
    yahoo_df = scrap_yahoo_finance_data("AAPL", lastdate)
    #Processing & Sentiment Analysis 
    preprocessed_reddit_df = preprocessing_reddit(reddit_df)
    new_data = create_dataset(preprocessed_reddit_df, yahoo_df)
    print(new_data)
    #write this dataset to InfluxDB
    write_data(new_data)
    new_dataset = pd.concat([new_data, old_dataset], ignore_index=True)
    new_dataset = new_dataset.drop_duplicates()
    new_dataset = new_dataset.sort_values(by='Date', ascending=False)
    new_dataset.to_csv("latest_dataset.csv", index=False)
    new_dataset.dropna(inplace=True)
    predictions = predict(new_dataset, window_size, target_size, epochs)
    predictions_df = make_dataframe(target_size, predictions, lastdate, lastClose)
    start_date, end_date = str(predictions_df.Date.min().date()), str(predictions_df.Date.max().date())
    print(start_date,"|000000000000000|", end_date)
    delete_data()
    write_data(predictions_df, is_historical=False)
    kafka_realtime_reddit_scraping()

    