
txtpath = '32Final_Result_sonselectdwi.txt'
with open(txtpath, 'r') as f:
    lines = f.readlines()
    info = lines[-1]
    info = info[:-1]

print(info)