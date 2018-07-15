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
		self.df['invoice_date'] = pd.to_datetime(self.df['invoice_date']).dt.strftime('%Y%m%d')
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
				<VOUCHER VCHTYPE='Sales' ACTION='Create'>
					<DATE>{row.invoice_date}</DATE> 
					<NARRATION> Amazon Order ID: {row.order_id}</NARRATION>
					<VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
					<VOUCHERNUMBER>{row.invoice_number}</VOUCHERNUMBER>
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
						<RATE>{row.tax_exclusive_gross}</RATE> 
						<ACCOUNTINGALLOCATIONS.LIST> 
							<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
							<LEDGERNAME>Sales</LEDGERNAME> 
							<AMOUNT>{row.tax_exclusive_gross}</AMOUNT> 
						</ACCOUNTINGALLOCATIONS.LIST>
					</ALLINVENTORYENTRIES.LIST>"""

		#end xml
		if row.ship_from_state.lower() == row.ship_to_state.lower():
			#xml_cgst_rate = int(row.cgst_rate*100)
			#xml_sgst_rate = int(row.sgst_rate*100)
			xml_op += f"""\n<LEDGERENTRIES.LIST> 
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
						<LEDGERNAME>CGST @{int(row.cgst_rate*100)}%</LEDGERNAME> 
						<AMOUNT>{row.cgst_tax}</AMOUNT> 
					</LEDGERENTRIES.LIST> 
					<LEDGERENTRIES.LIST> 
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
						<LEDGERNAME>SGST @{int(row.sgst_rate*100)}%</LEDGERNAME> 
						<AMOUNT>{row.sgst_tax}</AMOUNT> 
					</LEDGERENTRIES.LIST>"""
		else:
			#xml_igst_rate = int(row.igst_rate*100)
			xml_op += f"""\n<LEDGERENTRIES.LIST> 
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> 
						<LEDGERNAME>IGST @{int(row.igst_rate*100)}%</LEDGERNAME> 
						<AMOUNT>{row.igst_tax}</AMOUNT> 
					</LEDGERENTRIES.LIST>""" 

					
		#end xml
		xml_op += """</VOUCHER>
					</DATA>
					</BODY>
				</ENVELOPE>\n"""

		print(xml_op)
		return(xml_op)
		

	def send_tally_request(self, csv_row):
		xml_row = self.create_xml(csv_row)

		try:
			response = requests.post(url,data=xml_row, headers=headers)
		except requests.exceptions.RequestException as e: #Catch all exceptions
			return(e)

		#print('RESPONSE TEXT IS: \n',response.text)

		if response.status_code == 200:
			tree = ET.fromstring(response.content)
			#TODO - Handle only <RESPONSE> tag from voucher sohel_igst_vchr.xml
			if tree.find("./BODY/DATA/ERRORS").text != '1':
				if tree.find("./BODY/DATA/CREATED") == '1':
					# successful creation of sales voucher
					return('Created. Voucher ID is:'+ tree.find("./BODY/DATA/LASTVCHID").text +\
					 'and' + tree.find(tree.find("./BODY/DATA/DESC/CMPINFOEX/IDINFO/LASTCREATEDVCHID").text))
				else:
					#no error as sent by Tally Response message, yet no Last Voucher ID!
					return('Created Voucher ID not found. No Error.')
			else:
				# No LINEERROR XML tag
				if tree.find("./BODY/DATA/LINEERROR") == None:
					return('Unknown error inserting record.')
				
				else:
					# return LINEERROR XML tag text
					return('Error inserting record' + tree.find("./BODY/DATA/LINEERROR").text)
		else:
			# return Tally Response status code
			return('server error: ', response.status_code)

	def batch_import(self):
		result = self.df.apply(self.send_tally_request, axis=1) #apply function to each row
		return(result)
