"""Utility helpers for managing uploaded artifacts in the dashboard pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from functools import lru_cache
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import parse_qs, urlparse

import pandas as pd
import requests
import re

from deploy.api.model_service import BehaviorScoreModel, DataValidationError


@dataclass
class UploadedArtifacts:
    """Container that stores the artefacts used across the dashboard tabs."""

    relatorio: Optional[pd.DataFrame] = None
    relatorio_name: Optional[str] = None
    relatorio_features: Optional[pd.DataFrame] = None
    relatorio_quality: Optional[pd.DataFrame] = None
    shap_values: Optional[pd.DataFrame] = None
    shap_name: Optional[str] = None
    indicadores: Optional[pd.DataFrame] = None
    indicadores_name: Optional[str] = None

    def has_relatorio(self) -> bool:
        return self.relatorio is not None

    def has_shap(self) -> bool:
        return self.shap_values is not None

    def has_indicadores(self) -> bool:
        return self.indicadores is not None


class FileSourceOption(str, Enum):
    """Supported mechanisms for ingesting dashboard artefacts."""

    UPLOAD = "upload"
    GOOGLE_DRIVE = "google_drive"
    ONEDRIVE = "onedrive"


FILE_SOURCE_LABELS = {
    FileSourceOption.UPLOAD: "Upload manual",
    FileSourceOption.GOOGLE_DRIVE: "Google Drive",
    FileSourceOption.ONEDRIVE: "OneDrive",
}


class FileSourceError(RuntimeError):
    """Raised when an external file cannot be retrieved."""


def available_file_sources() -> list[FileSourceOption]:
    """Return the supported ingestion sources for artefacts."""

    return list(FILE_SOURCE_LABELS.keys())


def file_source_label(option: FileSourceOption) -> str:
    """Return the human readable label for a file source."""

    return FILE_SOURCE_LABELS[option]


def _extract_filename_from_headers(headers: requests.structures.CaseInsensitiveDict, fallback: str) -> str:
    """Infer a filename from the response headers if available."""

    content_disposition = headers.get("content-disposition")
    if content_disposition:
        match = re.search(r'filename="?([^";]+)"?', content_disposition)
        if match:
            return match.group(1)
    return fallback


def _google_drive_direct_download_url(url: str) -> Tuple[str, str]:
    """Transform a Google Drive sharing link into a direct download URL."""

    parsed = urlparse(url)
    if "drive.google.com" not in parsed.netloc:
        raise FileSourceError("O link informado não pertence ao Google Drive.")

    if parsed.path.startswith("/uc") and "id" in parse_qs(parsed.query):
        file_id = parse_qs(parsed.query)["id"][0]
        return url, file_id

    if "/d/" in parsed.path:
        file_id = parsed.path.split("/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}", file_id

    query = parse_qs(parsed.query)
    if "id" in query:
        file_id = query["id"][0]
        return f"https://drive.google.com/uc?export=download&id={file_id}", file_id

    raise FileSourceError("Não foi possível identificar o ID do arquivo do Google Drive.")


def _onedrive_direct_download_url(url: str) -> str:
    """Transform a OneDrive sharing link into a direct download URL."""

    parsed = urlparse(url)
    if "onedrive.live.com" not in parsed.netloc and "1drv.ms" not in parsed.netloc:
        raise FileSourceError("O link informado não pertence ao OneDrive.")

    if "download=" in parsed.query:
        return url

    separator = "&" if parsed.query else "?"
    return f"{url}{separator}download=1"


def fetch_external_file(
    *,
    source: FileSourceOption,
    reference: str,
    default_name: str,
) -> Tuple[BytesIO, str]:
    """Download an artefact shared via Google Drive or OneDrive."""

    if not reference:
        raise FileSourceError("Informe um link válido para realizar o download do arquivo.")

    if source is FileSourceOption.GOOGLE_DRIVE:
        download_url, file_id = _google_drive_direct_download_url(reference)
        fallback_name = f"google_drive_{file_id}" if default_name is None else default_name
    elif source is FileSourceOption.ONEDRIVE:
        download_url = _onedrive_direct_download_url(reference)
        fallback_name = default_name or "onedrive_arquivo"
    else:
        raise FileSourceError("Fonte de arquivo não suportada para download externo.")

    try:
        response = requests.get(download_url, allow_redirects=True, timeout=60)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FileSourceError(f"Falha ao baixar o arquivo compartilhado: {exc}") from exc

    filename = _extract_filename_from_headers(response.headers, fallback_name)
    buffer = BytesIO(response.content)
    buffer.seek(0)
    return buffer, filename


def load_relatorio(file) -> pd.DataFrame:
    """Loads the Behaviour report CSV file."""
    return pd.read_csv(file, sep=",")


def load_shap(file) -> pd.DataFrame:
    """Loads the SHAP parquet file."""
    return pd.read_parquet(file)


def load_indicadores(file) -> pd.DataFrame:
    """Loads the indicator spreadsheet."""
    return pd.read_excel(file)


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a dataframe to CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")


def df_to_parquet_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a dataframe to Parquet bytes."""
    buffer = BytesIO()
    df.to_parquet(buffer, index=False)
    return buffer.getvalue()


def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a dataframe to Excel bytes."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer.getvalue()


@lru_cache(maxsize=1)
def load_behavior_model(model_dir: Optional[str] = None) -> BehaviorScoreModel:
    """Carrega e mantém em cache o serviço de modelo compartilhado."""

    candidate_path = Path(model_dir) if model_dir else Path("Modelos")
    service = BehaviorScoreModel(str(candidate_path if candidate_path.exists() else "/app/Modelos"))
    service.load_models()
    return service


def sanitize_behavior_dataset(
    df: pd.DataFrame, *, model: Optional[BehaviorScoreModel] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Normaliza o relatório de behavior para scoring e gera um relatório de qualidade."""

    service = model or load_behavior_model()
    try:
        features, quality, normalized = service.preprocess_dataframe(df, collect_quality=True)
    except DataValidationError as exc:
        raise ValueError(f"Falha na validação do relatório: {exc}") from exc

    return normalized, features, quality


def summarize_quality_events(quality_df: pd.DataFrame) -> pd.DataFrame:
    """Agrega os eventos de qualidade em uma visão amigável para o dashboard."""

    if quality_df is None or quality_df.empty:
        return pd.DataFrame(
            [
                {
                    "coluna": "-",
                    "tipo": "info",
                    "ocorrencias": 0,
                    "detalhes": "Nenhum ajuste necessário.",
                }
            ]
        )

    grouped = quality_df.groupby(["coluna", "tipo"])
    summary = grouped.agg(
        ocorrencias=("detalhe", "size"),
        detalhes=("detalhe", lambda values: "; ".join(sorted(set(values)))),
    ).reset_index()
    return summary.sort_values(["tipo", "coluna"]).reset_index(drop=True)
