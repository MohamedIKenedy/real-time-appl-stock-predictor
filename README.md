
# Real-Time AAPL Stock Predictor Using Sentiment Analysis

This project leverages **sentiment analysis** on Reddit comments to predict **Apple's (AAPL)** stock price in real-time. By analyzing the sentiment of comments on social media and correlating it with historical stock data, this application provides meaningful insights into stock trends.

---

## Features

- **Sentiment Analysis**: Analyzes Reddit comments to classify community feedback as positive or negative.
- **Stock Prediction Models**: Utilizes pre-trained LSTM models to predict AAPL stock prices.
- **Data Visualization**: Dashboards display historical and predicted stock trends, sentiment distribution, and correlations.
- **Data Explorer**: Interactive tool to query and visualize stock and sentiment data.

---

## Project Structure

```
.
├── application/                   # Backend application logic
├── instance/                      # Application instance configurations
├── lstm_model_*.h5                # Pre-trained LSTM models
├── latest_dataset.csv             # Latest processed dataset for predictions
├── reddit_comments_all_*.csv      # Historical Reddit comments data
├── conda-requirements.txt         # Dependencies for the Conda environment
├── run.py                         # Main script to run the application
├── README.md                      # Project documentation
└── dashboards/                    # Contains visualizations (see below)
```

---

## Screenshots

### 1. **Main Dashboard**
The main dashboard showcases stock trends, sentiment distributions, and detailed metrics.

![Dashboard Overview](./path/to/dashboard-overview.png)

---

### 2. **Data Explorer**
The Data Explorer enables dynamic queries of stock and sentiment data, providing flexibility for analysis.

![Data Explorer](./path/to/data-explorer.png)

---

## Installation and Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/real-time-appl-stock-predictor.git
   cd real-time-appl-stock-predictor
   ```

2. **Set up the environment**:
   - Install Conda (if not already installed).
   - Create and activate a Conda environment:
     ```bash
     conda create -n stock-predictor python=3.9 -y
     conda activate stock-predictor
     ```
   - Install dependencies:
     ```bash
     pip install -r conda-requirements.txt
     ```

3. **Run the application**:
   ```bash
   python run.py
   ```

4. **Access the application**:
   Open your browser and go to `http://localhost:5000`.

---

## How It Works

1. **Sentiment Analysis**:
   - Collects Reddit comments related to Apple.
   - Classifies the sentiment using Natural Language Processing techniques.

2. **Stock Price Prediction**:
   - Historical stock data is fed into LSTM models.
   - Predictive models correlate sentiment data with stock prices.

3. **Visualization**:
   - Dashboards are powered by tools like **Grafana**, providing real-time updates.

---

## Key Metrics

- **Comments Collected**: 100,292
- **Maximum Comments in a Day**: 1,733
- **Average Comments in a Day**: 387

---

## Future Enhancements

- Extend support for other stock symbols.
- Use more advanced sentiment analysis models.
- Improve LSTM model accuracy using additional datasets.

---

## Contributions

Feel free to contribute to this project by submitting a pull request or opening an issue.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
