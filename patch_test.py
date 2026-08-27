with open('run_tests.py', 'r') as f:
    c = f.read()
    
c = c.replace('EV_TPS_2026_08_21_14_30_00_0045.xlsx', 'EV_TPS_21-08-2026_14.30.00_0045.xlsx')

with open('run_tests.py', 'w') as f:
    f.write(c)
