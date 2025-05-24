#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para configuração do bot de reconhecimento facial no Render.com
Este script configura o bot para ser executado em ambiente de produção no Render
"""

import os
import sys
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from deepface import DeepFace
import cv2
import numpy as np
import tempfile

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
        # Carrega a imagem
        img = cv2.imread(primeira_foto)
        
        # Detecta rostos na imagem usando DeepFace
        faces = DeepFace.extract_faces(img_path=primeira_foto, enforce_detection=False)
        
        if len(faces) == 0:
            await update.message.reply_text(
                "Não foi possível detectar um rosto na imagem enviada.\n\n"
                "Por favor, envie outra foto onde o rosto esteja claramente visível."
            )
            # Remove o arquivo temporário
            os.remove(primeira_foto)
            return ESPERANDO_PRIMEIRA_FOTO
        
        if len(faces) > 1:
            await update.message.reply_text(
                "Detectei múltiplos rostos na imagem. Para uma comparação mais precisa, "
                "envie uma foto contendo apenas um rosto.\n\n"
                "Por favor, envie outra imagem."
            )
            # Remove o arquivo temporário
            os.remove(primeira_foto)
            return ESPERANDO_PRIMEIRA_FOTO
        
        # Salva o caminho da primeira foto no contexto
        context.user_data['primeira_foto'] = primeira_foto
        
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
        # Carrega a imagem
        img = cv2.imread(segunda_foto)
        
        # Detecta rostos na imagem usando DeepFace
        faces = DeepFace.extract_faces(img_path=segunda_foto, enforce_detection=False)
        
        if len(faces) == 0:
            await update.message.reply_text(
                "Não foi possível detectar um rosto na imagem enviada.\n\n"
                "Por favor, envie outra foto onde o rosto esteja claramente visível."
            )
            # Remove o arquivo temporário
            os.remove(segunda_foto)
            return ESPERANDO_SEGUNDA_FOTO
        
        if len(faces) > 1:
            await update.message.reply_text(
                "Detectei múltiplos rostos na imagem. Para uma comparação mais precisa, "
                "envie uma foto contendo apenas um rosto.\n\n"
                "Por favor, envie outra imagem."
            )
            # Remove o arquivo temporário
            os.remove(segunda_foto)
            return ESPERANDO_SEGUNDA_FOTO
        
        # Salva o caminho da segunda foto no contexto
        context.user_data['segunda_foto'] = segunda_foto
        
        # Informa ao usuário que a comparação está sendo processada
        await update.message.reply_text(
            "Segunda foto recebida com sucesso!\n\n"
            "Processando a comparação facial... Por favor, aguarde alguns instantes."
        )
        
        # Realiza a comparação facial
        primeira_foto = context.user_data['primeira_foto']
        
        # Compara as duas imagens usando DeepFace
        try:
            resultado = DeepFace.verify(
                img1_path=primeira_foto,
                img2_path=segunda_foto,
                enforce_detection=False,
                model_name="VGG-Face"  # Modelo mais preciso para comparação
            )
            
            # Extrai os resultados
            verificado = resultado["verified"]
            distancia = resultado["distance"]
            
            # Calcula a similaridade em porcentagem (quanto menor a distância, maior a similaridade)
            # A distância é um valor entre 0 e 1, onde 0 significa rostos idênticos
            similaridade = max(0, min(100, (1 - distancia) * 100))
            
            # Determina o nível de confiabilidade com base na distância
            if distancia < 0.4:
                confiabilidade = "Alta"
            elif distancia < 0.6:
                confiabilidade = "Média"
            else:
                confiabilidade = "Baixa"
            
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
        if os.path.exists(primeira_foto):
            os.remove(primeira_foto)
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
    if 'segunda_foto' in context.user_data and os.path.exists(context.user_data['segunda_foto']):
        os.remove(context.user_data['segunda_foto'])
    
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
