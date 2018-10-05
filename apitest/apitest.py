import pandas as pd
import requests
from xml.etree import ElementTree as ET
from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__, static_url_path="")
api = Api(app)
auth = HTTPBasicAuth()

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

class TestTally(Resource):
	def __init__(self,host_url='http://192.168.1.3:9002'):
		self.url = host_url
		super(TestTally, self).__init__()

	def get(self):
		try:
			#print('url is: ', self.url)
			response = requests.get(self.url, headers=headers)
			if response.status_code == 200:
				tree = ET.fromstring(response.content)
				return('Tally Response: ' + tree.text)
			else: 
				return('Error connecting to Tally, response code is:' + str(response.status_code))
		except requests.exceptions.RequestException as e:
			return(str(e))

api.add_resource(TestTally, '/tally/api/v0.1/testtally',endpoint='testtally')

if __name__ == '__main__':
    app.run(debug=True)
