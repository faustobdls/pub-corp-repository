# Como usar o Pub Corp Repository

Este documento explica como configurar e usar o Pub Corp Repository como proxy para o pub.dev em seus projetos Dart/Flutter. O Pub Corp Repository suporta dois modos de armazenamento: GCP (Google Cloud Platform) e local (sistema de arquivos local).

## Configuração do ambiente

### 1. Escolher o modo de armazenamento

O Pub Corp Repository suporta dois modos de armazenamento:

#### Modo de armazenamento local (padrão)

Este modo usa o sistema de arquivos local para armazenar pacotes. É ideal para testes e desenvolvimento, não requerendo configurações adicionais de serviços externos.

#### Modo de armazenamento GCP

Este modo usa o Google Cloud Platform (GCP) para armazenar pacotes. É recomendado para ambientes de produção.

Para usar o modo GCP, você precisa configurar as credenciais do GCP. Existem duas maneiras de fazer isso:

##### Usando um arquivo de credenciais

1. Baixe o arquivo de credenciais JSON do seu projeto GCP.
2. Defina a variável de ambiente `GOOGLE_APPLICATION_CREDENTIALS` para apontar para o arquivo de credenciais:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/caminho/para/seu-arquivo-de-credenciais.json"
```

##### Usando o Google Cloud SDK

1. Instale o [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
2. Autentique-se usando o comando:

```bash
gcloud auth application-default login
```

### 2. Configurar as variáveis de ambiente

Crie um arquivo `.env` baseado no arquivo `.env.example` e preencha as variáveis de ambiente necessárias:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e defina as seguintes variáveis:

- `STORAGE_TYPE`: O tipo de armazenamento a ser usado (`local` ou `gcp`). O padrão é `local`.

Para o modo de armazenamento local:
- `LOCAL_STORAGE_DIR`: O diretório onde os pacotes serão armazenados. O padrão é `./storage`.

Para o modo de armazenamento GCP:
- `GCP_BUCKET_NAME`: O nome do bucket GCP para armazenar os pacotes.
- `GCP_PROJECT_ID`: O ID do seu projeto GCP.

Configuração do servidor:
- `HOST`: O endereço IP onde o servidor será executado. O padrão é `0.0.0.0` (todas as interfaces de rede).
- `PORT`: A porta onde o servidor será executado. O padrão é `5000`.

## Executando o Pub Corp Repository

### Usando Docker

A maneira mais fácil de executar o Pub Corp Repository é usando Docker:

```bash
docker-compose up
```

Isso iniciará o servidor na porta configurada (padrão: 5000). Se você alterou a porta no arquivo `.env`, certifique-se de atualizar o arquivo `docker-compose.yml` para mapear a porta correta.

### Executando localmente

Se preferir executar localmente sem Docker:

1. Crie e ative um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Execute a aplicação:

```bash
python run.py
```

## Usando o Pub Corp Repository com o pub CLI

Para usar o Pub Corp Repository como proxy para o pub.dev, você precisa configurar a variável de ambiente `PUB_HOSTED_URL` para apontar para o seu servidor:

```bash
export PUB_HOSTED_URL="http://localhost:${PORT:-5000}"
```

Substitua `${PORT:-5000}` pela porta que você configurou no arquivo `.env` (ou use 5000 se não tiver alterado).

Agora, quando você executar comandos como `flutter pub get` ou `dart pub get`, o pub CLI usará o seu proxy em vez do pub.dev oficial.

### Configuração permanente

Para configurar permanentemente o proxy, você pode adicionar a variável de ambiente ao seu arquivo de perfil (`.bashrc`, `.zshrc`, etc.):

```bash
echo 'export PUB_HOSTED_URL="http://localhost:PORTA"' >> ~/.bashrc
source ~/.bashrc
```

Substitua `PORTA` pela porta que você configurou no arquivo `.env` (ou use 5000 se não tiver alterado).

## Publicando pacotes privados

Para publicar um pacote privado no Pub Corp Repository:

1. Crie um arquivo `.tar.gz` do seu pacote:

```bash
cd seu_pacote
tar -czf ../seu_pacote-1.0.0.tar.gz .
```

2. Envie o pacote para o Pub Corp Repository:

```bash
curl -X POST -F "file=@../seu_pacote-1.0.0.tar.gz" -F "package_name=seu_pacote" -F "version=1.0.0" http://localhost:PORTA/api/packages
```

Substitua `PORTA` pela porta que você configurou no arquivo `.env` (ou use 5000 se não tiver alterado).

## Solução de problemas

### Problemas com o modo de armazenamento

#### Modo local

Se você encontrar problemas com o modo de armazenamento local, verifique se:

1. O diretório especificado em `LOCAL_STORAGE_DIR` existe e tem permissões de escrita.
2. Há espaço suficiente em disco para armazenar os pacotes.

#### Modo GCP

Se você encontrar erros relacionados à autenticação do GCP, verifique se:

1. O arquivo de credenciais está correto e acessível.
2. As permissões do bucket estão configuradas corretamente.
3. A variável de ambiente `GOOGLE_APPLICATION_CREDENTIALS` está definida corretamente.

### Problemas com o pub CLI

Se o pub CLI não estiver usando o proxy:

1. Verifique se a variável de ambiente `PUB_HOSTED_URL` está definida corretamente e aponta para o host e porta corretos.
2. Reinicie o terminal após definir a variável de ambiente.
3. Verifique se o servidor Pub Corp Repository está em execução.

### Problemas com a configuração do servidor

Se você estiver tendo problemas para acessar o servidor:

1. Verifique se as variáveis `HOST` e `PORT` estão configuradas corretamente no arquivo `.env`.
2. Certifique-se de que a porta configurada não está sendo usada por outro serviço.
3. Se você estiver usando Docker, verifique se o mapeamento de portas no arquivo `docker-compose.yml` corresponde à porta configurada no arquivo `.env`.
4. Se você alterou o host para um endereço específico (diferente de 0.0.0.0), certifique-se de que esse endereço é acessível a partir de onde você está tentando se conectar.