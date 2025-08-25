import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def linear_fit_segment(x, y):
    """
    Fit a linear model to (x, y) and return predicted y values and slope.
    """
    A = np.vstack([x, np.ones(len(x))]).T
    m, c = np.linalg.lstsq(A, y, rcond=None)[0]
    y_pred = m * x + c
    return y_pred, m

def detect_breakpoints(data, max_deviation=0.05, min_segment_len=5):
    """
    Detect breakpoints in 'data' using a piecewise linear approach.

    Parameters:
    - data: 1D numpy array or list
    - max_deviation: float threshold for allowable deviation
    - min_segment_len: minimum length of a segment before allowing a breakpoint

    Returns:
    - segments: list of (start_index, end_index) for each segment
    """
    data = np.array(data)
    n = len(data)
    segments = []
    
    seg_start = 0
    i = 1
    while i < n:
        # We'll keep trying to extend the current segment from seg_start to i
        x_range = np.arange(seg_start, i+1)
        y_range = data[seg_start:i+1]
        
        # Fit a linear model to [seg_start .. i]
        y_pred, slope = linear_fit_segment(x_range, y_range)
        
        # Calculate deviation as MAPE (mean absolute percentage error), or max absolute % error
        abs_pct_errors = np.abs(y_range - y_pred) / y_range
        max_error = abs_pct_errors.max()
        
        # If the segment is too short, keep going
        if i - seg_start + 1 < min_segment_len:
            i += 1
            continue
        
        # If error is too big, we found a breakpoint
        if max_error > max_deviation:
            # The segment ended just before i
            segments.append((seg_start, i-1))
            seg_start = i  # new segment starts at i
        i += 1
    
    # Last segment goes till the end
    if seg_start < n:
        segments.append((seg_start, n-1))
    
    return segments

def plot_piecewise_segments(data, segments):
    """
    Plot the data and overlay piecewise linear fits for each segment.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(data, label='Original Data', alpha=0.5)
    
    for (start, end) in segments:
        x_range = np.arange(start, end+1)
        y_range = data[start:end+1]
        y_pred, _ = linear_fit_segment(x_range, y_range)
        plt.plot(x_range, y_pred, linewidth=2, label=f'Segment {start}-{end}')
    
    plt.title('Piecewise Linear Segmentation')
    plt.xlabel('Time Index')
    plt.ylabel('OI')
    plt.legend()
    plt.grid(True)
    plt.show()


df = pd.read_csv('/Users/anishrayaguru/Desktop/SCLU/workexcelsheets/27300penifty_regress.csv')
oi_data = df["oi"].values

# Detect breakpoints with up to 5% max deviation, and require segments of at least 5 points
segments = detect_breakpoints(oi_data, max_deviation=0.03, min_segment_len=1)
print("Detected segments:", segments)

# Plot them
plot_piecewise_segments(oi_data, segments)
