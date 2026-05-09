import re
import logging
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

logger = logging.getLogger(__name__)

MODEL_NAME = "cointegrated/rut5-base-absum"


MAX_INPUT_TOKENS = 450   
MAX_OUTPUT_TOKENS = 150  

logger.info(f"Инициализация модели: {MODEL_NAME}...")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    model.eval() 
    logger.info("Модель успешно загружена в память")
except Exception as e:
    logger.error(f"Ошибка загрузки модели: {e}")
    raise

def _split_into_chunks(text: str, chunk_size_tokens: int = MAX_INPUT_TOKENS) -> list:
    """Разбивает текст на чанки, сохраняя границы предложений."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for sent in sentences:
        sent_tokens = len(tokenizer.encode(sent, add_special_tokens=False))
        if current_tokens + sent_tokens <= chunk_size_tokens:
            current_chunk.append(sent)
            current_tokens += sent_tokens
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [sent]
            current_tokens = sent_tokens
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def _summarize_chunk(text: str) -> str:
    """Генерирует саммари для одного чанка с защитой от повторов."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=MAX_OUTPUT_TOKENS,
            min_length=25,
            num_beams=2,
            early_stopping=True,
            length_penalty=1.3,
            repetition_penalty=1.3,          
            no_repeat_ngram_size=2,          
            do_sample=False
        )
    
    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return re.sub(r'<.*?>', '', summary).strip()

def _remove_consecutive_duplicates(text: str) -> str:
    """Убирает подряд идущие одинаковые предложения (эхо)."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    unique = []
    for s in sentences:
        s_clean = s.strip()
        if not s_clean: continue
        if not unique or s_clean.rstrip('.!?').lower() != unique[-1].rstrip('.!?').lower():
            unique.append(s_clean)
    return " ".join(unique)

def summarize(text: str) -> str:
 
    logger.info(f"[MODEL] === НАЧАЛО ОБРАБОТКИ ===")
    logger.info(f"[MODEL] Входной текст: {len(text)} символов, {len(tokenizer.encode(text))} токенов")
    
    if not text or not text.strip():
        return "Текст пустой или не удалось извлечь контент."
    
    if len(tokenizer.encode(text)) <= MAX_INPUT_TOKENS:
        logger.info(f"[MODEL] Текст помещается в один чанк. Генерирую...")
        result = _summarize_chunk(text)
        logger.info(f"[MODEL] Результат: {len(result)} символов")
        return result
    
    chunks = _split_into_chunks(text, chunk_size_tokens=MAX_INPUT_TOKENS)
    logger.info(f"[MODEL] Текст длинный. Создано чанков: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        logger.info(f"[MODEL] Чанк {i+1}: {len(chunk)} символов, {len(tokenizer.encode(chunk))} токенов")
    
    partial_summaries = []
    
    for i, chunk in enumerate(chunks):
        logger.info(f"[MODEL] Обработка чанка {i+1}/{len(chunks)}...")
        summary = _summarize_chunk(chunk)
        logger.info(f"[MODEL] Чанк {i+1} → {len(summary)} символов")
        if summary:
            partial_summaries.append(summary)
    
    raw_result = " ".join(partial_summaries)
    logger.info(f"[MODEL] После склейки: {len(raw_result)} символов")
    
    final_result = _remove_consecutive_duplicates(raw_result)
    logger.info(f"[MODEL] После дедупликации: {len(final_result)} символов")
    logger.info(f"[MODEL] === КОНЕЦ ОБРАБОТКИ ===")
    
    return final_result if final_result else "Не удалось сгенерировать саммари."