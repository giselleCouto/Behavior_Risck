"""
Cliente Python para a API do Behavior Score KAB

Exemplo de uso da API de predição de risco de crédito.
"""

import requests
import json
from typing import Dict, List, Any
from datetime import datetime


class BehaviorScoreClient:
    """Cliente para interagir com a API do Behavior Score"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        """
        Inicializa o cliente
        
        Args:
            base_url: URL base da API
            api_key: Chave de API (se configurada)
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {"Content-Type": "application/json"}
        
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica o status da API
        
        Returns:
            Status de saúde da API
        """
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def predict(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza predição para um único cliente
        
        Args:
            client_data: Dados do cliente
            
        Returns:
            Predição de risco com score, PD, faixa e limite
            
        Example:
            >>> client = BehaviorScoreClient()
            >>> data = {
            ...     "cpf_cnpj": "12345678900",
            ...     "idade": 35,
            ...     "renda_valida_new": 3000.0,
            ...     "tempo_relacionamento_kredilig_meses": 24,
            ...     "qtd_contratos": 5,
            ...     "dias_maior_atraso": 15
            ... }
            >>> result = client.predict(data)
            >>> print(f"Score: {result['score']}, Risco: {result['faixa_risco']}")
        """
        response = requests.post(
            f"{self.base_url}/predict",
            headers=self.headers,
            json=client_data
        )
        response.raise_for_status()
        return response.json()
    
    def predict_batch(self, clients_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Realiza predições em lote
        
        Args:
            clients_data: Lista de dados de clientes
            
        Returns:
            Resultados das predições em lote
        """
        payload = {"clients": clients_data}
        
        response = requests.post(
            f"{self.base_url}/predict/batch",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtém informações sobre o modelo
        
        Returns:
            Informações do modelo
        """
        response = requests.get(f"{self.base_url}/model/info")
        response.raise_for_status()
        return response.json()
    
    def get_expected_features(self) -> Dict[str, List[str]]:
        """
        Obtém as features esperadas pelo modelo
        
        Returns:
            Lista de features requeridas e opcionais
        """
        response = requests.get(f"{self.base_url}/model/features")
        response.raise_for_status()
        return response.json()


def exemplo_predicao_individual():
    """Exemplo de predição individual"""
    print("=" * 60)
    print("Exemplo 1: Predição Individual")
    print("=" * 60)
    
    # Inicializa cliente
    client = BehaviorScoreClient()
    
    # Verifica se API está disponível
    health = client.health_check()
    print(f"\n✅ API Status: {health['status']}")
    print(f"   Modelo carregado: {health['model_loaded']}")
    
    # Dados do cliente
    cliente = {
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
        "reneg_vs_liq_ratio_ponderado": 0.2
    }
    
    # Realiza predição
    resultado = client.predict(cliente)
    
    # Exibe resultado
    print(f"\n📊 Resultado da Predição:")
    print(f"   CPF: {resultado['cpf_cnpj']}")
    print(f"   Score: {resultado['score']}")
    print(f"   PD: {resultado['pd']:.2%}")
    print(f"   Faixa de Risco: {resultado['faixa_risco']}")
    print(f"   Limite Sugerido: R$ {resultado['limite_sugerido']:,.2f}")
    print(f"   Decisão: {resultado['decisao']}")
    print(f"   Motivo: {resultado['motivo']}")


def exemplo_predicao_lote():
    """Exemplo de predição em lote"""
    print("\n" + "=" * 60)
    print("Exemplo 2: Predição em Lote")
    print("=" * 60)
    
    client = BehaviorScoreClient()
    
    # Lista de clientes
    clientes = [
        {
            "cpf_cnpj": "11111111111",
            "idade": 30,
            "renda_valida_new": 2500.0,
            "tempo_relacionamento_kredilig_meses": 18,
            "qtd_contratos": 3,
            "qtd_contratos_nr": 3,
            "dias_maior_atraso": 5,
            "dias_maior_atraso_aberto": 0,
            "valor_pago_nr": 3000.0,
            "valor_principal_total_nr": 5000.0,
            "indice_instabilidade": 8.0,
            "indice_regularidade": 0.90,
            "reneg_vs_liq_ratio_ponderado": 0.1
        },
        {
            "cpf_cnpj": "22222222222",
            "idade": 45,
            "renda_valida_new": 5000.0,
            "tempo_relacionamento_kredilig_meses": 36,
            "qtd_contratos": 8,
            "qtd_contratos_nr": 6,
            "dias_maior_atraso": 30,
            "dias_maior_atraso_aberto": 10,
            "valor_pago_nr": 10000.0,
            "valor_principal_total_nr": 15000.0,
            "indice_instabilidade": 20.0,
            "indice_regularidade": 0.70,
            "reneg_vs_liq_ratio_ponderado": 0.4
        }
    ]
    
    # Realiza predições
    resultado = client.predict_batch(clientes)
    
    # Exibe resultados
    print(f"\n📊 Resultados:")
    print(f"   Total de clientes: {resultado['total']}")
    print(f"   Sucessos: {resultado['successful']}")
    print(f"   Falhas: {resultado['failed']}")
    
    print(f"\n📋 Predições:")
    for i, pred in enumerate(resultado['predictions'], 1):
        print(f"\n   Cliente {i}:")
        print(f"      CPF: {pred['cpf_cnpj']}")
        print(f"      Score: {pred['score']}")
        print(f"      Risco: {pred['faixa_risco']}")
        print(f"      Decisão: {pred['decisao']}")


def exemplo_info_modelo():
    """Exemplo de obtenção de informações do modelo"""
    print("\n" + "=" * 60)
    print("Exemplo 3: Informações do Modelo")
    print("=" * 60)
    
    client = BehaviorScoreClient()
    
    # Informações do modelo
    info = client.get_model_info()
    print(f"\n📋 Informações do Modelo:")
    print(json.dumps(info, indent=2))
    
    # Features esperadas
    features = client.get_expected_features()
    print(f"\n📝 Features Esperadas:")
    print(f"\n   Obrigatórias:")
    for feature in features['required_features']:
        print(f"      - {feature}")
    
    print(f"\n   Opcionais:")
    for feature in features['optional_features']:
        print(f"      - {feature}")


def exemplo_tratamento_erros():
    """Exemplo de tratamento de erros"""
    print("\n" + "=" * 60)
    print("Exemplo 4: Tratamento de Erros")
    print("=" * 60)
    
    client = BehaviorScoreClient()
    
    # Tentativa com dados incompletos
    dados_invalidos = {
        "cpf_cnpj": "99999999999",
        "idade": 25
        # Faltam campos obrigatórios
    }
    
    try:
        resultado = client.predict(dados_invalidos)
        print(f"✅ Predição realizada: {resultado}")
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erro HTTP: {e}")
        print(f"   Status Code: {e.response.status_code}")
        if e.response.status_code == 422:
            print(f"   Detalhes: Dados de entrada inválidos")
            print(f"   Resposta: {e.response.json()}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")


if __name__ == "__main__":
    try:
        # Executa exemplos
        exemplo_predicao_individual()
        exemplo_predicao_lote()
        exemplo_info_modelo()
        exemplo_tratamento_erros()
        
        print("\n" + "=" * 60)
        print("✅ Todos os exemplos foram executados!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API.")
        print("   Verifique se os containers estão rodando:")
        print("   docker-compose ps")
    except Exception as e:
        print(f"❌ Erro: {e}")

