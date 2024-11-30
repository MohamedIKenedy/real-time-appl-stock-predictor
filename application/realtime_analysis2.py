# producer_consumer.py
from time import sleep
from json import dumps, loads
from kafka import KafkaProducer, KafkaConsumer
import random
from threading import Thread
import requests
from bs4 import BeautifulSoup
import pandas as pd
from kafka import KafkaProducer, KafkaConsumer
import pandas as pd
import time
import praw
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from time import sleep, perf_counter
from tqdm import tqdm
from dateutil.parser import parse
import matplotlib.pyplot as plt
import seaborn as sns
import re
import emoji
import warnings
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

mapp={}
i=0
def preprocess_text_with_stemming_and_lemmatization(text):
    # global i
    # if i % 100 == 0:
    #     print(i)
    # i += 1
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
    # global i
    global mapp
    # print(i)
    # i+=1
    min_value = mapp[('Comment_Score', 'min')][row['Comment_Created_UTC']] 
    max_value = mapp[('Comment_Score', 'max')][row['Comment_Created_UTC']]
    if min_value == max_value:
        return 1
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

def sentiment_analysis(reddit_df):
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
    df['Comment_Created_UTC'] = pd.to_datetime(df['Comment_Created_UTC'])
    df['Comment_Created_UTC'] = df['Comment_Created_UTC'].dt.date
    print("~"*1000)
    print(df['Comment_Created_UTC'])
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
    # global i
    # i=1
    df["Comment Weight"] = df.apply(computeCommentsWeights, axis=1)
    sum_of_comment_weights_per_day_per_sentiment_df = df[['Comment_Created_UTC', "Comment Weight",'comment_sentiment']].groupby(['Comment_Created_UTC', 'comment_sentiment']).sum()
    sum_of_comment_weights_per_day_df = df[['Comment_Created_UTC', "Comment Weight"]].groupby(['Comment_Created_UTC']).sum()
    percentage_of_comment_weight_per_day_df = sum_of_comment_weights_per_day_per_sentiment_df / sum_of_comment_weights_per_day_df
    dates , positive_rate = extract_positive_rate(percentage_of_comment_weight_per_day_df)
    # print("%"*1000)
    # print("dates: ", dates)
    num_of_comments_per_day = df[['Comment_Created_UTC', 'Comment_Body']].groupby(['Comment_Created_UTC']).count().values.reshape(-1)
    dataset = pd.DataFrame(columns=["Date", "Positive Comments Rate", "# Comments"])
    dataset["Date"] = dates
    dataset["Positive Comments Rate"] = positive_rate
    dataset["# Comments"] = num_of_comments_per_day
    dataset["Date"] = pd.to_datetime(dataset["Date"])
    return dataset
    # apple_stock = yahoo_df
    # apple_stock = apple_stock[["Date", "Close"]]
    # apple_stock['Date'] = pd.to_datetime(apple_stock['Date'])
    # result_df = pd.merge(apple_stock, dataset, on='Date', how='inner')
    # result_df
    # return result_df

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

def scrap_reddit_rt(producer, num_posts=1_000_000_000, number_of_days=1, refresh_rate=60, batch_size=100):

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
    len_prev_post_data = len(post_data)
    while True:
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
                post_date = datetime.utcfromtimestamp(post.created_utc)
                if start_date <= post_date <= end_date:
                    c=1
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
                p+=1
                if len(post_data) == len_prev_post_data:
                    time.sleep(0.1)
                    continue
                
                if p%batch_size==0:
                    # Create a DataFrame from the list
                    df = pd.DataFrame(post_data)
                    df["Comment_Created_UTC"] = df["Comment_Created_UTC"].astype(str)
                    # df = df.sort_values("Comment_Created_UTC")
                    print("="*1000)
                    print(df)
                    # Save the DataFrame to a CSV file
                    # csv_file_path = f"reddit_comments_{subreddit_name}_{csv_label}_{num_posts}_year1.csv"
                    # df.to_csv(csv_file_path, index=False, encoding="utf-8")
                    producer.send(f'Reddit_Scrapping', value=df.to_json(orient='records'))
                    print(f"The Reddit Producer produced 100 posts")
                    sleep(refresh_rate)
                    len_prev_post_data = len(post_data)
                # Introduce a delay to avoid rate limiting
                time.sleep(0.1)  # You can adjust the delay as needed

