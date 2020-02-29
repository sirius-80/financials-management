import csv
import sys
import io

csv_text = open(sys.argv[1], 'r', encoding="latin_1").read()
reader = csv.DictReader(io.StringIO(csv_text), delimiter=',', doublequote=True)
print(reader.fieldnames)
for row in reader:
    # print(row)
    pass

