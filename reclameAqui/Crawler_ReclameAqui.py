from termcolor import colored
from time import sleep
import bs4 as bs
import requests
import loadJS

from pymongo import MongoClient
from pymongo import errors

import send_email as se

def getCategorias():

	page = loadJS.Page("https://www.reclameaqui.com.br/categoria/")
	soup = bs.BeautifulSoup(page.html, 'html.parser')
	categorias = soup.find_all(class_='col-lg-3 col-md-4 col-sm-6 ng-scope')
	link_categorias = {}

	print('Obtendo link das categorias...')
	for categ in categorias:
		nomeCateg = (categ.find(class_='ng-binding').text).strip()
		print("nome da categoria: "+nomeCateg)
		# input("")
		categ = str(categ)
		link = categ[categ.find('href=')+6: categ.find('/">')]
		link = categ[categ.find('href=')+6: categ.find('/">')]
		link_categorias[nomeCateg] = 'https://www.reclameaqui.com.br/'+link+'/'
		# link_categorias.append('https://www.reclameaqui.com.br/'+link+'/')
		print('\thttps://www.reclameaqui.com.br/'+link+'/')

	print("\n\nNumero de categorias: ", len(link_categorias))
	sleep(2)

	# print(link_categorias)
	# input("")

	return link_categorias

def getEmpresas(link_categorias):

	print('\n\nObtendo link das empresas de cada categoria...\n')
	cont = 1
	link_empresas = {}
	for categoria in link_categorias:
		link_empresas[categoria] = {}
		print("categoria;", categoria)
		link = link_categorias[categoria]
		# for link in link_categorias[categoria]:
		# print("link:", link)
		print('Categoria '+str(cont)+': \n', link)
		# input("")
		cont+=1

		page = loadJS.Page(link)
		soup = bs.BeautifulSoup(page.html, 'html.parser')
		feedB = soup.find_all(class_='box-gray')

		it = 0
		for mpr in feedB:
			mpr = mpr.find_all(class_='business-name ng-binding')
			for x in mpr:
				nome_empresa = x['title']
				link_empresa = x['href']
				print('\tEmpresa: ', nome_empresa, link_empresa)
				if nome_empresa not in link_empresas[categoria]:
					link_empresas[categoria][nome_empresa] = 'https://www.reclameaqui.com.br'+link_empresa
			it += 1
			if it == 3: break
		# if cont == 3: break

	return link_empresas


def getReputacao(link_empresas):

	dicEmpresas = {}
	count = 0
	print(len(link_empresas))
	# input("")
	for categoria in link_empresas:
		dicEmpresas[categoria] = {}
		for nome_empresa in link_empresas[categoria]:
			count += 1
			# if count == 10: break
			if nome_empresa not in dicEmpresas[categoria]:
				# nota reclamações, respondidas, não respondidas, tempo de resposta
				dicEmpresas[categoria][nome_empresa] = []

			print('Nome da empresa: ', nome_empresa, link_empresas[categoria][nome_empresa])
			link = link_empresas[categoria][nome_empresa]
			page = loadJS.Page(link)
			# sleep(2)
			soup = bs.BeautifulSoup(page.html, 'html.parser')

			nota = -1
			try:
				nota = (soup.find(class_='company-index fixed')).find(class_='ng-binding').text
			except: pass

			try:
				nota = float((soup.find(class_='current-score ng-binding').text).strip())
			except: pass

			reputacao = soup.find_all(class_='company-index-value')
			sleep(1)
			cont = 0

			if len(reputacao) == 0: continue
			dicEmpresas[categoria][nome_empresa].append(nota)

			for rep in reputacao:
				dicEmpresas[categoria][nome_empresa].append(rep.text.strip())
				cont+=1
				if cont == 4: break

			print(colored(dicEmpresas[categoria][nome_empresa], 'yellow'))
			# input("")
	# print(dicEmpresas)
	# input(">>>>>>")
	# input(">>>>>>")
	return dicEmpresas

