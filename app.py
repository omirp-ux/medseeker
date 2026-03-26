from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import unicodedata

app = Flask(__name__)

ARQUIVO_BANCO = "banco_de_dados.json"

def remover_acentos(texto):
    """Remove acentos de uma string"""
    return unicodedata.normalize('NFD', texto).encode('ascii', errors='ignore').decode('utf-8')

def carregar_banco():
    if os.path.exists(ARQUIVO_BANCO):
        with open(ARQUIVO_BANCO, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {
            "Gripe": ["Febre", "Tosse", "Cansaço"],
            "Resfriado": ["Coriza", "Tosse Leve", "Dor de Garganta"],
            "Dor de Cabeça": ["Dor latejante", "Náusea", "Sensibilidade à luz"],
            "Apendicite Aguda": ["Febre Baixa", "Nauseas", "Dor Abdominal"]
        }

def salvar_banco(banco):
    with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
        json.dump(banco, f, ensure_ascii=False, indent=4)

banco_de_dados = carregar_banco()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    dados = request.json
    sintomas_usuario = [remover_acentos(s.strip().lower()) for s in dados.get("sintomas", [])]
    resultados = []

    for doenca, sintomas in banco_de_dados.items():
        match_count = 0
        for sintoma_usuario in sintomas_usuario:
            for sintoma_cadastrado in sintomas:
                if sintoma_usuario in remover_acentos(sintoma_cadastrado.lower()):
                    match_count += 1
                    break

        if match_count > 0:
            prob = (match_count / len(sintomas)) * 100
            resultados.append({"doenca": doenca, "probabilidade": round(prob, 2)})

    resultados.sort(key=lambda x: x["probabilidade"], reverse=True)
    return jsonify(resultados)

@app.route('/adicionar', methods=['POST'])
def adicionar():
    dados = request.json
    nome = dados.get("nome").capitalize()
    sintomas = [s.strip().capitalize() for s in dados.get("sintomas", [])]
    banco_de_dados[nome] = sintomas
    salvar_banco(banco_de_dados)
    return jsonify({"status": "sucesso"})

@app.route('/listar')
def listar():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))
    start = (page - 1) * limit
    end = start + limit

    todas_doencas = [{"nome": k, "sintomas": v} for k, v in banco_de_dados.items()]
    total = len(todas_doencas)
    total_paginas = (total + limit - 1) // limit  # Arredonda para cima

    doencas_pagina = todas_doencas[start:end]

    return jsonify({
        "doencas": doencas_pagina,
        "total_paginas": total_paginas
    })

@app.route('/editar', methods=['POST'])
def editar():
    dados = request.json
    nome = dados.get("nome").capitalize()
    novos_sintomas = [s.strip().capitalize() for s in dados.get("sintomas", [])]
    if nome in banco_de_dados:
        banco_de_dados[nome] = novos_sintomas
        salvar_banco(banco_de_dados)
        return jsonify({"status": "sucesso"})
    return jsonify({"status": "erro", "msg": "Doença não encontrada"})

@app.route('/excluir', methods=['POST'])
def excluir():
    dados = request.json
    nome = dados.get("nome").capitalize()
    if nome in banco_de_dados:
        del banco_de_dados[nome]
        salvar_banco(banco_de_dados)
        return jsonify({"status": "sucesso"})
    return jsonify({"status": "erro", "msg": "Doença não encontrada"})

@app.route('/exportar')
def exportar():
    return send_file(ARQUIVO_BANCO, as_attachment=True)

@app.route('/importar', methods=['POST'])
def importar():
    dados = request.json
    global banco_de_dados
    banco_de_dados = dados
    salvar_banco(banco_de_dados)
    return jsonify({"status": "sucesso"})

if __name__ == '__main__':
    app.run(debug=True)