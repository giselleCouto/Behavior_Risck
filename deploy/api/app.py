"""
API FastAPI para servir o modelo Behavior Score KAB em produção
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import List, Dict, Any
from datetime import datetime

from model_service import BehaviorScoreModel
from schemas import PredictionRequest, PredictionResponse, HealthResponse, BatchPredictionRequest

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicialização da aplicação
app = FastAPI(
    title="Behavior Score KAB API",
    description="API para predição de risco de crédito usando o modelo Behavior Score",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialização do modelo
model_service = None

@app.on_event("startup")
async def startup_event():
    """Carrega o modelo na inicialização"""
    global model_service
    try:
        logger.info("Carregando modelo Behavior Score...")
        model_service = BehaviorScoreModel()
        model_service.load_models()
        logger.info("Modelo carregado com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao carregar modelo: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Limpeza na finalização"""
    logger.info("Finalizando aplicação...")

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz"""
    return {
        "message": "Behavior Score KAB API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Endpoint de health check"""
    try:
        if model_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Modelo não está carregado"
            )
        
        model_health = model_service.check_health()
        
        return HealthResponse(
            status="healthy" if model_health["all_loaded"] else "unhealthy",
            timestamp=datetime.now(),
            model_loaded=model_health["all_loaded"],
            models_info=model_health
        )
    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/predict", response_model=PredictionResponse, tags=["Predictions"])
async def predict(request: PredictionRequest):
    """
    Realiza predição para um único cliente
    
    Args:
        request: Dados do cliente para predição
        
    Returns:
        Predição de risco com score, PD, faixa de risco e limite sugerido
    """
    try:
        if model_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Modelo não está disponível"
            )
        
        logger.info(f"Processando predição para cliente: {request.cpf_cnpj}")
        
        # Converte request para dict
        input_data = request.dict()
        
        # Realiza predição
        prediction = model_service.predict(input_data)
        
        logger.info(f"Predição concluída - Score: {prediction['score']}, Faixa: {prediction['faixa_risco']}")
        
        return PredictionResponse(**prediction)
        
    except ValueError as e:
        logger.error(f"Erro de validação: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro na predição: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar predição: {str(e)}"
        )

@app.post("/predict/batch", tags=["Predictions"])
async def predict_batch(request: BatchPredictionRequest):
    """
    Realiza predições em lote para múltiplos clientes
    
    Args:
        request: Lista de dados de clientes para predição
        
    Returns:
        Lista de predições
    """
    try:
        if model_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Modelo não está disponível"
            )
        
        logger.info(f"Processando predição em lote para {len(request.clients)} clientes")
        
        results = []
        errors = []
        
        for idx, client in enumerate(request.clients):
            try:
                input_data = client.dict()
                prediction = model_service.predict(input_data)
                results.append(prediction)
            except Exception as e:
                logger.error(f"Erro na predição do cliente {idx}: {str(e)}")
                errors.append({
                    "index": idx,
                    "cpf_cnpj": client.cpf_cnpj,
                    "error": str(e)
                })
        
        logger.info(f"Predição em lote concluída - Sucessos: {len(results)}, Erros: {len(errors)}")
        
        return {
            "total": len(request.clients),
            "successful": len(results),
            "failed": len(errors),
            "predictions": results,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Erro na predição em lote: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar predição em lote: {str(e)}"
        )

@app.get("/model/info", tags=["Model"])
async def model_info():
    """Retorna informações sobre o modelo"""
    try:
        if model_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Modelo não está disponível"
            )
        
        return model_service.get_model_info()
        
    except Exception as e:
        logger.error(f"Erro ao obter informações do modelo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/model/features", tags=["Model"])
async def model_features():
    """Retorna as features esperadas pelo modelo"""
    try:
        if model_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Modelo não está disponível"
            )
        
        return model_service.get_expected_features()
        
    except Exception as e:
        logger.error(f"Erro ao obter features do modelo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

