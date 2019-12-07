from termcolor import colored
from time import sleep
from bs4 import BeautifulSoup
from termcolor import colored
import requests
import loadJS

from pymongo import MongoClient
from pymongo import errors

import send_email as se

def getEmpresas():

	dicEmpresas = {}

	numPag = 1
	while True:

		link = 'https://www.proteste.org.br/reclame/ranking?page='+str(numPag)
		print('Pagina: ', link)
		page = requests.get(link)
		soup = BeautifulSoup(page.text, 'html.parser')
		empresas = soup.find_all(class_='listing__item listing__item--company')

		if len(empresas) == 0: break

		print('Numero de empresas :', len(empresas))
		for empresa in empresas:
			categoria = ((empresa.find('p').text).strip()).replace('\n', '')
			link = 'https://www.proteste.org.br' + empresa.find(class_='chevron-link--after chevron-link--light chevron-link--minor')['href']
			nomeEmpresa = empresa.find(class_='chevron-link--after chevron-link--light chevron-link--minor').text
			nomeEmpresa = nomeEmpresa.replace('\n', '')

			print("Categoria: ", categoria)

			if categoria not in dicEmpresas:
				dicEmpresas[categoria] = {}

			if nomeEmpresa not in dicEmpresas[categoria]:
				dicEmpresas[categoria][nomeEmpresa] = link

			print('Nome da empresa: ', nomeEmpresa)
			print('\tlink: ', link)

		numPag+=1
		# if numPag == 2: break
	
	print("Numero de empresas coletadas: ", len(dicEmpresas))
	print(dicEmpresas)

	return dicEmpresas

def getReputacao(dicEmpresas):

	dicRecl = {}
	count = 1
	aux = 0
	for categoria in dicEmpresas:
		aux += 1
		# if aux == 5:  break
		dicRecl[categoria] = {}
		for nomeEmpresa in dicEmpresas[categoria]:

			print(colored("Iteração: "+str(count)+" de:"+str(len(dicEmpresas)), 'yellow'))
			count+=1

			if nomeEmpresa not in dicRecl[categoria]:
				dicRecl[categoria][nomeEmpresa] = []

			link = dicEmpresas[categoria][nomeEmpresa]
			print(colored('link: '+link, 'red'))
			# link = 'https://www.proteste.org.br/reclame/empresas/sancred-recovery/300000886'
			page = loadJS.Page(link)
			# page = requests.get(link)
			soup = BeautifulSoup(page.html, 'html.parser')
			empresa = soup.find(class_='smiley-rating__score')
			numReclam = soup.find(class_='company-status__title__count')
			recl = soup.find_all(class_='company-status__stats__value')
			print(colored("Empresa", 'green'), empresa)
			try:
				nota = float((empresa.text).split('/')[0])
			except: continue
			numReclam = int(numReclam.text)

			reclamacoes = []
			for rec in recl:
				reclamacoes.append(rec.text)

			# recConc = int(recConc.text)

			print(colored('Nota: ', 'blue'), nota)
			print(colored('Numero de reclamaçoes: ', 'blue'), numReclam)
			print(colored('Reclamações: ', 'blue'), reclamacoes)
			dicRecl[categoria][nomeEmpresa].append([nota, numReclam]+reclamacoes)
			# print(dicRecl[categoria])
			# input("")

	print(dicRecl)
	return dicRecl

def getComentarios():

	dicComent = {}

	print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n')

	numPag = 1
	while True:
		# if numPag == 5: break
		link = 'https://www.proteste.org.br/reclame/lista-de-reclamacoes-publicas?sectors=555&page='+str(numPag)

		print(colored("Pagina atual: "+str(numPag), 'yellow'))
		page = loadJS.Page(link)
		soup = BeautifulSoup(page.html, 'html.parser')
		comentarios = soup.find_all(class_='complaint-list__item')
		if len(comentarios) == 0: break

		for coment in comentarios:

			nomeEmpresa = (coment.find(class_='complaint-stub__company js-truncate').text).replace('\n', '')
			link = 'https://www.proteste.org.br'+coment.find(class_='chevron-link chevron-link--after chevron-link--light chevron-link--minor')['href']
			titulo = (coment.find(class_='gamma').text).strip()
			desc = (coment.find(class_='last').text).strip()
			
			print('\n'+nomeEmpresa+'\n', link+'\n', titulo+'\n', desc+'\n')
			
			if nomeEmpresa not in dicComent:
				dicComent[nomeEmpresa] = []

			dicComent[nomeEmpresa].append([titulo, desc, link])
		numPag += 1
	
	return dicComent

def insertToDatabase(banco, dicRecl, dicComent):
	
	for categoria in dicRecl.keys():
		for empresa in dicRecl[categoria]:
			nomeEmpresa = str(empresa).strip()
			print("Inserindo dados da empresa", nomeEmpresa)
			print(dicRecl[categoria][empresa])
			nota = dicRecl[categoria][empresa][0][0]
			reclamacoes = int(dicRecl[categoria][empresa][0][1])
			respondidas = int(dicRecl[categoria][empresa][0][2])
			n_respondidas = int(dicRecl[categoria][empresa][0][3])
			tempo_resposta = dicRecl[categoria][empresa][0][4]
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
			for comentario in dicComent[empresa]:

				titulo = comentario[0]
				desc = comentario[1]
				# status = comentario[2]
				link = comentario[2]
				print(titulo+'\n', desc+'\n', link+'\n')
				jsonComentario = {
					"titulo": titulo,
					"descricao": desc,
					"link": link
				}

				jsonEmpresa["reclamacoes"].append(jsonComentario)

			banco.empresas.insert_one(jsonEmpresa)

if __name__ == '__main__':	

	email = 'mrtrotta2010@gmail.com'

	try:
		cliente = MongoClient('localhost', 27017)
		banco = cliente.testetp2
		se.sendEmail(email, "Iniciando Crawler TP2 - Proteste", "...")

		dicEmpresas = getEmpresas()
		se.sendEmail(email, "Crawler TP2 - Proteste (1/4)", "Obteve todas as empresas!")
		dicRecl = getReputacao(dicEmpresas)
		se.sendEmail(email, "Crawler TP2 - Proteste (2/4)", "Obteve todas as reclamações!")
		dicComent = getComentarios()
		se.sendEmail(email, "Crawler TP2 - Proteste (3/4)", "Obteve todas os comentarios!")

		# print(dicRecl+'\n\n\n\n')
		# print(dicComent)

		insertToDatabase(banco, dicRecl, dicComent)
		se.sendEmail(email, "Crawler TP2 - Proteste (4/4)", "Os dados foram inseridos no banco de dados!")

	except Exception as e:
		print(e)
		se.sendEmail(email, "ERRO Crawler TP2- Proteste", "Ocorreu uma exceção:\n"+str(e))