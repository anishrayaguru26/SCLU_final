import csv
with open('25100  12_09_24.csv', 'r') as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        print(row)
        if i >= 4:  # Print only the first 5 rows
            break