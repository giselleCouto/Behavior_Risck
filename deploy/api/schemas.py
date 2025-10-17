"""
Schemas Pydantic para validação de dados da API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class PredictionRequest(BaseModel):
    """Schema para requisição de predição"""
    
    cpf_cnpj: str = Field(..., description="CPF/CNPJ do cliente")
    idade: int = Field(..., ge=18, le=120, description="Idade do cliente")
    renda_valida_new: float = Field(..., ge=0, description="Renda válida do cliente")
    tempo_relacionamento_kredilig_meses: int = Field(..., ge=0, description="Tempo de relacionamento em meses")
    
    # Informações de contratos
    qtd_contratos: int = Field(default=0, ge=0, description="Quantidade total de contratos")
    qtd_contratos_nr: int = Field(default=0, ge=0, description="Quantidade de contratos não renegociados")
    qtd_contratos_regular: int = Field(default=0, ge=0, description="Quantidade de contratos regulares")
    qtd_contratos_atraso: int = Field(default=0, ge=0, description="Quantidade de contratos em atraso")
    
    # Informações de atraso
    dias_maior_atraso: int = Field(default=0, ge=0, description="Dias do maior atraso geral")
    dias_maior_atraso_aberto: int = Field(default=0, ge=0, description="Dias do maior atraso em aberto")
    media_atraso_dias: float = Field(default=0.0, ge=0, description="Média de dias de atraso")
    
    # Informações financeiras
    valor_pago_nr: float = Field(default=0.0, ge=0, description="Valor pago em contratos não renegociados")
    valor_principal_total_nr: float = Field(default=0.0, ge=0, description="Valor principal total não renegociado")
    principal_total: float = Field(default=0.0, ge=0, description="Principal total")
    limite_total: float = Field(default=0.0, ge=0, description="Limite total atual")
    
    # Informações de parcelas
    qtd_parcelas_pagas: int = Field(default=0, ge=0, description="Quantidade de parcelas pagas")
    qtd_parcelas_pagas_nr: int = Field(default=0, ge=0, description="Quantidade de parcelas pagas não renegociadas")
    qtd_parcelas_aberta: int = Field(default=0, ge=0, description="Quantidade de parcelas em aberto")
    
    # Indicadores
    indice_instabilidade: float = Field(default=0.0, ge=0, description="Índice de instabilidade")
    indice_regularidade: float = Field(default=0.0, ge=0, le=1, description="Índice de regularidade")
    reneg_vs_liq_ratio_ponderado: float = Field(default=0.0, ge=0, description="Ratio ponderado reneg vs liquidação")
    freq_atraso: float = Field(default=0.0, ge=0, description="Frequência de atraso")
    
    # Informações categóricas
    ocupacao: Optional[str] = Field(default=None, description="Ocupação do cliente")
    canal_origem: Optional[str] = Field(default=None, description="Canal de origem")
    produtos: Optional[str] = Field(default=None, description="Produtos contratados")
    possui_contratos_a_vista: Optional[str] = Field(default="NAO", description="Possui contratos à vista")
    
    class Config:
        schema_extra = {
            "example": {
                "cpf_cnpj": "12345678900",
                "idade": 35,
                "renda_valida_new": 3000.0,
                "tempo_relacionamento_kredilig_meses": 24,
                "qtd_contratos": 5,
                "qtd_contratos_nr": 4,
                "dias_maior_atraso": 15,
                "dias_maior_atraso_aberto": 0,
                "valor_pago_nr": 5000.0,
                "valor_principal_total_nr": 8000.0,
                "indice_instabilidade": 12.5,
                "indice_regularidade": 0.85,
                "reneg_vs_liq_ratio_ponderado": 0.2,
                "ocupacao": "EMPREGADO_PRIVADO",
                "canal_origem": "Fisico",
                "produtos": "EMPRESTIMO"
            }
        }

class PredictionResponse(BaseModel):
    """Schema para resposta de predição"""
    
    cpf_cnpj: str = Field(..., description="CPF/CNPJ do cliente")
    score: int = Field(..., ge=0, le=1000, description="Score de crédito (0-1000)")
    pd: float = Field(..., ge=0, le=1, description="Probability of Default")
    faixa_risco: str = Field(..., description="Faixa de risco")
    limite_sugerido: float = Field(..., ge=0, description="Limite de crédito sugerido")
    decisao: str = Field(..., description="Decisão de crédito")
    motivo: str = Field(..., description="Motivo da decisão")
    timestamp: str = Field(..., description="Timestamp da predição")
    
    class Config:
        schema_extra = {
            "example": {
                "cpf_cnpj": "12345678900",
                "score": 750,
                "pd": 0.12,
                "faixa_risco": "MEDIO",
                "limite_sugerido": 15000.0,
                "decisao": "APROVAR",
                "motivo": "Cliente com risco MEDIO dentro dos parâmetros",
                "timestamp": "2025-10-17T10:30:00"
            }
        }

class BatchPredictionRequest(BaseModel):
    """Schema para requisição de predição em lote"""
    
    clients: List[PredictionRequest] = Field(..., description="Lista de clientes para predição")
    
    @validator('clients')
    def validate_batch_size(cls, v):
        if len(v) > 1000:
            raise ValueError("Máximo de 1000 clientes por lote")
        if len(v) == 0:
            raise ValueError("Lista de clientes não pode estar vazia")
        return v

class HealthResponse(BaseModel):
    """Schema para resposta de health check"""
    
    status: str = Field(..., description="Status da aplicação")
    timestamp: datetime = Field(..., description="Timestamp do health check")
    model_loaded: bool = Field(..., description="Modelo está carregado")
    models_info: dict = Field(..., description="Informações dos modelos")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-17T10:30:00",
                "model_loaded": True,
                "models_info": {
                    "preprocessors_loaded": True,
                    "models_loaded": True,
                    "bins_loaded": True,
                    "all_loaded": True
                }
            }
        }