def getComentarios(link_empresas):

	comentarios = {}
	prev_coment = 0
	count = 0
	for categoria in link_empresas:

		for nome_empresa in link_empresas[categoria]:
			count += 1
			# if count == 10: break
			if nome_empresa not in comentarios:
				comentarios[nome_empresa] = []

			numPag = 1
			print(colored('Empresa atual: ', 'red'), nome_empresa)
			while True:
				link = link_empresas[categoria][nome_empresa]+'lista-reclamacoes/?pagina='+str(numPag)
				print(colored('Link atual: ', 'yellow'), link)
				page = loadJS.Page(link)
				sleep(2)
				soup = bs.BeautifulSoup(page.html, 'html.parser')
				tds_comentarios = soup.find_all(class_='content-loader')
				if prev_coment == tds_comentarios: break
				prev_coment = tds_comentarios

				labels = ['label-not-answered', 'label-reply', 'label-resolved']
				
				for coment in tds_comentarios:
					coment = coment.find_all(class_='ng-scope')

					for i in range(0, len(coment), 2):

							for label in labels:
								try: link = coment[i].find(class_='link-complain-id-complains '+label)['href']; break
								except: pass

							titulo = coment[i].find(class_='text-title ng-binding')['title']
							desc = coment[i].find(class_='text-description ng-binding').text
							status = coment[i+1].text
							print(colored('Titulo: ', 'green'), titulo)
							print(colored('\tLink: ', 'blue'), 'https://www.reclameaqui.com.br/empresa'+link)
							print(colored('\tDesc: ', 'blue'), desc)
							print(colored('\tStatus: ', 'blue'), status)
							comentarios[nome_empresa].append((titulo, desc, status, link_empresas[categoria][nome_empresa]+link))
							# input(">>")

				numPag += 1
				# break
		

	
	# print(comentarios)
	return comentarios

def insertToDatabase(banco, dicEmpresas, comentarios):
	
	for categoria in dicEmpresas.keys():
		for empresa in dicEmpresas[categoria]:
			nomeEmpresa = str(empresa).strip()
			print("Inserindo dados da empresa", nomeEmpresa)
			print(dicEmpresas[categoria][empresa])
			nota = dicEmpresas[categoria][empresa][0]
			reclamacoes = int(dicEmpresas[categoria][empresa][1])
			respondidas = int(dicEmpresas[categoria][empresa][2])
			n_respondidas = int(dicEmpresas[categoria][empresa][3])
			tempo_resposta = dicEmpresas[categoria][empresa][4]
			print(str(nota)+'\n', str(reclamacoes)+'\n', str(n_respondidas)+'\n', tempo_resposta+'\n')
			
			jsonEmpresa = {
				"nome": empresa,
				"categoria": categoria,
				"nota": nota,
				"numReclamacoes": reclamacoes,
				"numRespondidas": respondidas,
				"numNaoRespondidas": n_respondidas,
				"tempoResposta": tempo_resposta,
				"reclamacoes": []
			}

			print("Inserindo comendarios da empresa: ", empresa)
			for comentario in comentarios[empresa]:

				titulo = comentario[0]
				desc = comentario[1]
				status = comentario[2]
				link = comentario[3]
				print(titulo+'\n', desc+'\n', status+'\n', link+'\n')
				jsonComentario = {
					"titulo": titulo,
					"descricao": desc,
					"status": status,
					"link": link
				}

				jsonEmpresa["reclamacoes"].append(jsonComentario)

			banco.empresas.insert_one(jsonEmpresa)

if __name__ == '__main__':

	email = 'mrtrotta2010@gmail.com'

	try:
		cliente = MongoClient('localhost', 27017)
		banco = cliente.tp2bd

		link_categorias = getCategorias()
		se.sendEmail(email, "Iniciando Crawler TP2...", "...")
		link_empresas = getEmpresas(link_categorias)
		se.sendEmail(email, "Crawler TP2 (1/4)", "Obteve todas as empresas!")
		# print('Numero de empresas:', len(link_empresas))
		dicEmpresas =  getReputacao(link_empresas)
		se.sendEmail(email, "Crawler TP2 (2/4)", "Obteve todas as reputações!")

		# for categoria in dicEmpresas:
		# 	print("Categoria: ", categoria)
		# 	for nomeEmp in dicEmpresas[categoria]:
		# 		print('\tEmpresa: ', nomeEmp)

		# input("")
		comentarios = getComentarios(link_empresas)
		se.sendEmail(email, "Crawler TP2 (3/4)", "Obteve todas os comentarios!")

		insertToDatabase(banco, dicEmpresas, comentarios)
		se.sendEmail(email, "Crawler TP2 (4/4)", "Os dados foram inseridos no banco de dados!")
	
	except Exception as e:
		se.sendEmail(email, "ERRO Crawler TP2", "Ocorreu uma exceção:\n"+str(e))

# dicEmpresas = {categoria} -> {nomeEmpresa} [nota, reclamações, respondidas, não respondidas, tempo de resposta]
# comentarios = {nome_empresa} -> [(titulo, desc, status, link)]