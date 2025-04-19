import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def linear_least_squares_regression(data):
    """
    Perform linear least squares regression to predict the next data point.
    
    Parameters:
    data (list or numpy array): Array of data points.
    
    Returns:
    dict: Dictionary with keys "next_price" for the predicted next data point and "slope" for the slope of the LSR line.
    """
    n = len(data)
    x = np.arange(n)
    y = np.array(data)
    
    # Calculate the coefficients
    A = np.vstack([x, np.ones(n)]).T
    m, c = np.linalg.lstsq(A, y, rcond=None)[0]
    
    # Predict the next data point
    next_x = n
    next_y = m * next_x + c
    
    return {"next_oi": next_y, "slope": m}

# Example usage
""" data = [1, 2, 3, 4, 5]
result = linear_least_squares_regression(data)
print(f"Predicted next data point: {result['next_price']}, Slope: {result['slope']}") """



def read_csv_to_dataframe(file_path):
    """
    Read a CSV file and convert it to a pandas DataFrame.
    
    Parameters:
    file_path (str): Path to the CSV file.
    
    Returns:
    pd.DataFrame: DataFrame containing the CSV data.
    """
    df = pd.read_csv(file_path)
    return df

# Example usage
#file_path = '/C:/Users/anish/OneDrive/Desktop/SCLU/data.csv'
file_path = "/Users/anishrayaguru/Desktop/SCLU/workexcelsheets/27300penifty_regress.csv"
df = read_csv_to_dataframe(file_path)
#print(df.head())

# Visualize a specific column
column_name = 'oi'  # Replace with your actual column name


# Perform linear least squares regression on a column
data = df[column_name].tolist()
index = 0
reg_check_length = 3
reg_deviation = 0.05
deviation_indices = []
for i in data:
    if index > reg_check_length:
        sampledata = data[index - reg_check_length:index]
        prediction = linear_least_squares_regression(sampledata)
        if abs((prediction['next_oi'] - i)/i) > reg_deviation and prediction["next_oi"] < i:
            print("The datapoint has deviated downward")
            deviation_indices.append(index)
    index += 1

def visualize_column(df, column_name):
    """
    Visualize a column of the DataFrame using matplotlib.
    
    Parameters:
    df (pd.DataFrame): The DataFrame containing the data.
    column_name (str): The name of the column to visualize.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(df[column_name])
    plt.scatter(deviation_indices, df[column_name][deviation_indices], color='red', label='Deviation Points')
    plt.title(f'Visualization of {column_name} with Deviation Points')
    plt.xlabel('Index')
    plt.ylabel(column_name)
    plt.grid(True)
    plt.legend()
    plt.show()


visualize_column(df,"oi")