import os
import openai
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity,
)
import logging

from openai import OpenAI

# Carregando as variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializar o Flask
app = Flask(__name__)

# Configuração do JWT
app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY"
)  # Troque por uma chave secreta forte
jwt = JWTManager(app)

# Definindo a chave da API do OpenAI
# openai.api_key = os.getenv("API_KEY")  # Substitua com sua chave de API do OpenAI

client = OpenAI(api_key=os.getenv("API_KEY"))

# openai.logging = logging.DEBUG
# Armazenando o histórico de mensagens em memória (pode ser substituído por um banco de dados)
conversations = {}


# Rota para login (autenticação)
@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    # Verificar se as credenciais são válidas (aqui estamos fazendo uma verificação simples, mas pode ser mais robusta)
    if username == os.getenv("ADMIN_USERNAME") and password == os.getenv(
        "ADMIN_PASSWORD"
    ):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Credenciais inválidas"}), 401


# Rota para acessar o ChatGPT (requer autenticação)
@app.route("/chatgpt", methods=["POST"])
@jwt_required()
def chatgpt():
    # Pegar a mensagem do usuário
    user_message = request.json.get("message", "")

    if not user_message:
        return jsonify({"msg": "A mensagem não pode estar vazia"}), 400

    user_identity = get_jwt_identity()

    # Recuperar o histórico de conversa para o usuário
    if user_identity not in conversations:
        conversations[user_identity] = []
        conversations[user_identity].append(
            {"role": "system", "content": "Você é um especialista em acústica"}
        )

    # Adicionar a nova mensagem ao histórico
    conversations[user_identity].append({"role": "user", "content": user_message})

    # Criar o prompt para o ChatGPT
    messages = conversations[user_identity]

    try:
        # Chamar a API do OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            n=1,
            stop=None,
            temperature=0.5,
        )
        print(response.choices[0].message.content)
        # Extrair a resposta gerada pelo modelo
        chatgpt_reply = response.choices[0].message.content

        # Adicionar a resposta do ChatGPT ao histórico
        conversations[user_identity].append(
            {"role": "assistant", "content": chatgpt_reply}
        )

        return jsonify({"response": chatgpt_reply}), 200
    except Exception as e:
        # return jsonify({"msg": str(e)}), 500
        return (
            jsonify(
                {
                    "msg": "Desculpe, algo está errado. Por favor volte mais tarde para continuarmos falado de acústica."
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run(debug=True)
