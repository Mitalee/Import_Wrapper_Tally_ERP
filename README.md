# Import_Wrapper_Tally_ERP
A simple python wrapper utilizing the power of Pandas to import sales vouchers as CSV files into Tally ERP 9.


```python

>>> from csv_to_tally import TallyImporter
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
```


