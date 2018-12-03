import psycopg2
import re
import json
import sys
import datetime
import urllib.request
# import parser

from bs4 import BeautifulSoup
from urllib.request import urlopen

class PostgreSQL(object):
	def __init__(self):
		self.conn = None
		self.cur  = None

	def connect(self):
		try:
			self.conn = psycopg2.connect(host='ec2-54-83-50-145.compute-1.amazonaws.com',
										database='dc9l11ha37gka3',
										user='ypwropixtpclqq',
										port='5432',
										password='00d68c8980033deb229a692dff10d9ffb8b2253421f84aa102055f08fee55af9')

		except Exception as e:
			print('Conexão inválida! Erro: ')
			print(e)

	def setCursor(self):
		try:
			self.cur = self.conn.cursor()
		except Exception as e:
			print(e)


	def getUsers(self):
		try:
			self.cur.execute("SELECT username FROM auth_user")
			return self.cur.fetchall()
		except Exception as e:
			print(e)

	def getPass(self, usr):
		try:
			self.cur.execute("SELECT * FROM auth_user")
			print(self.cur.fetchall())
			self.cur.execute("SELECT password FROM auth_user WHERE username = '%s'", usr)
			print(self.cur.fetchall())
			return self.cur.fetchall()
		except Exception as e:
			print(e)

	def getEmails(self):
		try:
			self.cur.execute("SELECT email FROM auth_user")
			return self.cur.fetchall()
		except Exception as e:
			print(e)

	def getEstabelecimentos(self):
		try:
			self.cur.execute("SELECT * FROM notas_estabelecimento")
			return self.cur.fetchall()
		except Exception as e:
			print(e)

	def getNotas(self):
		try:
			self.cur.execute("SELECT * FROM notas_nota")
			return self.cur.fetchall()
		except Exception as e:
			print(e)

	def getProdutos(self):
		try:
			self.cur.execute("SELECT * FROM notas_produto")

			return self.cur.fetchall()
		except Exception as e:
			print(e)

	def getAllTables(self):
		self.cur.execute("SELECT * FROM pg_catalog.pg_tables")
		return self.cur.fetchall()

	def buscarUser(self, usr):
		rows = self.getUsers()
		for row in rows:
			print(row)
			print(str(usr))
			if str(usr) == row[0]:
				return row

	def buscarPass(self, usr, pwd):
		#print(crypt(pwd))
		rows = self.getPass(usr)

		for row in rows:
			if str(pwd) == row[0]:
				return row 

	def buscarEmail(self, email):
		rows = self.getEmails()
		for row in rows:
			if str(email) == (row):
				return row

	def buscarEstabelecimento(self, cnpj):
		rows = self.getEstabelecimentos()
		for row in rows:
			if str(cnpj) == (row[1]):
				return row 

	def buscarProdutos(self, nome):
		produtos = list()
		rows = self.getProdutos()
		for row in rows:
			if nome.upper() in row[2].upper():
				produtos.append(row)

		return produtos

	def buscarNota(self, codigo):
		rows = self.getNotas()
		for row in rows:
			if str(codigo) == str(row[1]):
				return row

	def getEmpresa(self, cnpj):
		cnpj_clean = str(cnpj)
		cnpj_clean = cnpj_clean.replace('.', '')
		cnpj_clean = cnpj_clean.replace('/', '')
		cnpj_clean = cnpj_clean.replace('-', '')
		cnpj_clean = cnpj_clean.replace(' ', '')

		url = 'http://receitaws.com.br/v1/cnpj/{0}'.format(cnpj_clean)
		opener = urllib.request.build_opener()
		opener.addheaders = [
			('User-agent',
			 " Mozilla/5.0 (Windows NT 6.2; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0")]

		with opener.open(url) as fd:
			info = fd.read().decode()

		dic = json.loads(info)

		empresa = {}
		empresa['cnpj']   = dic['cnpj']
		empresa['nome']   = dic['fantasia']
		empresa['email']  = dic['email']
		empresa['rua']    = dic['logradouro']
		empresa['numero'] = dic['numero']
		empresa['bairro'] = dic['bairro']
		empresa['cep']    = dic['cep']
		empresa['cidade'] = dic['municipio']
		empresa['uf']     = dic['uf']

		if empresa['nome'] == '':
			empresa['nome'] = dic['nome']

		return empresa

	def executeQuery(self, query):
		try:
			self.cur.execute(query)
			return self.cur.fetchall()
		except Exception as e:
			raise e

	def qrcode(self, url):
		if len(url) == 0:
			print('URL vazia!')
			return

		if len(url) == 44:
			url = 'https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx?chNFe=' + url + '&'

		if  len(url) < 98:
			print('URL inválida!')
			return

		if str(url[0:53]) != 'https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx?chNFe=':
			print('URL inválida!')
			return
		
		try:
			doc = urlopen(url).read().decode('utf-8')
			link = BeautifulSoup(doc, 'html.parser').iframe['src']

			doc = urlopen(link).read().decode('iso-8859-1')
			soup = BeautifulSoup(doc, 'html.parser')

		except Exception as e:
			print(e)
			return
		try:
			data = {}
			cnpj = soup.find('td', class_='NFCCabecalho_SubTitulo1').string[55:73]
			data['empresa'] = self.getEmpresa(cnpj)

			data['chave'] = url[53:97]

			date = soup.find_all('td', class_='NFCCabecalho_SubTitulo')[2].string
			ind = date.find('Data de Emissão: ') + len('Data de Emissão: ')
			date = date[ind:].split(' ')
			data['data'] = [int(i) for i in date[0].split('/')] + [int(i) for i in date[1].split(':')]
			data['produtos'] = {}

			for tag in soup.find_all('tr', id=re.compile("Item +")):
				produto = []
				for child in tag.find_all('td', class_='NFCDetalhe_Item'):
					produto.append(child.string)

				del produto[5]
				del produto[2]

				data['produtos'][tag['id']] = produto

				data['erro'] = False
			return data
		except Exception as e:
			print(e)
			return

	def InserirNFE(self, chave):
		nfe = self.qrcode(chave)

		if nfe['erro']:
			return None

		empresa = nfe['empresa']

		if not self.buscarEstabelecimento(cnpj=empresa['cnpj']):
			print(self.executeQuery("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'notas_estabelecimento'"))
			self.cur.execute("INSERT INTO notas_estabelecimento (cnpj, nome, email, rua, numero, bairro, cep, cidade, uf) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" %
				(empresa['cnpj'], empresa['nome'], empresa['email'], empresa['rua'], empresa['numero'],
				empresa['bairro'], empresa['cep'], empresa['cidade'], empresa['uf']))
			self.conn.commit()

		if not self.buscarNota(nfe['chave']):
			d = nfe['data']
			data = datetime.date(d[2], d[1], d[0])

			mercado = self.executeQuery("SELECT id FROM notas_estabelecimento WHERE cnpj = '%s'" % empresa['cnpj'])
			self.cur.execute("INSERT INTO notas_nota (chave, data, empresa_id) VALUES (%s, '%s', '%s')" % (nfe['chave'], data, mercado[0][0]))
			self.conn.commit()

			nota = self.executeQuery("SELECT id FROM notas_nota WHERE chave = '%s'" % nfe['chave'])

			for prod in nfe['produtos']:
				print(self.executeQuery("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'notas_produto'"))
				self.cur.execute("INSERT INTO notas_produto (codigo, descricao, unidade, preco, nota_id) VALUES('%s', '%s', '%s', '%s', '%s')" % (nfe['produtos'][prod][0],
					nfe['produtos'][prod][1], nfe['produtos'][prod][2], nfe['produtos'][prod][3], nota[0][0]))
				self.conn.commit()

			print('Nota fiscal inserida com sucesso!')
		else:
			print('Nota fiscal já existe no banco!')

def howTo():
	db = PostgreSQL()
	db.connect()
	db.setCursor()

	produtos = db.getProdutos()
	mercados = db.getEstabelecimentos()
	notas    = db.getNotas()

	p = db.buscarProdutos('gasolina')
	e = db.buscarEstabelecimento('87.397.865/0019-40') 
	n = db.buscarNota('43180387397865001940652080000042681261512136')

	q = db.executeQuery("""SELECT * FROM "auth_user" """)

	#print('produtos')
	#print(produtos)

	#print('mercados')
	#print(mercados)

	#print('notas')
	#print(notas)

	#print('produto')
	#print(p)

	#print('mercado')
	#print(e)

	#print('nota')
	#print(n)

	#print('query')
	#print(q)

	#db.setTable('gasolina')