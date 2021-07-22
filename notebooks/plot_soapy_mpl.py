import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import argparse
import os

# Importing the PIL library
from PIL import Image
from PIL import ImageDraw

# Create the parser
parser = argparse.ArgumentParser(description='Plot a single row from a spectrum CSV file created by spectro_radiometer ')
# Add the arguments
parser.add_argument('-r', action="store", dest="row", type=int, default=0,help='Select row to print, 0 to FFTSIZE')
parser.add_argument('-f', action="store", dest="filename", type=str, default='/home/dcohen/Dropbox/Public/ra/laboratory/devel/soapy/data/airspy/spec_sample.csv',\
                    help='Complete path and filename in quotes')

# Parse the arguments
parse_results = parser.parse_args()
row = parse_results.row
file_name = parse_results.filename
print(f'File\t{file_name}')
print(f'Row selected\t{row}')

# Get the path and filename without extension, we'll need that to store the image later
image_name = os.path.splitext(file_name)[0] + '.png'
print(f'Image name\t{image_name}')

# Read in a dataframe
df = pd.read_csv(file_name,header=None)

# Determine the FFT size
num_rows,num_cols = df.shape

# Get some useful information
# Observation date and time
obs_date = df.iloc[row,0]
obs_time = df.iloc[row,1]

# Frequency information to determine frequency series  
freq_min = df.iloc[row,2]
freq_max = df.iloc[row,3]
fft_size = num_cols - 6     # the 1st 6 columns are not measured data

# Get the actual data - starting from row 6 to end
spectral_series = df.iloc[row,6:]

# Create the frequency series which will be the x-axis (domain) of the plot
freq_series = np.linspace(freq_min, freq_max, num = fft_size, endpoint=True)

# Print some useful statistics
print(f'Shape\t{df.shape}')
print(spectral_series.describe())

# Replace the integer index with the frequency series
spectral_series.index = freq_series

# Plot the row
spectral_series.plot(x='Sample Number', y = 'Power, dB')
plt.savefig(image_name)
#plt.show()

# Open the image created by plt
img = Image.open(image_name)
  
# Call draw Method to add 2D graphics in an image
I1 = ImageDraw.Draw(img)
  
# Add Text to an image
I1.text((20, 10), f'Filename       {file_name}', fill=(255, 0, 0))
I1.text((20, 20), f'Obs date       {obs_date}', fill=(0, 0, 255))
I1.text((20, 30), f'Time (UTC)     {obs_time}', fill=(0, 0, 255))
I1.text((20, 40), f'Rownum         {row}', fill=(0, 0, 255))
I1.text((20, 50), f'Shape          {df.shape}', fill=(0, 0, 255))
I1.text((20, 60), f'Mean           {spectral_series.mean()}', fill=(0, 0, 255))
I1.text((20, 70), f'Stdev          {spectral_series.std()}', fill=(0, 0, 255))
I1.text((20, 80), f'Min            {spectral_series.min()}', fill=(0, 0, 255))
I1.text((20, 90), f'Max            {spectral_series.max()}', fill=(0, 0, 255))
  
# Display edited image
img.show()
# Save the edited image
img.save(image_name)


  

