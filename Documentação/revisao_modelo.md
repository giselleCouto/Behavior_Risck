# Revisão do Modelo Behavior Score

## Visão Geral
Esta revisão analisa a implementação atual do serviço `BehaviorScoreModel` e o fluxo de dados associado no dashboard para identificar fragilidades em relação ao pré-processamento, previsões e governança de retreinamento.

## Fragilidades Principais
1. **Pré-processamento ausente no serviço de modelo**  
   Apesar de todos os imputadores, scaler e demais artefatos serem carregados na inicialização, o método `preprocess` apenas converte o dicionário de entrada em `DataFrame` e retorna sem aplicar imputação, codificação, clusterização ou normalização. Na prática, qualquer campo ausente, fora de ordem ou com tipo inválido será repassado diretamente ao modelo de floresta aleatória, contrariando o fluxo utilizado no treinamento original e podendo resultar em erros ou previsões incoerentes.【F:deploy/api/model_service.py†L33-L185】

2. **Ausência de validação de schema e tipos antes da predição**  
   Não há verificação se todas as `required_features` declaradas em `get_expected_features` estão presentes, se os tipos são compatíveis com os artefatos de pré-processamento ou se existem colunas extras que precisam ser descartadas. A API apenas transforma o payload em `DataFrame` e chama `predict_proba`, o que deixa o serviço suscetível a falhas silenciosas ou exceções em tempo de execução quando algum campo chega com formato inesperado.【F:deploy/api/model_service.py†L133-L206】【F:deploy/api/app.py†L156-L181】

3. **Bins de risco não utilizados**  
   Os bins carregados de `bins_risco.npy` são ignorados durante a classificação da faixa de risco; o método `_get_risk_band` utiliza limiares fixos codificados manualmente. Se os limites estatísticos forem atualizados nos artefatos, as faixas do serviço continuarão desatualizadas, produzindo decisões inconsistentes com os materiais analíticos.【F:deploy/api/model_service.py†L239-L253】

4. **Dependência frágil da tabela de limites**  
   `_calculate_limit` assume a existência de colunas específicas (`PD`, `limite`) e a presença de um valor próximo para toda predição. Caso a tabela mude de schema ou falte um intervalo, o código gera exceções ou retorna 0 sem fallback robusto, afetando diretamente as saídas entregues ao usuário final.【F:deploy/api/model_service.py†L255-L274】

5. **Fluxo de uploads no dashboard sem tratamento**  
   As funções `load_relatorio`, `load_shap` e `load_indicadores` apenas carregam os arquivos utilizando os readers padrão, sem validações de colunas, conversões de tipos, tratamento de dados faltantes ou padronização de nomes. Esses `DataFrames` são então armazenados na sessão e potencialmente reaproveitados em outras etapas, criando risco de alimentar o modelo com dados brutos inconsistentes.【F:deploy/dashboard/data_pipeline.py†L32-L64】

6. **Retreinamento exclusivamente manual**  
   O serviço declara explicitamente que o retreinamento automático está desabilitado (`retraining_enabled = False`) e expõe essa informação pela API. Não há rotina que monitore a chegada de novos dados mensais, tampouco scripts automatizados para atualizar os artefatos, o que pode levar a drift se o modelo não for reavaliado e retreinado seguindo governança formal.【F:deploy/api/model_service.py†L17-L114】

## Recomendações de Próximos Passos
- Implementar o pipeline completo de pré-processamento, reutilizando os imputadores, scaler e transformações de clusterização salvos durante o treinamento.
- Adicionar validações estruturadas do schema de entrada (tipos, colunas obrigatórias, ranges) antes de chamar o modelo, rejeitando ou corrigindo registros inconsistentes.
- Ler os bins de risco diretamente do artefato `bins_risco.npy` para determinar faixas dinamicamente, mantendo consistência com as análises estatísticas.
- Fortalecer `_calculate_limit` com checagens de integridade da tabela e fallback configurável quando não houver correspondência adequada.
- Enriquecer o pipeline de upload com limpeza, normalização de colunas e relatórios de qualidade dos dados antes de disponibilizá-los para scoring.
- Definir um processo de MLOps para ingestão mensal: monitoramento de drift, retreinamento controlado, validação de performance e versionamento dos artefatos.

## Processo MLOps Proposto

1. **Ingestão e qualificação mensal dos dados**  
   Consolidar a rotina de uploads no dashboard com a execução automática do pré-processamento (padronização de colunas, imputações e geração de relatórios de qualidade). Persistir os artefatos sanitizados juntamente com os relatórios de inconsistências para auditoria.

2. **Monitoramento contínuo de deriva**  
   Publicar indicadores de drift (populacional e de performance) calculados após cada carregamento mensal. Utilizar limites estatísticos acordados com o negócio para sinalizar quando o comportamento das variáveis-chave se desviar do intervalo esperado.

3. **Gatilho formal de retreinamento**  
   Estabelecer critérios objetivos (por exemplo, drift persistente por `N` meses ou degradação da métrica AUC em `X` p.p.) para iniciar o retreinamento. Uma vez atendidos os critérios, executar a pipeline de modelagem em ambiente isolado, versionando dados, código e artefatos resultantes.

4. **Validação e aprovação**  
   Comparar o modelo retreinado com a versão atual através de validação cruzada, backtesting e testes de robustez. Registrar os resultados em relatórios revisados por risco/modelagem e formalizar a aprovação com as áreas de negócio e compliance.

5. **Empacotamento e versionamento dos artefatos**  
   Versionar todos os arquivos (`.pkl`, `.npy`, tabelas auxiliares) em repositório controlado, adotando convenção de versionamento semântico e garantindo a rastreabilidade entre código, dados de treino e artefatos.

6. **Deploy controlado e monitorado**  
   Promover o novo conjunto de artefatos para produção somente após testes automatizados (integração e smoke tests). Monitorar as métricas de execução (latência, erros) e de negócio (taxa de aprovação, inadimplência) nos primeiros ciclos pós-deploy, com plano de rollback documentado.

