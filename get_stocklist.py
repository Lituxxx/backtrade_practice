import tushare as ts
pro = ts.pro_api('f95df333fd3fe823d921ae41e676147c44b397743b3f74de81e3e7f8')
df = pro.index_member_all(l2_code='801078.SI')#自动化设备
data=df.iloc[:,6:8]
data.to_excel('自动化设备.xlsx',index=False)