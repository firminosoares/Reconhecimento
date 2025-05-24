#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script otimizado para configuração do bot de reconhecimento facial no Render.com
Versão com consumo reduzido de memória para funcionar no plano gratuito
"""

import os
import sys
import logging
import tempfile
import numpy as np
import cv2
import face_recognition  # Biblioteca mais leve que DeepFace
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Estados para o ConversationHandler
ESPERANDO_PRIMEIRA_FOTO = 1
ESPERANDO_SEGUNDA_FOTO = 2

# Diretório para armazenar imagens temporárias
TEMP_DIR = tempfile.gettempdir()

# Token do bot
TOKEN = "7736951978:AAFheBfSTrvkgl40ALpR-_3Vdd80BL4yDHU"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia mensagem quando o comando /start é emitido."""
    await update.message.reply_text(
        "Olá! Eu sou o Recon Facial Bot, especialista em comparação de imagens faciais.\n\n"
        "Para iniciar uma comparação, envie o comando /reconhecimento.\n\n"
        "Para obter ajuda, envie /ajuda."
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia mensagem de ajuda quando o comando /ajuda é emitido."""
    await update.message.reply_text(
        "Como usar o Recon Facial Bot:\n\n"
        "1. Envie o comando /reconhecimento\n"
        "2. Envie a primeira foto com um rosto\n"
        "3. Envie a segunda foto com um rosto\n"
        "4. Aguarde o resultado da comparação\n\n"
        "O resultado mostrará a porcentagem de similaridade entre os rostos e o nível de confiabilidade da análise."
    )

async def reconhecimento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o processo de reconhecimento facial."""
    await update.message.reply_text(
        "Vamos iniciar a comparação facial!\n\n"
        "Por favor, envie a primeira foto contendo um rosto."
    )
    # Limpa dados anteriores se existirem
    if 'primeira_foto' in context.user_data:
        del context.user_data['primeira_foto']
    if 'segunda_foto' in context.user_data:
        del context.user_data['segunda_foto']
    
    return ESPERANDO_PRIMEIRA_FOTO

def detectar_rosto(imagem_path):
    """Detecta rostos em uma imagem usando face_recognition (mais leve que DeepFace)."""
    # Carrega a imagem usando OpenCV
    imagem = cv2.imread(imagem_path)
    if imagem is None:
        return False, "Erro ao carregar imagem"
    
    # Converte BGR para RGB (face_recognition usa RGB)
    rgb_imagem = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
    
    # Detecta rostos na imagem
    localizacoes_rostos = face_recognition.face_locations(rgb_imagem, model="hog")  # Modelo HOG é mais leve que CNN
    
    if len(localizacoes_rostos) == 0:
        return False, "Nenhum rosto detectado"
    
    if len(localizacoes_rostos) > 1:
        return False, f"Múltiplos rostos ({len(localizacoes_rostos)}) detectados"
    
    return True, localizacoes_rostos[0]

def extrair_caracteristicas(imagem_path, localizacao_rosto):
    """Extrai características faciais para comparação."""
    # Carrega a imagem
    imagem = cv2.imread(imagem_path)
    rgb_imagem = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
    
    # Extrai as características faciais (encodings)
    encodings = face_recognition.face_encodings(rgb_imagem, [localizacao_rosto])
    
    if len(encodings) == 0:
        return None
    
    return encodings[0]

def comparar_rostos(encoding1, encoding2):
    """Compara dois encodings faciais e retorna a similaridade."""
    # Calcula a distância facial (quanto menor, mais similar)
    distancia = face_recognition.face_distance([encoding1], encoding2)[0]
    
    # Converte a distância para similaridade (0-100%)
    similaridade = max(0, min(100, (1 - distancia) * 100))
    
    # Determina o nível de confiabilidade
    if distancia < 0.4:
        confiabilidade = "Alta"
    elif distancia < 0.6:
        confiabilidade = "Média"
    else:
        confiabilidade = "Baixa"
    
    return {
        "similaridade": similaridade,
        "confiabilidade": confiabilidade,
        "distancia": distancia
    }

async def receber_primeira_foto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a primeira foto e verifica se contém um rosto."""
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()
    
    # Cria um nome de arquivo temporário para a primeira foto
    primeira_foto = os.path.join(TEMP_DIR, f'primeira_foto_{user.id}.jpg')
    await photo_file.download_to_drive(primeira_foto)
    
    logger.info(f"Primeira foto recebida de {user.first_name} e salva em {primeira_foto}")
    
    # Verifica se há um rosto na imagem
    try:
        sucesso, resultado = detectar_rosto(primeira_foto)
        
        if not sucesso:
            await update.message.reply_text(
                f"Não foi possível processar a imagem: {resultado}\n\n"
                "Por favor, envie outra foto onde o rosto esteja claramente visível."
            )
            # Remove o arquivo temporário
            os.remove(primeira_foto)
            return ESPERANDO_PRIMEIRA_FOTO
        
        # Extrai características faciais
        localizacao_rosto = resultado
        encoding = extrair_caracteristicas(primeira_foto, localizacao_rosto)
        
        if encoding is None:
            await update.message.reply_text(
                "Não foi possível extrair características faciais da imagem.\n\n"
                "Por favor, envie outra foto com melhor qualidade e iluminação."
            )
            # Remove o arquivo temporário
            os.remove(primeira_foto)
            return ESPERANDO_PRIMEIRA_FOTO
        
        # Salva o caminho da primeira foto e o encoding no contexto
        context.user_data['primeira_foto'] = primeira_foto
        context.user_data['primeiro_encoding'] = encoding.tolist()  # Converte para lista para ser serializável
        
        await update.message.reply_text(
            "Primeira foto recebida com sucesso!\n\n"
            "Agora, por favor, envie a segunda foto contendo um rosto para comparação."
        )
        
        return ESPERANDO_SEGUNDA_FOTO
    
    except Exception as e:
        logger.error(f"Erro ao processar a primeira foto: {e}")
        await update.message.reply_text(
            "Ocorreu um erro ao processar a imagem.\n\n"
            "Por favor, envie outra foto com melhor qualidade e iluminação."
        )
        # Remove o arquivo temporário
        if os.path.exists(primeira_foto):
            os.remove(primeira_foto)
        return ESPERANDO_PRIMEIRA_FOTO

async def receber_segunda_foto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a segunda foto, verifica se contém um rosto e realiza a comparação."""
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()
    
    # Cria um nome de arquivo temporário para a segunda foto
    segunda_foto = os.path.join(TEMP_DIR, f'segunda_foto_{user.id}.jpg')
    await photo_file.download_to_drive(segunda_foto)
    
    logger.info(f"Segunda foto recebida de {user.first_name} e salva em {segunda_foto}")
    
    # Verifica se há um rosto na imagem
    try:
        sucesso, resultado = detectar_rosto(segunda_foto)
        
        if not sucesso:
            await update.message.reply_text(
                f"Não foi possível processar a imagem: {resultado}\n\n"
                "Por favor, envie outra foto onde o rosto esteja claramente visível."
            )
            # Remove o arquivo temporário
            os.remove(segunda_foto)
            return ESPERANDO_SEGUNDA_FOTO
        
        # Extrai características faciais
        localizacao_rosto = resultado
        segundo_encoding = extrair_caracteristicas(segunda_foto, localizacao_rosto)
        
        if segundo_encoding is None:
            await update.message.reply_text(
                "Não foi possível extrair características faciais da imagem.\n\n"
                "Por favor, envie outra foto com melhor qualidade e iluminação."
            )
            # Remove o arquivo temporário
            os.remove(segunda_foto)
            return ESPERANDO_SEGUNDA_FOTO
        
        # Informa ao usuário que a comparação está sendo processada
        await update.message.reply_text(
            "Segunda foto recebida com sucesso!\n\n"
            "Processando a comparação facial... Por favor, aguarde alguns instantes."
        )
        
        # Realiza a comparação facial
        primeiro_encoding = np.array(context.user_data['primeiro_encoding'])  # Converte de volta para numpy array
        
        # Compara os rostos
        try:
            resultado = comparar_rostos(primeiro_encoding, segundo_encoding)
            
            # Extrai os resultados
            similaridade = resultado["similaridade"]
            confiabilidade = resultado["confiabilidade"]
            
            # Envia o resultado ao usuário
            await update.message.reply_text(
                f"✅ Análise concluída!\n\n"
                f"📊 Resultado da comparação facial:\n\n"
                f"Similaridade: {similaridade:.2f}%\n"
                f"Confiabilidade: {confiabilidade}\n\n"
                f"Para realizar uma nova comparação, envie o comando /reconhecimento novamente."
            )
            
        except Exception as e:
            logger.error(f"Erro ao comparar as imagens: {e}")
            await update.message.reply_text(
                "❌ Ocorreu um erro durante a comparação das imagens.\n\n"
                "Isso pode acontecer devido a:\n"
                "- Baixa qualidade das imagens\n"
                "- Ângulos muito diferentes dos rostos\n"
                "- Iluminação inadequada\n\n"
                "Por favor, tente novamente com outras fotos usando o comando /reconhecimento."
            )
        
        # Remove os arquivos temporários
        if 'primeira_foto' in context.user_data and os.path.exists(context.user_data['primeira_foto']):
            os.remove(context.user_data['primeira_foto'])
        if os.path.exists(segunda_foto):
            os.remove(segunda_foto)
        
        # Limpa os dados do usuário
        context.user_data.clear()
        
        # Finaliza a conversa
        return ConversationHandler.END
    
    except Exception as e:
        logger.error(f"Erro ao processar a segunda foto: {e}")
        await update.message.reply_text(
            "Ocorreu um erro ao processar a imagem.\n\n"
            "Por favor, envie outra foto com melhor qualidade e iluminação."
        )
        # Remove o arquivo temporário
        if os.path.exists(segunda_foto):
            os.remove(segunda_foto)
        return ESPERANDO_SEGUNDA_FOTO

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a operação atual e limpa os dados."""
    user = update.message.from_user
    logger.info(f"Usuário {user.first_name} cancelou a operação")
    
    # Remove os arquivos temporários se existirem
    if 'primeira_foto' in context.user_data and os.path.exists(context.user_data['primeira_foto']):
        os.remove(context.user_data['primeira_foto'])
    
    # Limpa os dados do usuário
    context.user_data.clear()
    
    await update.message.reply_text(
        "Processo de comparação cancelado.\n\n"
        "Para iniciar uma nova comparação, envie o comando /reconhecimento."
    )
    
    return ConversationHandler.END

async def formato_invalido(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde quando um formato inválido é enviado."""
    await update.message.reply_text(
        "Por favor, envie apenas arquivos de imagem (jpg, jpeg, png).\n\n"
        "Para continuar, envie uma foto válida."
    )

def main() -> None:
    """Função principal para iniciar o bot."""
    # Cria a aplicação
    application = Application.builder().token(TOKEN).build()
    
    # Adiciona handlers para comandos básicos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ajuda", ajuda))
    
    # Adiciona o conversation handler para o processo de reconhecimento
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("reconhecimento", reconhecimento)],
        states={
            ESPERANDO_PRIMEIRA_FOTO: [
                MessageHandler(filters.PHOTO, receber_primeira_foto),
                MessageHandler(~filters.PHOTO, formato_invalido)
            ],
            ESPERANDO_SEGUNDA_FOTO: [
                MessageHandler(filters.PHOTO, receber_segunda_foto),
                MessageHandler(~filters.PHOTO, formato_invalido)
            ],
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar),
        ],
        conversation_timeout=300,  # 5 minutos de timeout
    )
    
    application.add_handler(conv_handler)
    
    # Inicia o bot
    application.run_polling()

if __name__ == '__main__':
    main()
