import pandas as pd
import requests
from xml.etree import ElementTree as ET

url = 'http://localhost:9000'
headers = {"Content-type": "text/xml;charset=UTF-8", "Accept": "text/xml"}


class TallyImporter:
	def __init__(self,filename=None):
		self.filename = filename
		if self.filename:
			self.df = pd.read_csv(self.filename, header=0, index_col=False)
			print('loaded file into df.')
		

	def clean_columns(self):
		self.df.columns = [c.lower().replace(' ', '_').replace('/','_') for c in self.df.columns]
		self.df['invoice_date'] = pd.to_datetime(self.df['invoice_date']).dt.strftime('%Y%m%d')
		print(self.df.columns)
