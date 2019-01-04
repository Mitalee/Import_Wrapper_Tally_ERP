import pandas as pd
import requests
from xml.etree import ElementTree as ET

#from app import celery

headers = {"Content-type": "text/xml;charset=UTF-8", "Accept": "text/xml"}

#Beginning tags
beg_xml = """<ENVELOPE>
		<HEADER>
			<VERSION>1</VERSION>
			<TALLYREQUEST>Import</TALLYREQUEST>
			<TYPE>Data</TYPE>
			<ID>Vouchers</ID>
		</HEADER>
		<BODY>
			<DESC>
				<STATICVARIABLES>
				</STATICVARIABLES>
			</DESC>
		<DATA>"""

#end xml
end_xml = """</DATA>
			</BODY>
		</ENVELOPE>"""


class TallyImporter:
	#Load csv file into the class object on initialization
	def __init__(self,filename=None,host_url='http://localhost:9000',num=None):
		self.filename = filename
		if self.filename:
			self.df = pd.read_csv(self.filename, nrows=num, header=0, index_col=False)
			print('loaded file into a dataframe "df".')
		self.url=host_url
		print('loaded url: ', self.url)

	def test_tally(self):
			try:
				#print('url is: ', self.url)
				response = requests.get(self.url, headers=headers)
				if response.status_code == 200:
					tree = ET.fromstring(response.content)
					return('Tally Response: ' + tree.text)
				else: 
					return('Error connecting to Tally, response code is:' + str(response.status_code))
			except requests.exceptions.RequestException as e:
				return(e)

		
	#replaced spaces with underscores and lowercase of all column names
	def clean_columns(self):
		#convert all column names to lowercase
		self.df.columns = [c.lower().replace(' ', '_').replace('/','_') for c in self.df.columns]
		#convert invoice date from string to datetime format
		self.df['invoice_date'] = pd.to_datetime(self.df['invoice_date'], infer_datetime_format=True)
		#convert date format to suit Tally
		self.df['invoice_date'] = self.df['invoice_date'].dt.strftime('%d-%m-%Y')
		#Ignore Cancel and Refund rows
		self.df=self.df[self.df.transaction_type == 'Shipment']
		print(self.df.columns)
		print(self.df.head(3))

	def create_voucher_xml(self, row):

		#Voucher Specifics for GST details
		#print('row is: ',row.invoice_number, ' ',str(row.ship_from_state.lower() == row.ship_to_state.lower()),' ',int(row.igst_rate*100))
		xml_op = f"""<TALLYMESSAGE xmlns:UDF='TallyUDF'>
				<VOUCHER VCHTYPE='Sales' ACTION='Create' OBJVIEW='Invoice Voucher View'>
					<DATE>{row.invoice_date}</DATE> 
					<NARRATION> Amazon Order ID: {row.order_id}</NARRATION>
					<VOUCHERTYPENAME>Sales_amazon</VOUCHERTYPENAME>
					<VOUCHERNUMBER>{row.invoice_number}</VOUCHERNUMBER>
					<PERSISTEDVIEW>Invoice Voucher View</PERSISTEDVIEW>
					<ISINVOICE>Yes</ISINVOICE>
					<LEDGERENTRIES.LIST>
						<ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
						<LEDGERNAME>Amazon IN OMS</LEDGERNAME>
						<AMOUNT>-{row.invoice_amount}</AMOUNT>
					</LEDGERENTRIES.LIST>
					<ALLINVENTORYENTRIES.LIST> 
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
						<STOCKITEMNAME>{row.sku}</STOCKITEMNAME> 
						<AMOUNT>{row.tax_exclusive_gross}</AMOUNT> 
						<ACTUALQTY>{row.quantity}</ACTUALQTY> 
						<BILLEDQTY>{row.quantity}</BILLEDQTY> 
						<RATE>{round(row.tax_exclusive_gross/row.quantity,2)}</RATE>"""

		if row.ship_from_state.lower() == row.ship_to_state.lower():
			xml_op += f"""\n<ACCOUNTINGALLOCATIONS.LIST> 
								<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
								<LEDGERNAME>Local Sales - GST - {int(row.cgst_rate*100)}%</LEDGERNAME> 
								<AMOUNT>{row.tax_exclusive_gross}</AMOUNT> 
							</ACCOUNTINGALLOCATIONS.LIST>
					</ALLINVENTORYENTRIES.LIST>
					<LEDGERENTRIES.LIST> 
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
						<LEDGERNAME>CGST</LEDGERNAME> 
						<AMOUNT>{row.cgst_tax}</AMOUNT> 
					</LEDGERENTRIES.LIST> 
					<LEDGERENTRIES.LIST> 
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
						<LEDGERNAME>SGST</LEDGERNAME> 
						<AMOUNT>{row.sgst_tax}</AMOUNT> 
					</LEDGERENTRIES.LIST>
					</VOUCHER>
					</TALLYMESSAGE>"""
		else:
			xml_op += f"""\n<ACCOUNTINGALLOCATIONS.LIST> 
								<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
								<LEDGERNAME>Interstate Sales - GST - {int(row.igst_rate*100)}%</LEDGERNAME> 
								<AMOUNT>{row.tax_exclusive_gross}</AMOUNT> 
							</ACCOUNTINGALLOCATIONS.LIST>
					</ALLINVENTORYENTRIES.LIST>
					<LEDGERENTRIES.LIST> 
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
						<LEDGERNAME>IGST</LEDGERNAME> 
						<AMOUNT>{row.total_tax_amount}</AMOUNT> 
					</LEDGERENTRIES.LIST>
					</VOUCHER>
					</TALLYMESSAGE>""" 

		#print(xml_op)
		return(xml_op)
		

	def send_tally_request(self, tally_req):
		try:
			response = requests.post(self.url,data=tally_req, headers=headers)
		except requests.exceptions.RequestException as e: #Catch all exceptions
			return(str(e))

		#FOR LOCAL DEBUGGING
		print('TALLY RESPONSE TEXT IS: \n',response.text)

		if response.status_code == 200:
			#print('\n response ok' + csv_row.order_id)
			tree = ET.fromstring(response.content)
			if tree.tag != 'ENVELOPE':
				if tree.tag == 'RESPONSE':
					print('tally response', tree.text, end=':')
					return('Tally Response: ' + tree.text)
			
			else: #Response has 'ENVELOPE'

				c = tree.find(".//CREATED")
				e = tree.find(".//ERRORS")
				le = tree.find(".//LINEERROR")

				if c is not None:
					if c.text == '0': 
						result = "\nA - None created."
						#print(result)
					else: 
						result = ("\nA - Created:" + c.text)
				else: #NO created field
					#print('No Created field. check xml.:')
					result = ("\nNo CREATED field. check xml.:")

				if e is not None:
					if e.text == '0': 
						result += "\nC - No errors."
						#print(result)
					else: 
						result += ("\nC - Errors:" + e.text)
				else: #NO errors field,
					#print('No Created field. check xml.:')
					result = ("\nNo ERRORS field. check xml.:")
				
				if le is not None:
					# LINEERROR IS PRESENT. Return the text.
					#print('LineError')
					result += ("\nLineError: " + le.text)
			#print('result is: ',result)
			return(result)
		else:
			# return Tally Response status code
			#print('server error')
			e = 'Tally Server error: ' + str(response.text) + ', status code: ' + str(response.status_code)
			print('e is: ',e)
			return(e)

	def create_voucher_request(self):

		msg_xml = ''.join(self.df.apply(self.create_voucher_xml, axis=1)) #apply function to each row
		#CHANGE THIS From here
		#https://stackoverflow.com/questions/3900054/python-strip-multiple-characters
		request_xml = (beg_xml+msg_xml+end_xml).replace('\n','').replace('\t','')
		return(request_xml)


	def batch_import_vouchers(self):

		request_xml = self.create_voucher_request()
		result = self.send_tally_request(tally_req=request_xml)
		return(result)

	def create_stockitem_xml(self, stock_item):

		xml_op = f"""<TALLYMESSAGE xmlns:UDF='TallyUDF'> 
					<STOCKITEM NAME='{stock_item}' ACTION='Create'> 
						<NAME.LIST> 
							<NAME>{stock_item}</NAME> 
						</NAME.LIST>   
					<BASEUNITS>nos.</BASEUNITS> 
					</STOCKITEM> 
					</TALLYMESSAGE>"""
		return(xml_op)

	def create_stockitem_request(self,chunksize=50):

		request_xml = []
		stock_list = self.df['sku'].unique()


		for i in range(0,len(stocklist),chunksize):
			msg_xml = ''.join(self.create_stockitem_xml(stock_item=s) for s in stock_list) #apply function to each row
		#CHANGE THIS From here
		#https://stackoverflow.com/questions/3900054/python-strip-multiple-characters
		request_xml.append((beg_xml+msg_xml+end_xml).replace('\n','').replace('\t',''))
		return(request_xml)


	def batch_import_stockitems(self):

		request_xml = self.create_stockitem_request(chunksize=10)

		result = self.send_tally_request(tally_req=request_xml)
		return(result)
