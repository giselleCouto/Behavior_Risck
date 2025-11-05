"""Serviço para carregar e executar o modelo Behavior Score."""

from __future__ import annotations

import logging
import os
import sys
import types
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataValidationError(ValueError):
    """Raised when the input payload violates the expected schema."""


@dataclass(frozen=True)
class ColumnSpec:
    """Definition of a column expected by the scoring pipeline."""

    name: str
    dtype: str
    required: bool = True
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    allowed: Optional[Iterable[str]] = None

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
        self.retraining_enabled = False
        self.retraining_strategy = "offline_manual"
        self._column_specs: Dict[str, ColumnSpec] = self._build_column_specs()
        self._column_aliases: Dict[str, str] = {
            "qtd_contratos_regular": "qtd_contratos_fechado_regular",
            "qtd_contratos_regulares": "qtd_contratos_fechado_regular",
            "media_atraso_dias": "mean_dias_maior_atraso",
            "dias_maior_atraso_medio": "mean_dias_maior_atraso",
            "possui_contratos_a_vista": "possui_contratos_a_vista",
            "possui_contratos_a_vista?": "possui_contratos_a_vista",
            "regiao_cliente": "regiao",
            "canal": "canal_origem",
            "produtos_ativos": "produtos",
        }
        self._quality_events: List[Dict[str, Any]] = []
        self.limit_fallback_factor = 0.35
        self._ocupacao_map = {
            "APOSENTADO_EMPRESA_PUBLICA": "APOSENTADO",
            "APOSENTADO_EMPRESA_PUBLICA_ESTADUAL": "APOSENTADO",
            "APOSENTADO_EMPRESA_PUBLICA_FEDERAL": "APOSENTADO",
            "APOSENTADO_EMPRESA_PUBLICA_MUNICIPAL": "APOSENTADO",
            "APOSENTADO_EMPRESA_PRIVADA": "APOSENTADO",
            "APOSENTADO_MILITAR,_MILITAR_RESERVA_OU_REFORMADO": "APOSENTADO",
            "PENSIONISTA_DA_PREVIDENCIA_SOCIAL_(INSS)": "RENDA_PASSIVA_PENSAO",
            "BENEFICIARIO_DE_PENSAO": "RENDA_PASSIVA_PENSAO",
            "LOCATARIO_RENDA_COM_ALUGUEIS": "RENDA_PASSIVA_PENSAO",
            "AUTONOMO_SEM_VINCULO_EMPREGO": "EMPREGADO_PRIVADO_AUTONOMO",
            "EMPREGADO_SETOR_PRIVADO,EXCETO_INSTITUICAO_FINANC": "EMPREGADO_PRIVADO_AUTONOMO",
            "EMPREGADO_DE_INSTITUICOES_FINANCEIRAS_PRIVADAS": "EMPREGADO_PRIVADO_AUTONOMO",
            "SERVIDOR_PUBLICO_ESTADUAL": "SERVIDOR_PUBLICO",
            "SERVIDOR_PUBLICO_FEDERAL": "SERVIDOR_PUBLICO",
            "SERVIDOR_PUBLICO_MUNICIPAL": "SERVIDOR_PUBLICO",
            "PROFISSIONAL_LIBERAL": "OUTROS",
            "EMPRESARIO_PROPRIETARIO_OU_FIRMA_INDIVIDUAL": "OUTROS",
            "MICROEMPRESARIO/MICROEMPREENDEDOR_INDIVIDUAL(MEI)": "OUTROS",
            "BOLSISTA": "OUTROS",
            "DO_LAR": "OUTROS",
            "ESTUDANTE": "OUTROS",
            "NATUREZA_OCUPACAO_NAO_ESPECIFICADA_ANTERIORMENTE": "OUTROS",
        }

    def _build_column_specs(self) -> Dict[str, ColumnSpec]:
        """Return the schema definition consumed by the preprocessing steps."""

        return {
            "cpf_cnpj": ColumnSpec("cpf_cnpj", "str"),
            "idade": ColumnSpec("idade", "float", minimum=18, maximum=120),
            "sexo": ColumnSpec("sexo", "str"),
            "estado_civil": ColumnSpec("estado_civil", "str"),
            "nacionalidade": ColumnSpec("nacionalidade", "str"),
            "grau_escolaridade_cat": ColumnSpec("grau_escolaridade_cat", "str", required=False),
            "natureza_ocupacao": ColumnSpec("natureza_ocupacao", "str"),
            "ocupacao": ColumnSpec("ocupacao", "str", required=False),
            "renda_valida_new": ColumnSpec("renda_valida_new", "float", minimum=0),
            "renda_comprometida": ColumnSpec("renda_comprometida", "float", minimum=0),
            "tempo_relacionamento_kredilig_meses": ColumnSpec(
                "tempo_relacionamento_kredilig_meses", "float", minimum=0
            ),
            "media_meses_entre_contratos_combinado": ColumnSpec(
                "media_meses_entre_contratos_combinado", "float"
            ),
            "qtd_contratos_fechado_regular": ColumnSpec(
                "qtd_contratos_fechado_regular", "float", minimum=0
            ),
            "meses_ultimo_pagamento": ColumnSpec(
                "meses_ultimo_pagamento", "float", minimum=0, required=False
            ),
            "qtd_contratos_nr": ColumnSpec("qtd_contratos_nr", "float", minimum=0),
            "qtd_parcelas_pagas_nr": ColumnSpec("qtd_parcelas_pagas_nr", "float", minimum=0),
            "valor_pago_nr": ColumnSpec("valor_pago_nr", "float", minimum=0),
            "valor_principal_total_nr": ColumnSpec("valor_principal_total_nr", "float", minimum=0),
            "mean_dias_maior_atraso": ColumnSpec(
                "mean_dias_maior_atraso", "float", minimum=0, required=False
            ),
            "dias_maior_atraso": ColumnSpec("dias_maior_atraso", "float", minimum=0, required=False),
            "canal_origem": ColumnSpec("canal_origem", "str"),
            "produtos": ColumnSpec("produtos", "str"),
            "regiao": ColumnSpec("regiao", "str"),
            "tipo_valor_entrada": ColumnSpec("tipo_valor_entrada", "str", required=False),
            "possui_contratos_a_vista": ColumnSpec("possui_contratos_a_vista", "str", required=False),
            "limite_total_ultimo_mes": ColumnSpec("limite_total_ultimo_mes", "float", minimum=0, required=False),
        }

    def load_models(self):
        """Carrega todos os modelos e artefatos necessários"""
        try:
            logger.info("Carregando pré-processadores...")

            # Carrega imputers
            preproc_path = self.model_path / "Pré-Processamento"
            self.preprocessors['imputer_cat'] = self._load_joblib(preproc_path / "imputer_cat.pkl")
            self.preprocessors['imputer_num'] = self._load_joblib(preproc_path / "imputer_num.pkl")
            self.preprocessors['imputer_num_median'] = self._load_joblib(preproc_path / "imputer_num_median.pkl")
            self.preprocessors['imputer_parametros'] = self._load_imputer_parameters(preproc_path / "imputer_parametros.pkl")
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
        """Safely load sklearn artefacts serialized with joblib/pickle."""

        try:
            return joblib.load(file_path)
        except Exception as exc:
            logger.error("Erro ao carregar %s: %s", file_path, exc)
            raise

    def _load_imputer_parameters(self, file_path: Path) -> Dict[str, pd.Series]:
        """Load custom Series based imputers saved during training."""

        series_module = types.ModuleType("Series")
        series_module.Series = pd.Series
        series_module.dtype = lambda *args, **kwargs: np.dtype("O")
        sys.modules.setdefault("Series", series_module)
        try:
            return joblib.load(file_path)
        finally:
            sys.modules.pop("Series", None)

    def preprocess_dataframe(
        self, df: pd.DataFrame, *, collect_quality: bool = False
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Normalize, validate and engineer features for scoring."""

        if df.empty:
            raise DataValidationError("Nenhum registro informado para processamento.")

        self._quality_events = []
        working = self._normalize_dataframe(df)
        self._enforce_schema(working)
        self._apply_domain_cleaning(working)
        engineered = self._engineer_features(working)

        quality_df = pd.DataFrame(self._quality_events)
        if collect_quality and quality_df.empty:
            quality_df = pd.DataFrame([
                {
                    "coluna": "-",
                    "tipo": "info",
                    "detalhe": "Nenhum ajuste de qualidade foi necessário.",
                }
            ])
        return engineered, quality_df if collect_quality else pd.DataFrame(), working.copy()

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column naming and apply known aliases."""

        normalized = df.copy()
        rename_map = {col: self._normalize_column_name(col) for col in normalized.columns}
        normalized.rename(columns=rename_map, inplace=True)

        for alias, canonical in self._column_aliases.items():
            if alias in normalized.columns:
                if canonical in normalized.columns:
                    normalized[canonical] = normalized[canonical].fillna(normalized[alias])
                else:
                    normalized[canonical] = normalized[alias]
                normalized.drop(columns=[alias], inplace=True)

        return normalized

    def _normalize_column_name(self, name: str) -> str:
        base = unicodedata.normalize("NFKD", str(name))
        base = "".join(ch for ch in base if not unicodedata.combining(ch))
        base = base.replace("%", "_percent")
        for token in ["/", "-", " ", "\n", "\t", "."]:
            base = base.replace(token, "_")
        return base.lower()

    def _enforce_schema(self, df: pd.DataFrame) -> None:
        """Ensure mandatory fields exist and values stay within expected ranges."""

        missing = [spec.name for spec in self._column_specs.values() if spec.required and spec.name not in df.columns]
        if missing:
            raise DataValidationError(
                f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}."
            )

        for spec in self._column_specs.values():
            if spec.name not in df.columns:
                continue
            column = df[spec.name]
            if spec.dtype in {"float", "int"}:
                coerced = pd.to_numeric(column, errors="coerce")
                invalid = coerced.isna() & column.notna()
                if invalid.any():
                    self._quality_events.append(
                        {
                            "coluna": spec.name,
                            "tipo": "coercao",
                            "detalhe": f"{invalid.sum()} registro(s) convertidos para valores nulos por não serem numéricos.",
                        }
                    )
                df[spec.name] = coerced
            else:
                df[spec.name] = column.astype(str).str.strip()

            if spec.minimum is not None:
                below_min = df[spec.name] < spec.minimum
                if below_min.any():
                    raise DataValidationError(
                        f"Valores inválidos em {spec.name}: {int(below_min.sum())} registro(s) abaixo do mínimo {spec.minimum}."
                    )
            if spec.maximum is not None:
                above_max = df[spec.name] > spec.maximum
                if above_max.any():
                    raise DataValidationError(
                        f"Valores inválidos em {spec.name}: {int(above_max.sum())} registro(s) acima do máximo {spec.maximum}."
                    )

    def _apply_domain_cleaning(self, df: pd.DataFrame) -> None:
        """Standardize domain specific values and apply imputations."""

        text_columns = [
            "sexo",
            "estado_civil",
            "nacionalidade",
            "grau_escolaridade_cat",
            "natureza_ocupacao",
            "ocupacao",
            "canal_origem",
            "produtos",
            "regiao",
            "tipo_valor_entrada",
            "possui_contratos_a_vista",
        ]

        for column in text_columns:
            if column not in df.columns:
                continue
            df[column] = (
                df[column]
                .astype(str)
                .str.strip()
                .replace({"nan": np.nan, "None": np.nan, "": np.nan})
            )
            df[column] = df[column].apply(self._normalize_category_value)

        if "possui_contratos_a_vista" in df.columns:
            df["possui_contratos_a_vista"] = df["possui_contratos_a_vista"].fillna("NAO")

        if "tipo_valor_entrada" in df.columns:
            df["tipo_valor_entrada"] = df["tipo_valor_entrada"].fillna("N_PAGA_ENTRADA")

        if "sexo" in df.columns:
            df["sexo"] = df["sexo"].replace({"MASCULINO": "M", "FEMININO": "F"})

        if "mean_dias_maior_atraso" not in df.columns and "dias_maior_atraso" in df.columns:
            df["mean_dias_maior_atraso"] = df["dias_maior_atraso"]

        if "mean_dias_maior_atraso" in df.columns:
            df["mean_dias_maior_atraso"] = df["mean_dias_maior_atraso"].fillna(0)

        self._apply_imputations(df)

    def _normalize_category_value(self, value: Optional[str]) -> Optional[str]:
        if value is None or value != value:  # NaN check
            return None
        normalized = unicodedata.normalize("NFKD", value)
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        normalized = normalized.upper().replace(" ", "_")
        normalized = normalized.replace("-", "_").replace("/", "/")
        normalized = normalized.replace("Ã", "A")
        return normalized

    def _apply_imputations(self, df: pd.DataFrame) -> None:
        """Impute missing values using persisted strategies from training."""

        parametros = self.preprocessors.get("imputer_parametros", {})

        if "natureza_ocupacao" in df.columns:
            if "grau_escolaridade_cat" in df.columns and "moda_grau_escolaridade_cat" in parametros:
                series = parametros["moda_grau_escolaridade_cat"]
                mask = df["grau_escolaridade_cat"].isna() & df["natureza_ocupacao"].notna()
                imputados = df.loc[mask, "natureza_ocupacao"].map(series)
                df.loc[mask, "grau_escolaridade_cat"] = imputados
                if mask.any():
                    self._quality_events.append(
                        {
                            "coluna": "grau_escolaridade_cat",
                            "tipo": "imputacao",
                            "detalhe": f"{int(mask.sum())} registro(s) preenchidos a partir da natureza da ocupação.",
                        }
                    )

            if "estado_civil" in df.columns and "moda_estado_civil" in parametros:
                series = parametros["moda_estado_civil"]
                mask = df["estado_civil"].isna() & df["natureza_ocupacao"].notna()
                imputados = df.loc[mask, "natureza_ocupacao"].map(series)
                df.loc[mask, "estado_civil"] = imputados
                if mask.any():
                    self._quality_events.append(
                        {
                            "coluna": "estado_civil",
                            "tipo": "imputacao",
                            "detalhe": f"{int(mask.sum())} registro(s) preenchidos pela moda observada na ocupação.",
                        }
                    )

            if "renda_valida_new" in df.columns and "medias_renda_valida" in parametros:
                series = parametros["medias_renda_valida"]
                mask = df["renda_valida_new"].isna() & df["natureza_ocupacao"].notna()
                imputados = df.loc[mask, "natureza_ocupacao"].map(series)
                df.loc[mask, "renda_valida_new"] = imputados
                if mask.any():
                    self._quality_events.append(
                        {
                            "coluna": "renda_valida_new",
                            "tipo": "imputacao",
                            "detalhe": f"{int(mask.sum())} registro(s) preenchidos com a média observada na ocupação.",
                        }
                    )

            if "renda_comprometida" in df.columns and "medias_renda_comprometida" in parametros:
                series = parametros["medias_renda_comprometida"]
                mask = df["renda_comprometida"].isna() & df["natureza_ocupacao"].notna()
                imputados = df.loc[mask, "natureza_ocupacao"].map(series)
                df.loc[mask, "renda_comprometida"] = imputados
                if mask.any():
                    self._quality_events.append(
                        {
                            "coluna": "renda_comprometida",
                            "tipo": "imputacao",
                            "detalhe": f"{int(mask.sum())} registro(s) preenchidos com a média por ocupação.",
                        }
                    )

        cat_imputer = self.preprocessors.get("imputer_cat")
        if cat_imputer is not None:
            cat_cols = [col for col in cat_imputer.feature_names_in_ if col in df.columns]
            if cat_cols:
                before = df[cat_cols].isna().sum()
                df[cat_cols] = pd.DataFrame(
                    cat_imputer.transform(df[cat_cols]),
                    columns=cat_cols,
                    index=df.index,
                )
                after = df[cat_cols].isna().sum()
                filled = (before - after).clip(lower=0)
                for column, count in filled.items():
                    if count > 0:
                        self._quality_events.append(
                            {
                                "coluna": column,
                                "tipo": "imputacao",
                                "detalhe": f"{int(count)} registro(s) preenchidos pelo imputador categórico.",
                            }
                        )

        num_imputer = self.preprocessors.get("imputer_num")
        if num_imputer is not None:
            num_cols = [col for col in num_imputer.feature_names_in_ if col in df.columns]
            if num_cols:
                before = df[num_cols].isna().sum()
                df[num_cols] = pd.DataFrame(
                    num_imputer.transform(df[num_cols]),
                    columns=num_cols,
                    index=df.index,
                )
                filled = (before - df[num_cols].isna().sum()).clip(lower=0)
                for column, count in filled.items():
                    if count > 0:
                        self._quality_events.append(
                            {
                                "coluna": column,
                                "tipo": "imputacao",
                                "detalhe": f"{int(count)} registro(s) preenchidos pelo imputador numérico (média).",
                            }
                        )

        median_imputer = self.preprocessors.get("imputer_num_median")
        if median_imputer is not None:
            med_cols = [col for col in median_imputer.feature_names_in_ if col in df.columns]
            if med_cols:
                before = df[med_cols].isna().sum()
                df[med_cols] = pd.DataFrame(
                    median_imputer.transform(df[med_cols]),
                    columns=med_cols,
                    index=df.index,
                )
                filled = (before - df[med_cols].isna().sum()).clip(lower=0)
                for column, count in filled.items():
                    if count > 0:
                        self._quality_events.append(
                            {
                                "coluna": column,
                                "tipo": "imputacao",
                                "detalhe": f"{int(count)} registro(s) preenchidos pelo imputador mediano.",
                            }
                        )

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create the feature matrix expected by the Random Forest model."""

        working = df.copy()

        if "ocupacao" not in working.columns:
            working["ocupacao"] = np.nan

        if "natureza_ocupacao" in working.columns:
            mapped = working["natureza_ocupacao"].map(self._ocupacao_map)
            working["ocupacao"] = working["ocupacao"].fillna(mapped)
        working["ocupacao"] = working["ocupacao"].fillna("OUTROS")

        scaler = self.preprocessors.get("scaler_num")
        numeric_cols = list(scaler.feature_names_in_) if scaler is not None else []

        for column in numeric_cols:
            if column not in working.columns:
                working[column] = 0.0
                self._quality_events.append(
                    {
                        "coluna": column,
                        "tipo": "preenchimento",
                        "detalhe": "Coluna ausente preenchida com zero para compatibilidade com o scaler.",
                    }
                )

        if scaler is not None:
            scaled_values = scaler.transform(working[numeric_cols])
            working[numeric_cols] = pd.DataFrame(
                scaled_values,
                columns=numeric_cols,
                index=working.index,
            )

        engineered = pd.DataFrame(index=working.index)
        for column in [
            "idade",
            "tempo_relacionamento_kredilig_meses",
            "media_meses_entre_contratos_combinado",
            "qtd_contratos_fechado_regular",
            "meses_ultimo_pagamento",
            "qtd_parcelas_pagas_nr",
            "valor_pago_nr",
            "valor_principal_total_nr",
            "mean_dias_maior_atraso",
            "qtd_contratos_nr",
            "renda_valida_new",
            "renda_comprometida",
        ]:
            if column not in working.columns:
                working[column] = 0
                self._quality_events.append(
                    {
                        "coluna": column,
                        "tipo": "preenchimento",
                        "detalhe": "Coluna ausente preenchida com zero por não estar presente na carga.",
                    }
                )
            engineered[column] = working[column]

        engineered["sexo_M"] = (working.get("sexo", "") == "M").astype(int)

        estado_map = {
            "CASADO": "estado_civil_CASADO",
            "DIVORCIADO": "estado_civil_DIVORCIADO",
            "SOLTEIRO": "estado_civil_SOLTEIRO",
            "UNIAO_ESTAVEL": "estado_civil_UNIAO ESTAVEL",
            "VIUVO": "estado_civil_VIUVO",
        }
        estado_civil_series = working.get("estado_civil", pd.Series(index=working.index))
        for raw_value, feature_name in estado_map.items():
            engineered[feature_name] = (estado_civil_series == raw_value).astype(int)

        engineered["nacionalidade_ESTRANGEIRO"] = (
            working.get("nacionalidade", "") == "ESTRANGEIRO"
        ).astype(int)

        engineered["canal_origem_Fisico"] = (
            working.get("canal_origem", pd.Series(index=working.index)).fillna("") == "FISICO"
        ).astype(int)

        produtos_map = {
            "EMPRESTIMO/FINANCIAMENTO": "EMPRESTIMO/FINANCIAMENTO",
            "EMPRESTIMO": "EMPRESTIMO",
            "FINANCIAMENTO": "FINANCIAMENTO",
        }
        produtos_value = working.get("produtos", pd.Series(index=working.index)).map(produtos_map).fillna("OUTROS")
        for categoria in ["EMPRESTIMO", "EMPRESTIMO/FINANCIAMENTO", "FINANCIAMENTO"]:
            engineered[f"produtos_{categoria}"] = (produtos_value == categoria).astype(int)

        ocupacao_value = working["ocupacao"].fillna("OUTROS")
        for categoria in [
            "APOSENTADO",
            "EMPREGADO_PRIVADO_AUTONOMO",
            "OUTROS",
            "RENDA_PASSIVA_PENSAO",
            "SERVIDOR_PUBLICO",
        ]:
            engineered[f"ocupacao_{categoria}"] = (ocupacao_value == categoria).astype(int)

        escolaridade_value = working.get("grau_escolaridade_cat", pd.Series(index=working.index)).fillna("ATE_FUNDAMENTAL")
        for categoria in ["ATE_FUNDAMENTAL", "ENSINO_MEDIO", "TECNICO_SUPERIOR"]:
            engineered[f"grau_escolaridade_cat_{categoria}"] = (
                escolaridade_value == categoria
            ).astype(int)

        regiao_map = {
            "FORA_SC": "Fora_SC",
            "GRANDE_FLORIANOPOLIS": "Grande_Florianópolis",
            "NORTE_CATARINENSE": "Norte_Catarinense",
            "OESTE_CATARINENSE": "Oeste_Catarinense",
            "SERRANA": "Serrana",
            "SUL_CATARINENSE": "Sul_Catarinense",
            "VALE_DO_ITAJAI": "Vale_do_Itajaí",
        }
        regiao_value = working.get("regiao", pd.Series(index=working.index)).map(regiao_map).fillna("Fora_SC")
        for categoria in regiao_map.values():
            engineered[f"regiao_{categoria}"] = (regiao_value == categoria).astype(int)

        engineered["tipo_valor_entrada_Paga_entrada"] = (
            working.get("tipo_valor_entrada", "") == "PAGA_ENTRADA"
        ).astype(int)

        engineered["possui_contratos_a_vista_SIM"] = (
            working.get("possui_contratos_a_vista", "") == "SIM"
        ).astype(int)

        renda_series = working.get("renda_valida_new", pd.Series(index=working.index, dtype=float)).astype(float)
        fx_labels = [
            "Até 1 SM",
            "De 1 SM a 1,25 SM",
            "De 1,25 SM a 1,5 SM",
            "De 1,5 SM a 2 SM",
            "De 2 SM a 3 SM",
            "Acima de 3 SM",
        ]
        fx_bins = [0, 1518, 1518 * 1.25, 1518 * 1.5, 1518 * 2, 1518 * 3, np.inf]
        renda_fx = pd.cut(renda_series.fillna(0), bins=fx_bins, labels=fx_labels, include_lowest=True)
        for label in fx_labels:
            engineered[f"fx_renda_valida_{label}"] = (renda_fx == label).astype(int)

        rf_features = list(self.models['random_forest'].feature_names_in_)
        missing_features = [feature for feature in rf_features if feature not in engineered.columns]
        for feature in missing_features:
            engineered[feature] = 0

        engineered = engineered[rf_features]

        kmeans_model = self.models.get('kmeans')
        if kmeans_model is not None:
            cluster_features = [col for col in kmeans_model.feature_names_in_ if col in working.columns or col in engineered.columns]
            cluster_frame = pd.DataFrame(index=working.index)
            for col in cluster_features:
                if col in engineered.columns:
                    cluster_frame[col] = engineered[col]
                else:
                    cluster_frame[col] = working.get(col, 0)
            working['cluster_kmeans'] = kmeans_model.predict(cluster_frame)
        else:
            working['cluster_kmeans'] = 0

        return engineered
    
    def check_health(self) -> Dict[str, Any]:
        """Verifica se todos os modelos estão carregados"""
        return {
            "preprocessors_loaded": len(self.preprocessors) > 0,
            "models_loaded": len(self.models) > 0,
            "bins_loaded": len(self.bins) > 0,
            "limits_table_loaded": self.limits_table is not None,
            "retraining_enabled": self.retraining_enabled,
            "all_loaded": (
                len(self.preprocessors) > 0 and
                len(self.models) > 0 and
                len(self.bins) > 0 and
                self.limits_table is not None
            )
        }

    def retraining_status(self) -> Dict[str, Any]:
        """Expose the current retraining configuration for monitoring."""
        return {
            "enabled": self.retraining_enabled,
            "strategy": self.retraining_strategy,
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
        """Pré-processa os dados de entrada e retorna a matriz de features."""

        feature_df, _, _ = self.preprocess_dataframe(pd.DataFrame([data]), collect_quality=False)
        return feature_df

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
            df_processed, quality, _normalized = self.preprocess_dataframe(pd.DataFrame([data]), collect_quality=True)

            if not quality.empty:
                logger.info("Ajustes de qualidade aplicados: %s", quality.to_dict(orient="records"))

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
            faixa_risco, risk_interval = self._get_risk_band(score)

            # Calcula limite sugerido
            limite_sugerido = self._calculate_limit(score, pd_value, risk_interval, data)
            
            # Aplica políticas de crédito
            decision = self._apply_policies(pd_value, faixa_risco, data)
            
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
    
    def _get_risk_band(self, score: float) -> Tuple[str, str]:
        """Determina a faixa de risco com base no score usando os bins salvos."""

        if 'risco' not in self.bins:
            raise RuntimeError("Bins de risco não foram carregados.")

        bins = self.bins['risco']
        interval = pd.cut([score], bins=bins, precision=6)[0]
        interval_str = str(interval)

        # Determina quantil para mapear a faixa de risco
        position = int(np.searchsorted(bins, score, side='right') - 1)
        total_intervals = max(len(bins) - 1, 1)
        quantile_ratio = position / total_intervals

        if quantile_ratio >= 0.80:
            label = "MUITO BAIXO"
        elif quantile_ratio >= 0.60:
            label = "BAIXO"
        elif quantile_ratio >= 0.40:
            label = "MEDIO"
        elif quantile_ratio >= 0.20:
            label = "ALTO"
        else:
            label = "MUITO ALTO"

        return label, interval_str

    def _parse_interval(self, value: str) -> pd.Interval:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Intervalo vazio para fx_risco")
        left_bracket, right_bracket = cleaned[0], cleaned[-1]
        left_str, right_str = cleaned[1:-1].split(",")
        left = float("-inf") if left_str.strip() in {"-inf", "-Inf"} else float(left_str)
        right = float("inf") if right_str.strip() in {"inf", "Inf"} else float(right_str)
        if left_bracket == "[" and right_bracket == "]":
            closed = "both"
        elif left_bracket == "[" and right_bracket == ")":
            closed = "left"
        elif left_bracket == "(" and right_bracket == "]":
            closed = "right"
        else:
            closed = "neither"
        return pd.Interval(left, right, closed=closed)

    def _calculate_limit(self, score: float, pd_value: float, risk_interval: str, data: Dict[str, Any]) -> float:
        """Calcula o limite sugerido baseado no score e na tabela isotônica."""
        try:
            if self.limits_table is not None:
                table = self.limits_table.copy()
                table['fx_risco'] = table['fx_risco'].astype(str).str.strip()
                match = table['fx_risco'] == risk_interval
                if match.any():
                    limite = table.loc[match, 'media_limite_isotonico'].iloc[0]
                    return float(limite)

                # Caso não exista correspondência textual, aproxima pelo intervalo mais próximo
                table['_interval'] = table['fx_risco'].apply(self._parse_interval)
                distances = table['_interval'].apply(
                    lambda interval: abs(interval.mid - score) if np.isfinite(interval.mid) else np.inf
                )
                nearest_idx = distances.astype(float).idxmin()
                limite = table.loc[nearest_idx, 'media_limite_isotonico']
                self._quality_events.append(
                    {
                        "coluna": "fx_risco",
                        "tipo": "fallback",
                        "detalhe": "Intervalo de risco não encontrado; utilizado o limite do intervalo mais próximo.",
                    }
                )
                return float(limite)

            base_limit = 20000
            limit = base_limit * (1 - min(pd_value, 0.95)) * self.limit_fallback_factor
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

