#!/bin/bash

# Ativa o ambiente virtual se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Executa os testes com cobertura
python -m pytest --cov=pub_proxy --cov-report=term-missing

# Exibe mensagem de conclusão
echo "Testes concluídos!"