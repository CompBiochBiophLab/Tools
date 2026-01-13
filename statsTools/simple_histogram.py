# import packages
import seaborn as sns
import matplotlib.pyplot as plt
import os
import pandas as pd
 
# configure path and column
folder_path = os.path.expanduser(os.path.expandvars("$HOME/Downloads"))   # <- change to your folder (can use ~ or $HOME)
filename = "notes.csv"             # <- change to your CSV file name
# select the third column by position (use the header/title)
filepath = os.path.join(folder_path, filename)
cols = pd.read_csv(filepath, nrows=0,sep=";").columns.tolist()
print(f"Columns in {filename}: {cols}")
if len(cols) < 3:
    raise ValueError(f"CSV file {filename} must have at least 3 columns")
column_name = cols[3]
print(f"Using column: {column_name}")

raw = pd.read_csv(filepath, sep=";")[column_name]
# coerce to numeric: normalize decimals (commas -> dots), strip spaces, convert, and coerce errors to NaN
numeric = pd.to_numeric(raw.astype(str).str.replace(',', '.', regex=False).str.strip(), errors='coerce')
n_total = len(raw)
n_non_numeric = numeric.isna().sum()
if n_non_numeric:
    print(f"Warning: {n_non_numeric}/{n_total} values in '{column_name}' could not be converted and will be dropped")
numeric = numeric.dropna()
if numeric.empty:
    raise ValueError(f"No numeric data found in column '{column_name}' after coercion")

summary = numeric.describe()
print(f"Summary statistics for column '{column_name}':\n{summary}")

# plotting a histogram
ax = sns.histplot(numeric,
                  bins=20,
                  kde=False,
                  color='red')
ax.set(xlabel=column_name, ylabel='Frequency')
 
# saving the figure
output_filepath = os.path.join(folder_path, "histogram.png")
plt.savefig(output_filepath, bbox_inches='tight')
print(f"Histogram saved to {output_filepath}")
plt.show()
plt.close()