def real_time_Reddit_preprocessing(consumer, topic):
    consumer.subscribe(topic)
    print("consumer subscribed")
    for message in consumer:
        json_data = message.value  # Assuming the message is a JSON-formatted string
        df = pd.read_json(json_data, orient='records')
        print("$"*100)
        print("df")
        print(df)
        # print("Close")
        # print(df["Close"])
        # print("# Comments")
        # print(df["Comments"])
        # print("Positive Comments Rate")
        # print(df["Positive Comments Rate"])
        # Perform real-time analysis (e.g., counting page views per minute)
        preprocessed_df = preprocessing_reddit(df)
        processed_df = sentiment_analysis(preprocessed_df.copy())
        print("SOS"*100)
        print(processed_df["Date"])
        print(processed_df["Positive Comments Rate"])
        print(processed_df["# Comments"])
        #check if yahoo data was produced in database.
        latest_data = query_InfluxDB()
        date = processed_df.Date.max()
        print("DATE "*100)
        print(date)
        num_comments = processed_df.loc[processed_df.Date == date, "# Comments"].values[0]
        pos_com_rate = processed_df.loc[processed_df.Date == date, "Positive Comments Rate"].values[0]
        #TODO .values ?
        if date in latest_data.Date.values:
            #TODO date type
            latest_data.loc[latest_data.Date == date, "Positive Comments Rate"] = pos_com_rate 
            latest_data.loc[latest_data.Date == date,"# Comments"] = num_comments
        else:
            new_row = {'Date': date, 'Close': float('nan'), '# Comments': num_comments, "Positive Comments Rate":pos_com_rate  }
            # Add new row using append
            latest_data = latest_data.append(new_row, ignore_index=True)
            #TODO not sure drop parameter
            latest_data.reset_index(drop=True)
        latest_data = latest_data.sort_values("Date", ascending=False)
        latest_data = latest_data.reset_index(drop=True)
        write_data(latest_data)
        print("#"*100)
        print("latest_data")
        print(latest_data)
        print("Close")
        print(latest_data["Close"])
        print("# Comments")
        print(latest_data["# Comments"])
        print("Positive Comments Rate")
        print(latest_data["Positive Comments Rate"])
        print("/\/"*1000)
        print(f"Consumer subscribed to topic {topic} in real-time updated Table 1 : Date: {date}, # Comments: {num_comments}, # Positive Comment Rate {pos_com_rate}  ")


# if __name__ == "__main__":

#     # Kafka producer setup
#     producers = [
#         KafkaProducer(
#         bootstrap_servers='localhost:9092',
#         value_serializer=lambda x: dumps(x).encode('utf-8')
#         )
#     ]

#     # Kafka consumer setup
#     consumers = [
#         KafkaConsumer(
#             bootstrap_servers='localhost:9092',
#             auto_offset_reset='earliest',
#             group_id='Reddit_Scrapping',
#             value_deserializer=lambda x: loads(x.decode('utf-8'))
#         )
#     ]

#     # Create and start threads for producers and consumers
#     producer_threads = [Thread(target=scrap_reddit_rt, args=(producers[0], 1_000_000_000, 1, 60, 100))]
#     consumer_threads = [Thread(target=real_time_Reddit_preprocessing, args=(consumers[0], "Reddit_Scrapping"))]

#     for thread in producer_threads:
#         thread.start()

#     for thread in consumer_threads:
#         thread.start()

#     # Wait for producer and consumer threads to finish
#     for thread in producer_threads:
#         thread.join()

#     for thread in consumer_threads:
#         thread.join()





# # def generate_user_activity(producer, producer_id):
# #     while True:

# #         event = {"user": user, "page": page}
# #         producer.send(f'user_activity_topic_{producer_id}', value=event)
# #         print(f"Producer-{producer_id} produced event: {event}")

# #         sleep(1)


# # def real_time_analyzer(consumer, topics):
# #     page_view_counts = {}

# #     consumer.subscribe(topics)

# #     for message in consumer:
# #         event = message.value
# #         user = event["user"]
# #         page = event["page"]

# #         # Perform real-time analysis (e.g., counting page views per minute)
# #         if page in page_view_counts:
# #             page_view_counts[page] += 1
# #         else:
# #             page_view_counts[page] = 1

# #         print(f"Consumer subscribed to topics {topics} real-time analysis: {page} views - {page_view_counts[page]}")

# # if __name__ == "__main__":
# #     # Number of producers and consumers
# #     num_producers = 2
# #     num_consumers = 2

# #     # Kafka producer setup
# #     producers = [KafkaProducer(
# #         bootstrap_servers='localhost:9092',
# #         value_serializer=lambda x: dumps(x).encode('utf-8')
# #     ) for _ in range(num_producers)]

# #     # Kafka consumer setup
# #     consumers = [KafkaConsumer(
# #         bootstrap_servers='localhost:9092',
# #         auto_offset_reset='earliest',
# #         group_id=f'user_activity_group_{i}',
# #         value_deserializer=lambda x: loads(x.decode('utf-8'))
# #     ) for i in range(num_consumers)]

# #     # Create and start threads for producers and consumers
# #     producer_threads = [Thread(target=generate_user_activity, args=(producers[i], i)) for i in range(num_producers)]
# #     consumer_threads = [Thread(target=real_time_analyzer, args=(consumers[i], [f'user_activity_topic_{j}' for j in range(num_producers)])) for i in range(num_consumers)]

# #     for thread in producer_threads:
# #         thread.start()

# #     for thread in consumer_threads:
# #         thread.start()

# #     # Wait for producer and consumer threads to finish
# #     for thread in producer_threads:
# #         thread.join()

# #     for thread in consumer_threads:
# #         thread.join()
