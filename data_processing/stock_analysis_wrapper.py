
import subprocess
import yfinance as yf
import pandas as pd
from datetime import datetime

def fetch_stock_data(ticker):
    data = yf.download(ticker, start="2022-01-01", end="2022-12-31")
    return data['Close'].tolist()

def call_cpp_executable(data):
    # Convert data list to a space-separated string
    input_data = ' '.join(map(str, data))
    # Call the C++ executable and pass the data
    result = subprocess.run(["/mnt/data/finance_calculations_fixed", input_data], capture_output=True, text=True)
    return result.stdout

def main():
    stocks = ["AAPL", "MSFT", "GOOGL"]
    for stock in stocks:
        print(f"Processing {stock}")
        data = fetch_stock_data(stock)
        output = call_cpp_executable(data)
        
        # Save the output to a unique file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"results_{stock}_{timestamp}.txt", 'w') as file:
            file.write(output)
        
        print(f"Results saved for {stock}.")

if __name__ == "__main__":
    main()
