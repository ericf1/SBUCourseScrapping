import xlsxwriter
import pandas as pd
workbook = xlsxwriter.Workbook('SBU.xlsx')
worksheet = workbook.add_worksheet('Hyperlinks')

df = pd.read_excel('BetterSBU.xlsx')
# df = pd.read_csv('SBU.csv')

for index, row in df.iterrows():
    i = index + 1
    worksheet.write_url(
        f'A{i}', f"https://www.stonybrook.edu/sb/bulletin/current/courses/{row['Dep']}/#{int(row['ID'])}", string=row['Course #'])

workbook.close()
