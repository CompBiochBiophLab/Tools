# Python program to read
# json file
 
 
import json
 
# Opening JSON file
f = open('../../Downloads/Export.json')
 
# returns JSON object as
# a dictionary
data = json.load(f)
print(data)
 
# Iterating through the json
# list
for i in data['header']:
    print(i)
 
# Closing file
f.close()