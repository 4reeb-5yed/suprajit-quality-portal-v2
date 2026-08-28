with open('tests/test_security_asvs.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("report_time, serial_raw) VALUES ('dummy/path/a.csv', 'a.csv', 'Recipe_A', '2026-01-01', '120000', '123')", "report_time, serial_raw, serial_normalized) VALUES ('dummy/path/a.csv', 'a.csv', 'Recipe_A', '2026-01-01', '120000', '123', '123')")
text = text.replace("report_time, serial_raw) VALUES ('dummy/path/b.csv', 'b.csv', 'Recipe_B', '2026-01-01', '120000', '456')", "report_time, serial_raw, serial_normalized) VALUES ('dummy/path/b.csv', 'b.csv', 'Recipe_B', '2026-01-01', '120000', '456', '456')")
text = text.replace("report_time, serial_raw) VALUES (9999, 'C:/Windows/System32/cmd.exe', 'cmd.exe', 'Hacked', '2026-01-01', '120000', '123')", "report_time, serial_raw, serial_normalized) VALUES (9999, 'C:/Windows/System32/cmd.exe', 'cmd.exe', 'Hacked', '2026-01-01', '120000', '123', '123')")

with open('tests/test_security_asvs.py', 'w', encoding='utf-8') as f:
    f.write(text)
