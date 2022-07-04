import json
a_file = open("Tareset.json", "r")
json_object = json.load(a_file)
a_file.close()
outputOld = json_object["Data Tare"]["002"]
print('Output old : ', outputOld)

a = 'asdasd123'
newa = ''.join([i for i in a if not i.isdigit()])
print('',newa)