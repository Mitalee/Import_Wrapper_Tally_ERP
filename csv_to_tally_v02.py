import pandas as pd
import requests
from xml.etree import ElementTree as ET

url = 'http://localhost:9000'
headers = {"Content-type": "text/xml;charset=UTF-8", "Accept": "text/xml"}


class TallyImporter:
	#Load csv file into the class object on initialization
	def __init__(self,filename=None):
		self.filename = filename
		if self.filename:
			self.df = pd.read_csv(self.filename, header=0, index_col=False)
			print('loaded file into a dataframe "df".')
		
	#replaced spaces with underscores and lowercase of all column names
	def clean_columns(self):
		self.df.columns = [c.lower().replace(' ', '_').replace('/','_') for c in self.df.columns]
		#keep only date and strip time from invoice date
		self.df['invoice_date'] = self.df['invoice_date'].str[:-6]
		print(self.df.columns)

	def create_xml(self, row):
		#Beginning tags
		xml_op = """<ENVELOPE>
				<HEADER>
					<VERSION>1</VERSION>
					<TALLYREQUEST>Import</TALLYREQUEST>
					<TYPE>Data</TYPE>
					<ID>Vouchers</ID>
				</HEADER>
				<BODY>
					<DESC>
						<STATICVARIABLES>
							<SVCURRENTCOMPANY>Test Sales Import</SVCURRENTCOMPANY>
						</STATICVARIABLES>
					</DESC>
				<DATA>\n"""

		#Voucher Specifics excluding GST details
		xml_op += f"""<TALLYMESSAGE>
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
					<LEDGERENTRIES.LIST> 
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
						<LEDGERNAME>Sales Account</LEDGERNAME> 
						<AMOUNT>{row.tax_exclusive_gross}</AMOUNT> 
					</LEDGERENTRIES.LIST>"""

		#end xml
		if row.ship_from_state.lower() == row.ship_to_state.lower():
			#xml_cgst_rate = int(row.cgst_rate*100)
			#xml_sgst_rate = int(row.sgst_rate*100)
			xml_op += f"""\n<LEDGERENTRIES.LIST> 
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
						<LEDGERNAME>CGST</LEDGERNAME> 
						<AMOUNT>{row.cgst_tax}</AMOUNT> 
					</LEDGERENTRIES.LIST> 
					<LEDGERENTRIES.LIST> 
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
						<LEDGERNAME>SGST</LEDGERNAME> 
						<AMOUNT>{row.sgst_tax}</AMOUNT> 
					</LEDGERENTRIES.LIST>"""
		else:
			#xml_igst_rate = int(row.igst_rate*100)
			xml_op += f"""\n<LEDGERENTRIES.LIST> 
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
						<LEDGERNAME>IGST</LEDGERNAME> 
						<AMOUNT>{row.igst_tax}</AMOUNT> 
					</LEDGERENTRIES.LIST>""" 

					
		#end xml
		xml_op += """</VOUCHER>
					</TALLYMESSAGE>
					</DATA>
					</BODY>
				</ENVELOPE>\n"""

		#print(xml_op)
		return(xml_op)
		

	def send_tally_request(self, csv_row):
		xml_row = self.create_xml(csv_row)

		try:
			response = requests.post(url,data=xml_row, headers=headers)
		except requests.exceptions.RequestException as e: #Catch all exceptions
			return(e)

		#print('RESPONSE TEXT IS: \n',response.text)

		if response.status_code == 200:
			#print(response.content)
			tree = ET.fromstring(response.content)
			if tree.tag != 'ENVELOPE':
				if tree.tag == 'RESPONSE':
					return('Tally Response: ' + tree.text)
			else: #Response has 'ENVELOPE'
				if tree.find("./BODY/DATA/LINEERROR") is None:
					if tree.find("./BODY/DATA/IMPORTRESULT/CREATED").text == '1':
						# successful creation of sales voucher
						return('Amazon Invoice:' + tree.find("./BODY/DATA/IMPORTRESULT/VCHNUMBER").text +\
						 ' - Tally Voucher ID:'+ tree.find("./BODY/DATA/IMPORTRESULT/LASTVCHID").text)

					else: #Created is 0 but no LINEERROR
						#TODO - what if created is 0 and no LINEERROR?
						return('Created tag not equal to 1, yet no LINEERROR. DEBUG code.')
				else:  
					# LINEERROR IS PRESENT. Return the text.
					return('Amazon Invoice: ' + csv_row.invoice_number + '- LineError: ' + tree.find("./BODY/DATA/LINEERROR").text)
		else:
			# return Tally Response status code
			print('server error')
			return('server error: ', response.status_code)

	def batch_import(self):
		result = self.df.apply(self.send_tally_request, axis=1) #apply function to each row
		return(result)
