# Import_Wrapper_Tally_ERP
A simple python wrapper utilizing the power of Pandas to import sales vouchers from CSV files into Tally ERP 9.

I made this wrapper while helping a former classmate build a small product around his ecommerce sales, to push all his sales invoices into Tally. works perfectly on the python CLI. Currently developing the front end for the same (folks interested in ReactJS are welcome to contribute!).


```python

>>> import csv_to_tally_v05 #verify version with the filename
>>> from csv_to_tally_v05 import TallyImporter  #Import the class
>>> from importlib import reload # to be used only after making changes to the file
>>> reload(csv_to_tally) # to be used only after making changes to the file
>>> f = 'test.csv'
>>> t = TallyImporter(filename=f) #instantiate object of the class TallyImporter
loaded file into a dataframe "df".
>>> t.test_tally() #if Tally is running, the response will indicate the same.
>>> type(t.df)
<class 'pandas.core.frame.DataFrame'>
>>> t.clean_columns() #clean all columns of the dataframe 
Index([ 'invoice_number', 'invoice_date','sku', 'invoice_amount','total_tax_amount', 'cgst_rate', 'sgst_rate','igst_rate'],
      dtype='object')
>>> row = t.df.iloc[0]
>>> t.send_tally_request(row) #send one row to Tally and get the response back
>>> o = t.batch_import() #send multiple rows to Tally and get the response back.
>>> type(o)
<class 'pandas.core.series.Series'>
>>> o
>>>o.to_csv('tally_log.txt', sep='\t', index=False) # Store the response in a log file for furter viewing.
```


