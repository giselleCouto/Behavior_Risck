"""Serviço para carregar e executar o modelo Behavior Score."""

from __future__ import annotations

import logging
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

try:  # shap é opcional para ambientes onde não será utilizado
    import shap  # type: ignore

    _SHAP_AVAILABLE = True
except ImportError:  # pragma: no cover - import opcional
    shap = None  # type: ignore
    _SHAP_AVAILABLE = False

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
        self.preprocessors: Dict[str, Any] = {}
        self.models = {}
        self.bins = {}
        self.policies = None
        self.limits_table = None

    # ------------------------------------------------------------------
    # Carregamento de artefatos
    # ------------------------------------------------------------------
        
    def load_models(self):
        """Carrega todos os modelos e artefatos necessários"""
        try:
            logger.info("Carregando pré-processadores...")
            
            # Carrega imputers
            preproc_path = self.model_path / "Pré-Processamento"
            self.preprocessors['imputer_cat'] = self._load_joblib(preproc_path / "imputer_cat.pkl")
            self.preprocessors['imputer_num'] = self._load_joblib(preproc_path / "imputer_num.pkl")
            self.preprocessors['imputer_num_median'] = self._load_joblib(preproc_path / "imputer_num_median.pkl")
            self.preprocessors['imputer_parametros'] = self._load_joblib(preproc_path / "imputer_parametros.pkl")
            self.preprocessors['scaler_num'] = self._load_joblib(preproc_path / "scaler_num.pkl")
            
            logger.info("Carregando modelos de ML...")
            
            # Carrega modelo de clusterização
            self.models['kmeans'] = self._load_joblib(self.model_path / "kmeans.pkl")
            
            # Carrega modelo de floresta aleatória (versão mais recente)
            # Tenta carregar fa_12.pkl, se não existir tenta fa_11.pkl, etc
            for version in [12, 11, 8]:
                model_file = self.model_path / f"fa_{version}.pkl"
                if model_file.exists():
                    self.models['random_forest'] = self._load_joblib(model_file)
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
    
    def _load_joblib(self, file_path: Path):
        """Carrega arquivos persistidos com pickle/joblib."""

        try:
            return joblib.load(file_path)
        except Exception as exc:  # pragma: no cover - logging
            logger.error("Erro ao carregar artefato %s: %s", file_path, exc)
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
    
    # ------------------------------------------------------------------
    # Pré-processamento
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_text(value: Any) -> str:
        if pd.isna(value):
            return ""

        text = str(value).strip().upper()
        normalized = unicodedata.normalize("NFKD", text)
        cleaned = "".join(c for c in normalized if not unicodedata.combining(c))
        cleaned = cleaned.replace("-", "_")
        cleaned = "_".join(part for part in cleaned.split())
        return cleaned

    @staticmethod
    def _map_estado_civil(value: str) -> str:
        value = BehaviorScoreModel._normalize_text(value)
        normalized = value.replace(" ", "_")
        mapping = {
            "CASADA": "CASADO",
            "CASADO(A)": "CASADO",
            "DIVORCIADA": "DIVORCIADO",
            "DIVORCIADO(A)": "DIVORCIADO",
            "UNIAO_ESTAVEL": "UNIAO ESTAVEL",
            "UNIAOESTAVEL": "UNIAO ESTAVEL",
            "VIUVA": "VIUVO",
            "VIUVO(A)": "VIUVO",
        }

        return mapping.get(normalized, value)

    @staticmethod
    def _map_ocupacao(value: str) -> str:
        value = BehaviorScoreModel._normalize_text(value)

        if not value:
            return "OUTROS"

        if "APOSENT" in value:
            return "APOSENTADO"
        if "SERVIDOR" in value or "PUBLIC" in value:
            return "SERVIDOR_PUBLICO"
        if "PENSA" in value or "PENSION" in value:
            return "RENDA_PASSIVA_PENSAO"
        if "AUTON" in value or "EMPREG" in value:
            return "EMPREGADO_PRIVADO_AUTONOMO"

        return "OUTROS"

    @staticmethod
    def _map_regiao(value: str) -> str:
        value = BehaviorScoreModel._normalize_text(value)
        replacements = {
            "FORA SC": "FORA_SC",
            "FORA_SC": "FORA_SC",
            "GRANDE FLORIANOPOLIS": "GRANDE_FLORIANOPOLIS",
            "NORTE CATARINENSE": "NORTE_CATARINENSE",
            "OESTE CATARINENSE": "OESTE_CATARINENSE",
            "SERRA CATARINENSE": "SERRANA",
            "SERRA": "SERRANA",
            "SUL CATARINENSE": "SUL_CATARINENSE",
            "VALE DO ITAJAI": "VALE_DO_ITAJAI",
        }
        return replacements.get(value, value)

    @staticmethod
    def _map_tipo_entrada(value: str) -> str:
        value = BehaviorScoreModel._normalize_text(value)
        if value in {"PAGA ENTRADA", "PAGA_ENTRADA", "PAGA-ENTRADA"}:
            return "PAGA_ENTRADA"
        return value

    @staticmethod
    def _fx_renda_valida(value: float) -> str:
        bins = [0, 1518, 1518 * 1.25, 1518 * 1.5, 1518 * 2, 1518 * 3, float("inf")]
        labels = [
            "Até 1 SM",
            "De 1 SM a 1,25 SM",
            "De 1,25 SM a 1,5 SM",
            "De 1,5 SM a 2 SM",
            "De 2 SM a 3 SM",
            "Acima de 3 SM",
        ]

        if pd.isna(value):
            return ""

        idx = np.digitize([value], bins)[0] - 1
        idx = max(0, min(idx, len(labels) - 1))
        return labels[idx]

    @staticmethod
    def _ensure_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
        for column in columns:
            if column not in df.columns:
                df[column] = np.nan

    def _required_columns(self) -> List[str]:
        return [
            "cpf_cnpj",
            "idade",
            "tempo_relacionamento_kredilig_meses",
            "media_meses_entre_contratos_combinado",
            "valor_pago_nr",
            "valor_principal_total_nr",
            "qtd_contratos_nr",
            "qtd_parcelas_pagas_nr",
            "sexo",
            "estado_civil",
            "nacionalidade",
            "canal_origem",
            "produtos",
            "ocupacao",
            "grau_escolaridade_cat",
            "regiao",
            "tipo_valor_entrada",
            "possui_contratos_a_vista",
            "renda_valida_new",
            "dias_maior_atraso_aberto",
        ]

    def _scaler_stats(self) -> Dict[str, Tuple[float, float]]:
        scaler = self.preprocessors.get('scaler_num')
        if scaler is None:
            return {}

        return {
            feature: (mean, scale if scale != 0 else 1.0)
            for feature, mean, scale in zip(
                scaler.feature_names_in_, scaler.mean_, scaler.scale_
            )
        }

    def preprocess_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Pré-processa um DataFrame completo.

        Retorna uma tupla contendo o DataFrame original tratado e o DataFrame
        com as features alinhadas ao modelo.
        """

        if not self.preprocessors:
            raise ValueError("Modelos de pré-processamento não foram carregados")

        df_work = df.copy()
        self._ensure_columns(df_work, self._required_columns())

        # Conversões numéricas
        numeric_columns = [
            "idade",
            "tempo_relacionamento_kredilig_meses",
            "media_meses_entre_contratos_combinado",
            "valor_pago_nr",
            "valor_principal_total_nr",
            "qtd_contratos_nr",
            "qtd_parcelas_pagas_nr",
            "renda_valida_new",
            "dias_maior_atraso_aberto",
        ]
        for column in numeric_columns:
            df_work[column] = pd.to_numeric(df_work[column], errors='coerce')

        # Imputação categórica
        imputer_cat = self.preprocessors['imputer_cat']
        cat_cols = list(imputer_cat.feature_names_in_)
        df_work[cat_cols] = imputer_cat.transform(df_work[cat_cols])

        # Imputação numérica (média)
        imputer_num = self.preprocessors['imputer_num']
        num_cols = list(imputer_num.feature_names_in_)
        self._ensure_columns(df_work, num_cols)
        df_work[num_cols] = imputer_num.transform(df_work[num_cols])

        # Imputação mediana
        imputer_median = self.preprocessors['imputer_num_median']
        median_cols = list(imputer_median.feature_names_in_)
        self._ensure_columns(df_work, median_cols)
        df_work[median_cols] = imputer_median.transform(df_work[median_cols])

        # Normalização de strings
        df_work['estado_civil'] = df_work['estado_civil'].map(self._map_estado_civil)
        df_work['ocupacao'] = df_work['ocupacao'].map(self._map_ocupacao)
        df_work['regiao'] = df_work['regiao'].map(self._map_regiao)
        df_work['tipo_valor_entrada'] = df_work['tipo_valor_entrada'].map(self._map_tipo_entrada)
        df_work['sexo'] = df_work['sexo'].map(self._normalize_text)
        df_work['nacionalidade'] = df_work['nacionalidade'].map(self._normalize_text)
        df_work['possui_contratos_a_vista'] = df_work['possui_contratos_a_vista'].map(self._normalize_text)
        df_work['canal_origem'] = df_work['canal_origem'].map(self._normalize_text)
        df_work['produtos'] = df_work['produtos'].map(self._normalize_text)

        # Faixa de renda
        df_work['fx_renda_valida'] = df_work['renda_valida_new'].apply(self._fx_renda_valida)

        # Construção do DataFrame de features alinhado ao modelo
        rf_model = self.models['random_forest']
        feature_names = list(rf_model.feature_names_in_)
        features = pd.DataFrame(0.0, index=df_work.index, columns=feature_names)

        scaler_stats = self._scaler_stats()
        numeric_features = [
            "idade",
            "tempo_relacionamento_kredilig_meses",
            "media_meses_entre_contratos_combinado",
            "valor_pago_nr",
            "valor_principal_total_nr",
            "qtd_contratos_nr",
            "qtd_parcelas_pagas_nr",
        ]
        for column in numeric_features:
            mean, scale = scaler_stats.get(column, (0.0, 1.0))
            features[column] = (df_work[column].fillna(mean) - mean) / scale

        # Variáveis categóricas binárias
        features['sexo_M'] = (df_work['sexo'] == 'M').astype(float)

        for option in ['CASADO', 'DIVORCIADO', 'SOLTEIRO', 'UNIAO ESTAVEL', 'VIUVO']:
            column_name = f'estado_civil_{option}'
            if column_name in features.columns:
                features[column_name] = (df_work['estado_civil'] == option).astype(float)

        if 'nacionalidade_ESTRANGEIRO' in features.columns:
            features['nacionalidade_ESTRANGEIRO'] = (
                df_work['nacionalidade'] == 'ESTRANGEIRO'
            ).astype(float)

        if 'canal_origem_Fisico' in features.columns:
            features['canal_origem_Fisico'] = (
                df_work['canal_origem'] == 'FISICO'
            ).astype(float)

        # Produtos
        produtos_series = df_work['produtos'].fillna('')
        if 'produtos_EMPRESTIMO' in features.columns:
            features['produtos_EMPRESTIMO'] = produtos_series.str.contains('EMPRESTIMO', regex=False).astype(float)
        if 'produtos_FINANCIAMENTO' in features.columns:
            features['produtos_FINANCIAMENTO'] = produtos_series.str.contains('FINANCIAMENTO', regex=False).astype(float)
        if 'produtos_EMPRESTIMO/FINANCIAMENTO' in features.columns:
            features['produtos_EMPRESTIMO/FINANCIAMENTO'] = (
                produtos_series == 'EMPRESTIMO/FINANCIAMENTO'
            ).astype(float)

        # Ocupação
        for option in [
            'APOSENTADO',
            'EMPREGADO_PRIVADO_AUTONOMO',
            'OUTROS',
            'RENDA_PASSIVA_PENSAO',
            'SERVIDOR_PUBLICO',
        ]:
            column_name = f'ocupacao_{option}'
            if column_name in features.columns:
                features[column_name] = (df_work['ocupacao'] == option).astype(float)

        # Escolaridade
        for option in ['ATE_FUNDAMENTAL', 'ENSINO_MEDIO', 'TECNICO_SUPERIOR']:
            column_name = f'grau_escolaridade_cat_{option}'
            if column_name in features.columns:
                features[column_name] = (
                    df_work['grau_escolaridade_cat'].map(self._normalize_text) == option
                ).astype(float)

        # Região
        for option in [
            'FORA_SC',
            'GRANDE_FLORIANOPOLIS',
            'NORTE_CATARINENSE',
            'OESTE_CATARINENSE',
            'SERRANA',
            'SUL_CATARINENSE',
            'VALE_DO_ITAJAI',
        ]:
            column_name = f'regiao_{option}'
            if column_name in features.columns:
                features[column_name] = (df_work['regiao'] == option).astype(float)

        if 'tipo_valor_entrada_Paga_entrada' in features.columns:
            features['tipo_valor_entrada_Paga_entrada'] = (
                df_work['tipo_valor_entrada'] == 'PAGA_ENTRADA'
            ).astype(float)

        if 'possui_contratos_a_vista_SIM' in features.columns:
            features['possui_contratos_a_vista_SIM'] = (
                df_work['possui_contratos_a_vista'] == 'SIM'
            ).astype(float)

        for option in [
            'Acima de 3 SM',
            'Até 1 SM',
            'De 1 SM a 1,25 SM',
            'De 1,25 SM a 1,5 SM',
            'De 1,5 SM a 2 SM',
            'De 2 SM a 3 SM',
        ]:
            column_name = f'fx_renda_valida_{option}'
            if column_name in features.columns:
                features[column_name] = (df_work['fx_renda_valida'] == option).astype(float)

        features = features.fillna(0.0)

        return df_work, features

    def preprocess(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Pré-processa os dados de entrada de um único cliente."""

        _, features = self.preprocess_dataframe(pd.DataFrame([data]))
        return features

    # ------------------------------------------------------------------
    # Predições
    # ------------------------------------------------------------------

    def predict_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Executa a predição para um DataFrame inteiro."""

        df_processed, features = self.preprocess_dataframe(df)
        rf_model = self.models['random_forest']
        probabilities = rf_model.predict_proba(features)[:, 1]

        relatorio = df_processed.copy()
        relatorio['pd'] = probabilities
        relatorio['score'] = ((1 - relatorio['pd']) * 1000).round().astype(int)
        relatorio['faixa_risco'] = relatorio['pd'].apply(self._get_risk_band)
        relatorio['limite_sugerido'] = [
            self._calculate_limit(pd_value, row)
            for pd_value, row in zip(relatorio['pd'], relatorio.to_dict('records'))
        ]
        decisions = [
            self._apply_policies(pd_value, faixa, row)
            for pd_value, faixa, row in zip(
                relatorio['pd'], relatorio['faixa_risco'], relatorio.to_dict('records')
            )
        ]
        relatorio['decisao'] = [item['action'] for item in decisions]
        relatorio['motivo'] = [item['reason'] for item in decisions]
        relatorio['timestamp'] = pd.Timestamp.now().isoformat()

        return relatorio

    def _compute_shap_values(self, features: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Calcula valores SHAP para interpretação do modelo."""

        if not _SHAP_AVAILABLE:
            return None

        rf_model = self.models['random_forest']
        explainer = shap.TreeExplainer(rf_model)  # type: ignore[arg-type]
        shap_values = explainer.shap_values(features)[1]
        shap_df = pd.DataFrame(
            shap_values,
            columns=[f"{column}_shap" for column in features.columns],
            index=features.index,
        )
        return shap_df

    def generate_outputs(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Gera todos os artefatos necessários para o dashboard."""

        relatorio = self.predict_dataframe(df)
        _, features = self.preprocess_dataframe(df)
        shap_df = self._compute_shap_values(features)
        if shap_df is not None and 'cpf_cnpj' in df.columns:
            shap_df = shap_df.copy()
            shap_df.insert(0, 'cpf_cnpj', df['cpf_cnpj'].values)

        indicadores = (
            relatorio.groupby('faixa_risco')
            .agg(
                quantidade=('cpf_cnpj', 'count'),
                score_medio=('score', 'mean'),
                pd_medio=('pd', 'mean'),
                limite_medio=('limite_sugerido', 'mean'),
            )
            .reset_index()
        )
        if not indicadores.empty:
            total = indicadores['quantidade'].sum()
            indicadores['percentual_clientes'] = (
                indicadores['quantidade'] / total * 100
            )
            total_row = {
                'faixa_risco': 'TOTAL',
                'quantidade': total,
                'score_medio': relatorio['score'].mean(),
                'pd_medio': relatorio['pd'].mean(),
                'limite_medio': relatorio['limite_sugerido'].mean(),
                'percentual_clientes': 100.0,
            }
            indicadores = pd.concat(
                [indicadores, pd.DataFrame([total_row])],
                ignore_index=True,
            )

        indicadores[['score_medio', 'pd_medio', 'limite_medio']] = indicadores[
            ['score_medio', 'pd_medio', 'limite_medio']
        ].round(4)

        return {
            'relatorio': relatorio,
            'features': features,
            'shap': shap_df,
            'indicadores': indicadores,
        }
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza predição para um cliente
        
        Args:
            data: Dicionário com os dados do cliente
            
        Returns:
            Dicionário com score, PD, faixa de risco e limite
        """
        try:
            relatorio = self.predict_dataframe(pd.DataFrame([data]))
            row = relatorio.iloc[0]

            return {
                "cpf_cnpj": row.get("cpf_cnpj"),
                "score": int(row.get("score", 0)),
                "pd": round(float(row.get("pd", 0.0)), 4),
                "faixa_risco": row.get("faixa_risco"),
                "limite_sugerido": float(row.get("limite_sugerido", 0.0)),
                "decisao": row.get("decisao"),
                "motivo": row.get("motivo"),
                "timestamp": row.get("timestamp"),
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

