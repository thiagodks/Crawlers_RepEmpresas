from termcolor import colored
from time import sleep
import bs4 as bs
import requests
import loadJS

def getCategorias():

	page = loadJS.Page("https://www.reclameaqui.com.br/categoria/")
	soup = bs.BeautifulSoup(page.html, 'html.parser')
	categorias = soup.find_all(class_='col-lg-3 col-md-4 col-sm-6 ng-scope')
	link_categorias = []

	print('Obtendo link das categorias...')
	for categ in categorias:
		categ = str(categ)
		link = categ[categ.find('href=')+6: categ.find('/">')]
		link = categ[categ.find('href=')+6: categ.find('/">')]
		link_categorias.append('https://www.reclameaqui.com.br/'+link+'/')
		print('\thttps://www.reclameaqui.com.br/'+link+'/')

	print("\n\nNumero de categorias: ", len(link_categorias))
	sleep(2)

	return link_categorias

def getEmpresas(link_categorias):

	print('\n\nObtendo link das empresas de cada categoria...\n')
	cont = 1
	link_empresas = {}
	for link in link_categorias:
		print('Categoria '+str(cont)+': \n', link)
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
				if nome_empresa not in link_empresas:
					link_empresas[nome_empresa] = 'https://www.reclameaqui.com.br'+link_empresa
			it += 1
			if it == 3: break
		# if cont == 3: break

	return link_empresas


def getReputacao(link_empresas):

	dicEmpresas = {}

	for nome_empresa in link_empresas:

		if nome_empresa not in dicEmpresas:
			# reclamações, respondidas, não respondidas, tempo de resposta
			dicEmpresas[nome_empresa] = []

		print('Nome da empresa: ', nome_empresa, link_empresas[nome_empresa])
		link = link_empresas[nome_empresa]
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
		dicEmpresas[nome_empresa].append(nota)

		for rep in reputacao:
			dicEmpresas[nome_empresa].append(rep.text.strip())
			cont+=1
			if cont == 4: break

		print(colored(dicEmpresas[nome_empresa], 'yellow'))
		# input("")
	print(dicEmpresas)
	return dicEmpresas

def getComentarios(link_empresas):

	comentarios = {}
	prev_coment = 0
	for nome_empresa in link_empresas:

		if nome_empresa not in comentarios:
			comentarios[nome_empresa] = []

		numPag = 1
		print(colored('Empresa atual: ', 'red'), nome_empresa)
		while True:
			link = link_empresas[nome_empresa]+'lista-reclamacoes/?pagina='+str(numPag)
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
						comentarios[nome_empresa].append((titulo, desc, status, link_empresas[nome_empresa]+link))
						# input(">>")

			numPag += 1

	
	print(comentarios)
	return comentarios


if __name__ == '__main__':

	link_categorias = getCategorias()
	link_empresas = getEmpresas(link_categorias)
	# print('Numero de empresas:', len(link_empresas))
	dicEmpresas =  getReputacao(link_empresas)
	comentarios = getComentarios(link_empresas)


# dicEmpresas = {categoria} -> {nomeEmpresa} [nota, reclamações, respondidas, não respondidas, tempo de resposta]
# comentarios = {nome_empresa} -> [(titulo, desc, status, link)]