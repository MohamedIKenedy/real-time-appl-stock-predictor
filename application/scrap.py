import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from dateutil.parser import parse
from selenium.common.exceptions import NoSuchElementException
from time import perf_counter
from tqdm import tqdm

def scrap_data_dynamically(ticker, numDays=1862, order="DESC"):
    url = "https://finance.yahoo.com/quote/"+ ticker +"/history?period1=1420070400&period2=1653350400&interval=1d&filter=history&frequency=1d&includeAdjustedClose=true"
    driver = webdriver.Chrome(ChromeDriverManager().install()) 
    driver.get(url)
    driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
    start = 0
    finish = 4200
    columns = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
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
            table.append(
                [
                    driver.find_element_by_xpath(f'//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[2]/table/tbody/tr[{i}]/td[1]/span').text,
                    driver.find_element_by_xpath(f'//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[2]/table/tbody/tr[{i}]/td[2]/span').text,
                    driver.find_element_by_xpath(f'//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[2]/table/tbody/tr[{i}]/td[3]/span').text,
                    driver.find_element_by_xpath(f'//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[2]/table/tbody/tr[{i}]/td[4]/span').text,
                    driver.find_element_by_xpath(f'//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[2]/table/tbody/tr[{i}]/td[5]/span').text,
                    driver.find_element_by_xpath(f'//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[2]/table/tbody/tr[{i}]/td[6]/span').text,
                    driver.find_element_by_xpath(f'//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[2]/table/tbody/tr[{i}]/td[7]/span').text
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
    pbar.update(14)
    for open_str in scrapped_data["Open"]:
        if(type(open_str)!= float):
            open_float = float(open_str.replace(',',''))
            open_index = scrapped_data["Open"] == open_str
            scrapped_data["Open"].loc[open_index] = open_float
    pbar.update(14)
    for high_str in scrapped_data["High"]:
        if(type(high_str)!= float):
            high_float = float(high_str.replace(',',''))
            high_index = scrapped_data["High"] == high_str
            scrapped_data["High"].loc[high_index] = high_float
    pbar.update(14)
    for low_str in scrapped_data["Low"]:
        if(type(low_str)!= float):
            low_float = float(low_str.replace(',',''))
            low_index = scrapped_data["Low"] == low_str
            scrapped_data["Low"].loc[low_index] = low_float
    pbar.update(14)
    for close_str in scrapped_data["Close"]:
        if(type(close_str)!= float):
            close_float = float(close_str.replace(',',''))
            close_index = scrapped_data["Close"] == close_str
            scrapped_data["Close"].loc[close_index] = close_float
    pbar.update(14)   
    for adj_close_str in scrapped_data["Adj Close"]:
        if(type(adj_close_str)!= float):
            adj_close_float = float(adj_close_str.replace(',',''))
            adj_close_index = scrapped_data["Adj Close"] == adj_close_str
            scrapped_data["Adj Close"].loc[adj_close_index] = adj_close_float
    pbar.update(14)   
    for volume_str in scrapped_data["Volume"]:
        if(type(volume_str)!= float):
            volume_float = float(volume_str.replace(',',''))
            volume_index = scrapped_data["Volume"] == volume_str
            scrapped_data["Volume"].loc[volume_index] = volume_float
    pbar.update(14)
    pbar.close()
    return scrapped_data


def load_data(ticker,numDays,order):
    time_start = perf_counter()
    scrapped_data = scrap_data_dynamically(ticker=ticker , numDays=numDays,order=order)
    time_finish = perf_counter()
    print("\n\n\n\nDuration:",time_finish-time_start,"\n\n\n\n")
    cleaned_data = clean_data(scrapped_data)
    return cleaned_data