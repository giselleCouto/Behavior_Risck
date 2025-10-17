"""
Serviço para carregar e executar o modelo Behavior Score
"""
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
import logging
from typing import Dict, Any, List
import os

logger = logging.getLogger(__name__)

class BehaviorScoreModel:
    """Classe para gerenciar o modelo Behavior Score"""
    
    def __init__(self, model_path: str = "/app/Modelos"):
        """
        Inicializa o serviço do modelo
        
        Args:
            model_path: Caminho para a pasta com os modelos
        """
        self.model_path = Path(model_path)
        self.preprocessors = {}
        self.models = {}
        self.bins = {}
        self.policies = None
        self.limits_table = None
        
    def load_models(self):
        """Carrega todos os modelos e artefatos necessários"""
        try:
            logger.info("Carregando pré-processadores...")
            
            # Carrega imputers
            preproc_path = self.model_path / "Pré-Processamento"
            self.preprocessors['imputer_cat'] = self._load_pickle(preproc_path / "imputer_cat.pkl")
            self.preprocessors['imputer_num'] = self._load_pickle(preproc_path / "imputer_num.pkl")
            self.preprocessors['imputer_num_median'] = self._load_pickle(preproc_path / "imputer_num_median.pkl")
            self.preprocessors['imputer_parametros'] = self._load_pickle(preproc_path / "imputer_parametros.pkl")
            self.preprocessors['scaler_num'] = self._load_pickle(preproc_path / "scaler_num.pkl")
            
            logger.info("Carregando modelos de ML...")
            
            # Carrega modelo de clusterização
            self.models['kmeans'] = self._load_pickle(self.model_path / "kmeans.pkl")
            
            # Carrega modelo de floresta aleatória (versão mais recente)
            # Tenta carregar fa_12.pkl, se não existir tenta fa_11.pkl, etc
            for version in [12, 11, 8]:
                model_file = self.model_path / f"fa_{version}.pkl"
                if model_file.exists():
                    self.models['random_forest'] = self._load_pickle(model_file)
                    logger.info(f"Modelo de Floresta Aleatória carregado: fa_{version}.pkl")
                    break
            
            if 'random_forest' not in self.models:
                raise FileNotFoundError("Nenhum modelo de Floresta Aleatória encontrado")
            
            logger.info("Carregando bins e tabelas...")
            
            # Carrega bins
            self.bins['SCR'] = np.load(self.model_path / "bins_SCR.npy", allow_pickle=True)
            self.bins['PD'] = np.load(self.model_path / "bins_PD.npy", allow_pickle=True)
            self.bins['risco'] = np.load(self.model_path / "bins_risco.npy", allow_pickle=True)
            
            # Carrega tabela de limites
            self.limits_table = pd.read_csv(self.model_path / "resultados_limites.csv")
            
            # Carrega políticas (se existir)
            policies_file = self.model_path.parent / "POLÍTICAS_BEHAVIOR.xlsx"
            if policies_file.exists():
                self.policies = pd.read_excel(policies_file)
            
            logger.info("Todos os modelos e artefatos carregados com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelos: {str(e)}")
            raise
    
    def _load_pickle(self, file_path: Path):
        """Carrega arquivo pickle"""
        try:
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar {file_path}: {str(e)}")
            raise
    
    def check_health(self) -> Dict[str, Any]:
        """Verifica se todos os modelos estão carregados"""
        return {
            "preprocessors_loaded": len(self.preprocessors) > 0,
            "models_loaded": len(self.models) > 0,
            "bins_loaded": len(self.bins) > 0,
            "limits_table_loaded": self.limits_table is not None,
            "all_loaded": (
                len(self.preprocessors) > 0 and 
                len(self.models) > 0 and 
                len(self.bins) > 0 and 
                self.limits_table is not None
            )
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre os modelos carregados"""
        return {
            "model_type": "Random Forest Classifier",
            "preprocessing": {
                "categorical_imputer": self.preprocessors.get('imputer_cat') is not None,
                "numerical_imputer": self.preprocessors.get('imputer_num') is not None,
                "scaler": self.preprocessors.get('scaler_num') is not None,
            },
            "clustering": {
                "algorithm": "KMeans",
                "loaded": self.models.get('kmeans') is not None
            },
            "bins": list(self.bins.keys()),
            "limits_table_size": len(self.limits_table) if self.limits_table is not None else 0
        }
    
    def get_expected_features(self) -> Dict[str, List[str]]:
        """Retorna as features esperadas pelo modelo"""
        # Lista de features principais do modelo
        # Estas devem ser ajustadas conforme o modelo real
        return {
            "required_features": [
                "cpf_cnpj",
                "idade",
                "renda_valida_new",
                "tempo_relacionamento_kredilig_meses",
                "qtd_contratos",
                "qtd_contratos_nr",
                "dias_maior_atraso",
                "dias_maior_atraso_aberto",
                "valor_pago_nr",
                "valor_principal_total_nr",
                "qtd_parcelas_pagas_nr",
                "indice_instabilidade",
                "reneg_vs_liq_ratio_ponderado"
            ],
            "optional_features": [
                "ocupacao",
                "canal_origem",
                "produtos",
                "possui_contratos_a_vista"
            ]
        }
    
    def preprocess(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Pré-processa os dados de entrada
        
        Args:
            data: Dicionário com os dados do cliente
            
        Returns:
            DataFrame pré-processado
        """
        # Converte para DataFrame
        df = pd.DataFrame([data])
        
        # Aqui você deve implementar todo o pré-processamento
        # que é feito no notebook refatoracao_modelagem.ipynb
        
        # Exemplo simplificado:
        # 1. Imputação de categóricas
        # 2. Imputação de numéricas
        # 3. Clusterização
        # 4. Escalonamento
        
        # TODO: Implementar pré-processamento completo
        
        return df
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza predição para um cliente
        
        Args:
            data: Dicionário com os dados do cliente
            
        Returns:
            Dicionário com score, PD, faixa de risco e limite
        """
        try:
            # Pré-processa os dados
            df_processed = self.preprocess(data)
            
            # Realiza predição com o modelo
            rf_model = self.models['random_forest']
            
            # Predição de probabilidade
            proba = rf_model.predict_proba(df_processed)[0]
            prob_inadimplente = proba[1]  # Probabilidade da classe 1 (inadimplente)
            
            # Calcula PD (Probability of Default)
            pd_value = prob_inadimplente
            
            # Calcula Score (inversamente proporcional ao risco)
            # Score vai de 0 a 1000, onde maior é melhor
            score = int((1 - pd_value) * 1000)
            
            # Determina faixa de risco usando bins
            faixa_risco = self._get_risk_band(pd_value)
            
            # Calcula limite sugerido
            limite_sugerido = self._calculate_limit(pd_value, data)
            
            # Aplica políticas de crédito
            decision = self._apply_policies(pd_value, faixa_risco, data)
            
            return {
                "cpf_cnpj": data.get("cpf_cnpj"),
                "score": score,
                "pd": round(pd_value, 4),
                "faixa_risco": faixa_risco,
                "limite_sugerido": limite_sugerido,
                "decisao": decision["action"],
                "motivo": decision["reason"],
                "timestamp": pd.Timestamp.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro na predição: {str(e)}")
            raise
    
    def _get_risk_band(self, pd_value: float) -> str:
        """Determina a faixa de risco baseado na PD"""
        bins = self.bins['risco']
        
        # Define faixas de risco
        if pd_value <= 0.05:
            return "MUITO BAIXO"
        elif pd_value <= 0.10:
            return "BAIXO"
        elif pd_value <= 0.20:
            return "MEDIO"
        elif pd_value <= 0.35:
            return "ALTO"
        else:
            return "MUITO ALTO"
    
    def _calculate_limit(self, pd_value: float, data: Dict[str, Any]) -> float:
        """Calcula o limite sugerido baseado na PD e outras variáveis"""
        try:
            # Usa a tabela de limites isotônicos
            # Encontra o limite correspondente à PD
            if self.limits_table is not None:
                # Busca na tabela de limites
                closest_idx = (self.limits_table['PD'] - pd_value).abs().idxmin()
                limite = self.limits_table.loc[closest_idx, 'limite']
                return float(limite)
            else:
                # Cálculo simples se não houver tabela
                # Quanto maior a PD, menor o limite
                base_limit = 20000  # Limite base
                limit = base_limit * (1 - pd_value)
                return round(limit, 2)
                
        except Exception as e:
            logger.error(f"Erro ao calcular limite: {str(e)}")
            return 0.0
    
    def _apply_policies(self, pd_value: float, faixa_risco: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Aplica as políticas de crédito"""
        
        # Verifica se cliente tem muitos dias de atraso
        dias_atraso_aberto = data.get('dias_maior_atraso_aberto', 0)
        
        if dias_atraso_aberto > 90:
            return {
                "action": "NEGAR",
                "reason": "Cliente com atraso superior a 90 dias"
            }
        
        # Verifica faixa de risco
        if faixa_risco in ["MUITO ALTO", "ALTO"]:
            if pd_value > 0.35:
                return {
                    "action": "NEGAR",
                    "reason": f"Risco {faixa_risco} - PD acima do limite"
                }
            else:
                return {
                    "action": "APROVAR_COM_RESTRICAO",
                    "reason": f"Risco {faixa_risco} - Limite reduzido"
                }
        
        # Aprova nos demais casos
        return {
            "action": "APROVAR",
            "reason": f"Cliente com risco {faixa_risco} dentro dos parâmetros"
        }

