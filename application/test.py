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



def parse_row(row: OrderedDict):
    return Point("financial-forecasting-using-social-media") \
        .tag("type", "1year-AAPL-daily") \
        .field("# comments", int(row['# Comments'])) \
        .field("positive comments rate", float(row['Positive Comments Rate'])) \
        .field("close", float(row['Close'])) \
        .time(row['Date'])



def write_data():
    token = "zvQULighqQrexRsG6GIaSvv6DxSXxr_9JnLZysy0VHThrra09e2mvriF-1521VK_5j-nmTN25p37119gocabNQ=="
    org = "ENSIAS1"
    url = "http://localhost:8086"

    """
    Converts csv into sequence of data point
    """
    df = pd.read_csv("/home/yassine/Documents/S5/Projet Alami/Projet/Backup/TimeSeriesDataset1year (copy).csv")
    data = rx.from_iterable(df.to_dict(orient='records')).pipe(ops.map(lambda row: parse_row(row)))

    with InfluxDBClient(url=url, token=token, org=org, debug=True) as client:

        """
        Create client that writes data in batches with 50_000 items.
        """
        with client.write_api(write_options=WriteOptions(batch_size=50_000, flush_interval=10_000)) as write_api:

            """
            Write data into InfluxDB
            """
            write_api.write(bucket="Bucket1", record=data)

write_data()