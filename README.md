# Import_Wrapper_Tally_ERP
A simple python wrapper utilizing the power of Pandas to import sales vouchers from CSV files into Tally ERP 9.

I made this wrapper while helping a former classmate build a small product around his ecommerce sales, to push all his sales invoices into Tally. works perfectly on the python CLI. Currently developing the front end for the same (folks interested in ReactJS are welcome to contribute!).


```python

>>> from csv_to_tally import TallyImporter
>>> from importlib import reload
>>> reloac(csv_to_tally)
>>> f = 'test.csv'
>>> t = TallyImporter(filename=f)
loaded file into a dataframe "df".
>>> type(t.df)
<class 'pandas.core.frame.DataFrame'>
>>> t.clean_columns()
Index([ 'invoice_number', 'invoice_date','sku', 'invoice_amount','total_tax_amount', 'cgst_rate', 'sgst_rate','igst_rate'],
      dtype='object')
>>> row = t.df.iloc[0]
>>> t.send_tally_request(row)
>>> o = t.batch_import()
>>> type(o)
<class 'pandas.core.series.Series'>
>>> o
>>>o.to_csv('tally_log.txt', sep='\t', index=False)
```


